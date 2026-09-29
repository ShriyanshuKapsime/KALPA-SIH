"""
Contextual Clarification Extractor for Stage 10 Entrepreneur Profile Engine.
Extracts structured entrepreneur facts from multilingual text / voice STT transcripts.
Uses deterministic regex and canonical ontology-driven rule-based parsing with optional LLM fallback.
DOES NOT calculate readiness or risk scores.
"""
import re
from typing import Dict, Any, Optional, List, Union
from app.services.llm_client import llm_client
from app.core.logging import logger


class ClarificationExtractor:
    """
    Converts natural-language responses (Hindi/English/Hinglish/Kannada/Tamil/Telugu/Marathi)
    into structured profile field updates within specific business domain contexts.
    """

    # Multi-lingual number words mapping
    INDIC_NUMBER_MAP = {
        # English
        "zero": 0.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0,
        "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0, "ten": 10.0,
        "eleven": 11.0, "twelve": 12.0, "a": 1.0, "an": 1.0,
        # Hindi / Hinglish
        "शून्य": 0.0, "shunya": 0.0,
        "आधा": 0.5, "डेढ़": 1.5, "ढाई": 2.5,
        "एक": 1.0, "दो": 2.0, "तीन": 3.0, "चार": 4.0, "पांच": 5.0, "पाँच": 5.0,
        "छह": 6.0, "छः": 6.0, "सात": 7.0, "आठ": 8.0, "नौ": 9.0, "दस": 10.0,
        "ग्यारह": 11.0, "बारह": 12.0, "तेरह": 13.0, "चौदह": 14.0, "पंद्रह": 15.0,
        "सोलह": 16.0, "सत्रह": 17.0, "अठारह": 18.0, "उन्नीस": 19.0, "बीस": 20.0,
        "पच्चीस": 25.0, "तीस": 30.0, "चालीस": 40.0, "पचास": 50.0,
        # Hinglish
        "ek": 1.0, "do": 2.0, "teen": 3.0, "char": 4.0, "chaar": 4.0, "paanch": 5.0, "panch": 5.0,
        "che": 6.0, "chheh": 6.0, "saat": 7.0, "aath": 8.0, "ath": 8.0, "nau": 9.0, "das": 10.0,
        "pandrah": 15.0, "bees": 20.0, "pachees": 25.0, "tees": 30.0,
        # Kannada
        "ಸೊನ್ನೆ": 0.0, "ಒಂದು": 1.0, "ಎರಡು": 2.0, "ಮೂರು": 3.0, "ನಾಲ್ಕು": 4.0, "ಐದು": 5.0,
        "ಆರು": 6.0, "ಏಳು": 7.0, "ಎಂಟು": 8.0, "ಒಂಬತ್ತು": 9.0, "ಹತ್ತು": 10.0,
        # Tamil
        "பூஜ்ஜியம்": 0.0, "ஒன்று": 1.0, "இரண்டு": 2.0, "மூன்று": 3.0, "நான்கு": 4.0, "ஐந்து": 5.0,
        "ஆறு": 6.0, "ஏழு": 7.0, "எட்டு": 8.0, "ஒன்பது": 9.0, "பத்து": 10.0,
        # Telugu
        "సున్నా": 0.0, "ఒకటి": 1.0, "రెండు": 2.0, "మూడు": 3.0, "నాలుగు": 4.0, "ఐదు": 5.0,
        "ఆరు": 6.0, "ఏడు": 7.0, "ఎనిమిది": 8.0, "తొమ్మిది": 9.0, "పది": 10.0,
        # Marathi
        "शून्य": 0.0, "एक": 1.0, "दोन": 2.0, "तीन": 3.0, "चार": 4.0, "पाच": 5.0,
        "सहा": 6.0, "सात": 7.0, "आठ": 8.0, "नऊ": 9.0, "दहा": 10.0
    }

    # Business domain skill mapping
    DOMAIN_SKILLS_ONTOLOGY = {
        "general_enterprise": {
            "keywords": ["business", "enterprise", "व्यापार", "दुकान", "retail", "selling", "service", "customer"],
            "default_skills": ["business_management", "customer_handling", "daily_operations"],
            "experience_domain": "general_business"
        },
        "saree_retail": {
            "keywords": ["saree", "saari", "साड़ी", "handloom saree", "silk saree", "बनारसी साड़ी"],
            "default_skills": ["retail_sales", "saree_retail", "customer_handling", "inventory_management"],
            "experience_domain": "saree_retail"
        },
        "garment_store": {
            "keywords": ["garment", "readymade", "कपड़े", "apparel", "clothing", "dress", "फैब्रिक", "kurti", "jeans"],
            "default_skills": ["apparel_retailing", "customer_service", "stock_procurement", "visual_merchandising"],
            "experience_domain": "garment_retail"
        },
        "dairy_farm": {
            "keywords": ["dairy", "milk", "गाय", "भैंस", "cow", "buffalo", "दूध", "डेयरी", "chilling", "cattle", "पशु", "fodder", "चारा"],
            "default_skills": ["livestock_handling", "milk_testing", "dairy_aggregation", "feed_management"],
            "experience_domain": "dairy_farming"
        },
        "rice_mill": {
            "keywords": ["rice", "paddy", "धान", "चावल", "mill", "dehusking", "हलर", "चक्की", "राइस मिल"],
            "default_skills": ["paddy_processing", "milling_machinery_operations", "moisture_testing", "grain_grading"],
            "experience_domain": "rice_milling"
        },
        "flour_mill": {
            "keywords": ["flour", "atta", "wheat", "गेहूं", "आटा", "chakki", "चक्की", "grinding", "पीसना"],
            "default_skills": ["flour_milling", "stone_dressing", "machine_maintenance", "grain_cleaning"],
            "experience_domain": "flour_milling"
        },
        "grocery_store": {
            "keywords": ["grocery", "kirana", "किराना", "दुकान", "fmcg", "store", "राशन", "सामान"],
            "default_skills": ["retail_sales", "inventory_procurement", "bookkeeping", "customer_credit_management"],
            "experience_domain": "grocery_retail"
        },
        "tailoring_shop": {
            "keywords": ["tailor", "stitching", "सिलाई", "दर्जी", "कटिंग", "cutting", "garment", "sewing", "blouse"],
            "default_skills": ["garment_stitching", "pattern_cutting", "fabric_handling", "sewing_machine_maintenance"],
            "experience_domain": "garment_tailoring"
        },
        "poultry_farm": {
            "keywords": ["poultry", "chicken", "broiler", "मुर्गी", "पोल्ट्री", "birds", "feed", "egg", "अंडा"],
            "default_skills": ["poultry_broiler_management", "feed_rationing", "biosecurity_maintenance", "disease_monitoring"],
            "experience_domain": "poultry_farming"
        },
        "goat_farming": {
            "keywords": ["goat", "बकरी", "बकरा", "livestock", "grazing", "breeding", "चारा"],
            "default_skills": ["goat_husbandry", "feed_management", "disease_monitoring", "shelter_management"],
            "experience_domain": "goat_farming"
        },
        "spice_processing": {
            "keywords": ["spice", "masala", "मसाला", "haldi", "mirch", "धनिया", "grinding", "packaging"],
            "default_skills": ["spice_grinding", "moisture_inspection", "hygienic_packaging", "fssai_compliance"],
            "experience_domain": "spice_processing"
        },
        "oil_expeller": {
            "keywords": ["oil", "tel", "तेल", "expeller", "mustard", "sarson", "groundnut", "मूंगफली"],
            "default_skills": ["oil_expeller_operation", "seed_cleaning", "oil_filtration", "cake_handling"],
            "experience_domain": "oil_extraction"
        },
        "beauty_salon": {
            "keywords": ["beauty", "parlour", "salon", "ब्यूटी", "पार्लर", "makeup", "hair", "facial"],
            "default_skills": ["bridal_makeup", "hair_styling", "skin_treatment", "salon_sanitization"],
            "experience_domain": "beauty_wellness"
        },
        "mobile_repair": {
            "keywords": ["mobile", "phone", "मोबाइल", "repair", "hardware", "screen", "charging", "recharge"],
            "default_skills": ["circuit_diagnostics", "component_soldering", "screen_replacement", "flashing_software"],
            "experience_domain": "electronics_repair"
        },
        "solar_pump_repair": {
            "keywords": ["solar", "pump", "सोलर", "पंप", "electric", "motor", "wiring", "inverter"],
            "default_skills": ["solar_pump_diagnostics", "inverter_maintenance", "electrical_wiring", "borewell_troubleshooting"],
            "experience_domain": "solar_maintenance"
        },
        "organic_fertilizer": {
            "keywords": ["vermicompost", "compost", "manure", "केंचुआ", "खाद", "dung", "organic"],
            "default_skills": ["bed_moisture_maintenance", "pre_decomposition", "worm_separation", "grading"],
            "experience_domain": "organic_fertilizer"
        }
    }

    def _resolve_target_domain(self, business_context: Optional[Dict[str, Any]] = None) -> str:
        """Determines best matching domain key from business context."""
        if not business_context:
            return "general_enterprise"

        b_id = str(
            business_context.get("business_id") or
            business_context.get("business_node_id") or
            business_context.get("specific_business") or
            business_context.get("category") or
            ""
        ).lower().replace(" ", "_").replace("-", "_")

        for domain_key in self.DOMAIN_SKILLS_ONTOLOGY:
            if domain_key in b_id or b_id in domain_key:
                return domain_key

        if "saree" in b_id or "cloth" in b_id or "textile" in b_id:
            return "saree_retail"
        elif "garment" in b_id or "apparel" in b_id:
            return "garment_store"
        elif "dairy" in b_id or "milk" in b_id or "cow" in b_id:
            return "dairy_farm"
        elif "rice" in b_id or "paddy" in b_id:
            return "rice_mill"
        elif "flour" in b_id or "atta" in b_id or "chakki" in b_id:
            return "flour_mill"
        elif "grocery" in b_id or "kirana" in b_id:
            return "grocery_store"
        elif "tailor" in b_id or "sewing" in b_id:
            return "tailoring_shop"
        elif "poultry" in b_id or "chicken" in b_id:
            return "poultry_farm"
        elif "goat" in b_id or "sheep" in b_id:
            return "goat_farming"
        elif "spice" in b_id or "masala" in b_id:
            return "spice_processing"
        elif "oil" in b_id:
            return "oil_expeller"

        return "general_enterprise"

    def extract_from_text(
        self,
        text: str,
        target_field: Optional[str] = None,
        business_context: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        is_voice: bool = False
    ) -> Dict[str, Any]:
        """
        Deterministically extracts structured profile properties from user text/voice transcript.
        If user explicitly says 0 years experience or no experience -> accurately extracts 0.0.
        """
        if not text or not isinstance(text, str):
            return {}

        clean_text = text.strip()
        lower_text = clean_text.lower()
        extracted: Dict[str, Any] = {}
        source_tag = "USER_VOICE" if is_voice else "USER_CLARIFICATION"

        domain_key = self._resolve_target_domain(business_context)
        domain_info = self.DOMAIN_SKILLS_ONTOLOGY.get(domain_key, self.DOMAIN_SKILLS_ONTOLOGY["general_enterprise"])
        field_norm = (target_field or "").lower().strip()

        # =====================================================================
        # 1. EXTRACT YEARS OF EXPERIENCE
        # =====================================================================
        years = None

        # Check explicit zero / fresh entrepreneur indicators FIRST
        zero_indicators = [
            "0 years", "0 saal", "0 साल", "0 वर्ष", "zero years", "zero experience",
            "no experience", "fresh", "first time", "naya", "नया", "पहला",
            "कभी काम नहीं किया", "कभी व्यापार नहीं किया", "अनुभव नहीं है", "कोई अनुभव नहीं",
            "never run a business", "not worked before", "start fresh", "కొత్త", "ಹೊಸ", "புதிய"
        ]
        if any(z in lower_text for z in zero_indicators):
            years = 0.0

        # Pattern: Optional modifier + Digit + unit (e.g., "लगभग 2 साल", "about 1 year", "5 years", "5 saal", "5 साल", "5.5 yrs", "3.0 years")
        if years is None:
            exp_match = re.search(r'(?:लगभग|करीब|about|around|approx|approximately)?\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?|saal|sal|bars|varsh|साल|वर्ष|ವರ್ಷ|வருடம்|సంవత్సరాలు)', lower_text)
            if exp_match:
                try:
                    years = float(exp_match.group(1))
                except ValueError:
                    pass

        # Pattern: Optional modifier + Indic/English word + unit (e.g., "एक साल", "one year", "a year", "an year", "तीन साल", "मೂರು ವರ್ಷ")
        if years is None:
            for word, val in self.INDIC_NUMBER_MAP.items():
                pattern = rf'(?:लगभग|करीब|about|around|approx|approximately)?\s*(?:^|\s|\b){re.escape(word)}\s*(?:years?|yrs?|saal|sal|bars|varsh|साल|वर्ष|ವರ್ಷ|வருடம்|సంవత్సరాలు)'
                if re.search(pattern, lower_text, re.IGNORECASE):
                    years = float(val)
                    break

        # Pattern: "X months" (e.g. "6 months" -> 0.5 years, "12 months" -> 1.0 year)
        if years is None:
            month_match = re.search(r'(\d+)\s*(?:months?|mahine|mahina|महीने|महीना|ತಿಂಗಳು)', lower_text)
            if month_match:
                try:
                    years = round(float(month_match.group(1)) / 12.0, 2)
                except ValueError:
                    pass

        # Direct single digit when question target is specifically experience
        if years is None and ("experience" in field_norm or "year" in field_norm or "exp" in field_norm):
            digit_only = re.search(r'\b(\d+(?:\.\d+)?)\b', lower_text)
            if digit_only:
                try:
                    val = float(digit_only.group(1))
                    if 0.0 <= val <= 60.0:
                        years = val
                except ValueError:
                    pass
            if years is None:
                for word, val in self.INDIC_NUMBER_MAP.items():
                    if word in lower_text.split() or word == lower_text:
                        years = float(val)
                        break

        if years is not None:
            extracted["experience"] = {
                "years_of_experience": years,
                "domain": domain_info["experience_domain"],
                "source": source_tag,
                "raw_text": clean_text,
                "confidence": 0.96
            }

        # =====================================================================
        # 2. EXTRACT SKILLS / TRADE ABILITIES
        # =====================================================================
        skills_found: List[str] = []

        domain_matched = False
        for kw in domain_info["keywords"]:
            if kw in lower_text:
                domain_matched = True
                break

        for d_k, d_v in self.DOMAIN_SKILLS_ONTOLOGY.items():
            for kw in d_v["keywords"]:
                if kw in lower_text:
                    for s in d_v["default_skills"]:
                        if s not in skills_found:
                            skills_found.append(s)
                    break

        if domain_matched or ("skill" in field_norm and len(skills_found) == 0):
            for s in domain_info["default_skills"]:
                if s not in skills_found:
                    skills_found.append(s)

        # Sales / retail tokens
        if any(w in lower_text for w in ["sales", "selling", "बेच", "बिक्री", "retail", "दुकान", "customer", "ग्राहक", "negotiation"]):
            if "retail_sales" not in skills_found:
                skills_found.append("retail_sales")
            if "customer_handling" not in skills_found:
                skills_found.append("customer_handling")

        # Bookkeeping tokens
        if any(w in lower_text for w in ["hisaab", "khata", "accounting", "billing", "खाता", "हिसाब", "बहीखाता"]):
            if "bookkeeping" not in skills_found:
                skills_found.append("bookkeeping")

        # Machinery tokens
        if any(w in lower_text for w in ["machine", "मशीन", "चालक", "operator", "चलाना", "operation", "maintenance", "रिपेयर"]):
            if "machinery_operations" not in skills_found:
                skills_found.append("machinery_operations")

        # Fabric / Saree tokens
        if any(w in lower_text for w in ["saree", "saari", "साड़ी"]):
            if "saree_retail" not in skills_found:
                skills_found.append("saree_retail")

        if skills_found:
            extracted["skills"] = {
                "skills": skills_found,
                "source": source_tag,
                "raw_text": clean_text,
                "confidence": 0.93
            }

        # =====================================================================
        # 3. EXTRACT RESOURCES (SPACE, PREMISES, POWER)
        # =====================================================================
        res_dict: Dict[str, Any] = {}
        is_resource_targeted = any(rk in field_norm for rk in ["resource", "area", "space", "power", "sqft", "shop", "land"])

        # Power Connection
        if any(w in lower_text for w in ["3 phase", "three phase", "3-phase", "तीन फेस", "3 फेज", "commercial power", "3ಫೇಸ್", "3 phase commercial"]):
            res_dict["power_connection_type"] = "THREE_PHASE_COMMERCIAL"
        elif any(w in lower_text for w in ["single phase", "1 phase", "सिंगल फेस", "घर की बिजली", "domestic", "सिंगल फेज"]):
            res_dict["power_connection_type"] = "SINGLE_PHASE"
        elif is_resource_targeted and any(w in lower_text for w in ["no power", "no electricity", "बिजली नहीं"]):
            res_dict["power_connection_type"] = "NONE"

        # Space / Area
        sqft_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:sq\s*ft|sqft|square\s*feet|स्क्वायर\s*फीट|वर्ग\s*फुट|चौरस\s*फूट|ಚದರ\s*ಅಡಿ)', lower_text)
        if sqft_match:
            try:
                res_dict["available_area_sqft"] = float(sqft_match.group(1))
                res_dict["land_or_premises_available"] = True
            except ValueError:
                pass

        # Gaj (1 gaj ~ 9 sqft)
        gaj_match = re.search(r'(\d+)\s*(?:gaj|गज|yard)', lower_text)
        if gaj_match and "available_area_sqft" not in res_dict:
            try:
                res_dict["available_area_sqft"] = float(gaj_match.group(1)) * 9.0
                res_dict["land_or_premises_available"] = True
            except ValueError:
                pass

        # Direct number when question specifically targets resources.available_area_sqft
        if "available_area_sqft" not in res_dict and ("area" in field_norm or "sqft" in field_norm or "space" in field_norm):
            digit_match = re.search(r'\b(\d+(?:\.\d+)?)\b', lower_text)
            if digit_match:
                try:
                    num_val = float(digit_match.group(1))
                    if 20.0 <= num_val <= 50000.0:
                        res_dict["available_area_sqft"] = num_val
                        res_dict["land_or_premises_available"] = True
                except ValueError:
                    pass

        # General shop readiness (only if explicit readiness phrase or target field is resources)
        explicit_shop_ready = [
            "shop ready", "dukan taiyar", "दुकान तैयार है", "दुकान उपलब्ध है", "खुद की दुकान है",
            "किराए की दुकान है", "पक्की दुकान है", "जगह तैयार है", "जगह उपलब्ध है",
            "own land", "premises available", "rented shop", "शेड तैयार है"
        ]
        if any(w in lower_text for w in explicit_shop_ready) or (is_resource_targeted and any(w in lower_text for w in ["दुकान है", "shop", "जगह है"])):
            res_dict["land_or_premises_available"] = True
        elif is_resource_targeted and any(w in lower_text for w in ["no shop", "no land", "जगह नहीं है", "arranging", "ढूंढ रहे"]):
            res_dict["land_or_premises_available"] = False

        if res_dict:
            res_dict["source"] = source_tag
            res_dict["raw_text"] = clean_text
            res_dict["confidence"] = 0.91
            extracted["resources"] = res_dict

        # =====================================================================
        # 4. EXTRACT TRAINING / CERTIFICATIONS
        # =====================================================================
        certs: List[str] = []
        has_formal = None
        willing = True

        if any(w in lower_text for w in ["certified", "certificate", "सर्टिफिकेट", "डिप्लोमा", "pmkvy", "fostac", "iti", "rseti", "edp", "ट्रेनिंग की है", "प्रशिक्षण लिया"]):
            has_formal = True
            if "fostac" in lower_text or "fssai" in lower_text:
                certs.append("FoSTaC_FSSAI")
            if "pmkvy" in lower_text:
                certs.append("PMKVY_Skill_Certificate")
            if "iti" in lower_text:
                certs.append("ITI_Trade_Diploma")
            if "rseti" in lower_text or "edp" in lower_text:
                certs.append("RSETI_EDP_Certificate")
            if not certs:
                certs.append("Vocational_Trade_Certificate")

        elif any(w in lower_text for w in ["training karunga", "seekh lunga", "ट्रेनिंग करूँगा", "willing to learn", "ready for training", "सीखने को तैयार"]):
            has_formal = False
            willing = True

        elif any(w in lower_text for w in ["no training", "training nahi", "ट्रेनिंग नहीं", "नहीं सीखा"]):
            has_formal = False
            willing = False

        if has_formal is not None or certs or ("train" in field_norm or "cert" in field_norm):
            extracted["training"] = {
                "has_formal_training": has_formal if has_formal is not None else len(certs) > 0,
                "certifications": certs,
                "willing_to_undergo_training": willing,
                "source": source_tag,
                "raw_text": clean_text,
                "confidence": 0.90
            }

        # =====================================================================
        # 5. EXTRACT OPERATIONS (COMMITMENT & WORKFORCE)
        # =====================================================================
        ops_dict: Dict[str, Any] = {}

        if any(w in lower_text for w in ["full time", "full-time", "फुल टाइम", "पूरा समय", "पूर्णकालिक", "रोजाना"]):
            ops_dict["commitment_type"] = "FULL_TIME"
        elif any(w in lower_text for w in ["part time", "part-time", "पार्ट टाइम", "आधा समय"]):
            ops_dict["commitment_type"] = "PART_TIME"
        elif any(w in lower_text for w in ["seasonal", "सीजनल", "मौसमी"]):
            ops_dict["commitment_type"] = "SEASONAL"

        workers_match = re.search(r'(\d+)\s*(?:workers?|helpers?|karamchari|मजदूर|कर्मचारी|लोग|सहायक)', lower_text)
        if workers_match:
            try:
                ops_dict["hired_workers_planned"] = int(workers_match.group(1))
            except ValueError:
                pass

        if ops_dict or ("operation" in field_norm or "commit" in field_norm or "worker" in field_norm):
            if not ops_dict and ("operation" in field_norm or "commit" in field_norm):
                ops_dict["commitment_type"] = "FULL_TIME"
            if ops_dict:
                ops_dict["source"] = source_tag
                ops_dict["raw_text"] = clean_text
                ops_dict["confidence"] = 0.90
                extracted["operations"] = ops_dict

        return extracted

    async def extract_with_optional_llm(
        self,
        text: str,
        field_hint: Optional[str] = None,
        business_context: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        is_voice: bool = False
    ) -> Dict[str, Any]:
        """
        Runs contextual deterministic extraction first.
        If empty and LLM is configured, uses LLM as a graceful extraction fallback.
        """
        deterministic_res = self.extract_from_text(
            text=text,
            target_field=field_hint,
            business_context=business_context,
            language=language,
            is_voice=is_voice
        )
        if deterministic_res:
            return deterministic_res

        # Safe LLM fallback only for entity extraction
        try:
            domain_key = self._resolve_target_domain(business_context)
            system_prompt = f"""You are a precise multilingual entity extraction assistant for rural Indian MSME intake.
Current Business Domain: {domain_key}. Target field hint: {field_hint or 'all'}.
Extract any mentioned:
- experience (years_of_experience: float, domain: string)
- skills (skills: list of string domain skills)
- resources (available_area_sqft: float, power_connection_type: string, land_or_premises_available: bool)
- training (has_formal_training: bool, certifications: list of string)
- operations (commitment_type: FULL_TIME/PART_TIME, hired_workers_planned: int)

Respond with ONLY valid JSON containing the extracted keys. Do NOT calculate scores or readiness."""

            resp = await llm_client.generate(
                prompt=f"User clarification utterance: '{text}'",
                system_instruction=system_prompt,
                response_format={"type": "json_object"}
            )
            import json
            parsed = json.loads(resp)
            if isinstance(parsed, dict) and parsed:
                return parsed
        except Exception as e:
            logger.warning(f"Optional LLM extraction fallback encountered an issue: {e}")

        return deterministic_res


clarification_extractor = ClarificationExtractor()
