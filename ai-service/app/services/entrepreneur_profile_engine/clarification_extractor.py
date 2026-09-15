"""
Clarification Extractor for Stage 10 Entrepreneur Profile Engine.
Extracts structured entrepreneur facts from multilingual text / voice STT transcripts.
Uses deterministic regex and canonical rule-based parsing with optional LLM NLU extraction.
DOES NOT calculate readiness scores.
"""
import re
from typing import Dict, Any, Optional
from app.services.intake.indic_number_parser import parse_indic_number_expression
from app.services.llm_client import llm_client
from app.core.logging import logger


class ClarificationExtractor:
    """
    Converts natural-language responses (Hindi/English/Kannada) into structured profile updates.
    """

    # Hindi number words mapping for experience/area
    HINDI_YEAR_MAP = {
        "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5,
        "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10
    }

    def extract_from_text(self, text: str, target_field: Optional[str] = None) -> Dict[str, Any]:
        """
        Deterministically extracts structured profile properties from user text.
        """
        if not text or not isinstance(text, str):
            return {}

        clean_text = text.strip()
        lower_text = clean_text.lower()
        extracted: Dict[str, Any] = {}

        # 1. Extract Years of Experience
        exp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:years?|saal|साल|ವರ್ಷ)', lower_text)
        if exp_match:
            try:
                extracted["experience"] = {
                    "years_of_experience": float(exp_match.group(1)),
                    "source": "USER_REPORTED"
                }
            except ValueError:
                pass
        else:
            for word, val in self.HINDI_YEAR_MAP.items():
                if f"{word} साल" in clean_text or f"{word} वर्ष" in clean_text:
                    extracted["experience"] = {
                        "years_of_experience": float(val),
                        "source": "USER_REPORTED"
                    }
                    break

        # 2. Extract Power Type
        if any(w in lower_text for w in ["3 phase", "three phase", "3-phase", "तीन फेस", "3 फेज", "commercial power", "3ಫೇಸ್"]):
            extracted["resources"] = extracted.get("resources", {})
            extracted["resources"]["power_connection_type"] = "THREE_PHASE_COMMERCIAL"
        elif any(w in lower_text for w in ["single phase", "1 phase", "सिंगल फेस", "घर की बिजली", "domestic"]):
            extracted["resources"] = extracted.get("resources", {})
            extracted["resources"]["power_connection_type"] = "SINGLE_PHASE"

        # 3. Extract Space / Land Area
        sqft_match = re.search(r'(\d+)\s*(?:sq\s*ft|sqft|square\s*feet|स्क्वायर\s*फीट|वर्ग\s*फुट)', lower_text)
        if sqft_match:
            try:
                extracted["resources"] = extracted.get("resources", {})
                extracted["resources"]["available_area_sqft"] = float(sqft_match.group(1))
                extracted["resources"]["land_or_premises_available"] = True
            except ValueError:
                pass

        # 4. Extract Commitment (Full-time / Part-time)
        if any(w in lower_text for w in ["full time", "full-time", "फुल टाइम", "पूरा समय", "पूर्णकालिक"]):
            extracted["operations"] = extracted.get("operations", {})
            extracted["operations"]["commitment_type"] = "FULL_TIME"
        elif any(w in lower_text for w in ["part time", "part-time", "पार्ट टाइम", "आधा समय"]):
            extracted["operations"] = extracted.get("operations", {})
            extracted["operations"]["commitment_type"] = "PART_TIME"

        # 5. Extract Training / Certifications
        if any(w in lower_text for w in ["certified", "certificate", "pmkvy", "fostac", "iti", "ट्रेनिंग की है", "प्रशिक्षण लिया"]):
            extracted["training"] = {
                "has_formal_training": True,
                "willing_to_undergo_training": True
            }
            certs = []
            if "fostac" in lower_text:
                certs.append("FoSTaC")
            if "pmkvy" in lower_text:
                certs.append("PMKVY")
            if "iti" in lower_text:
                certs.append("ITI_Diploma")
            if certs:
                extracted["training"]["certifications"] = certs
        elif any(w in lower_text for w in ["training karunga", "seekh lunga", "ट्रेनिंग करूँगा", "willing to learn", "ready for training"]):
            extracted["training"] = {
                "has_formal_training": False,
                "willing_to_undergo_training": True
            }

        # 6. Extract Skills / Trade
        skills_found = []
        trade_keywords = [
            ("chakki", "Stone dressing & Atta Chakki Operation"),
            ("flour", "Flour Milling"),
            ("tailor", "Garment Stitching & Tailoring"),
            ("cloth", "Apparel & Fabric Retail"),
            ("कपड़े", "Apparel Retail"),
            ("welding", "Metal Fabrication & Welding"),
            ("electric", "Electrical Motor Maintenance"),
            ("solar", "Solar Pump Diagnostics"),
            ("oil", "Oil Expeller Extraction"),
            ("spice", "Spice Grinding & Packaging"),
            ("dairy", "Milk Testing & Dairy Aggregation"),
            ("poultry", "Poultry Broiler Management")
        ]
        for kw, skill_label in trade_keywords:
            if kw in lower_text:
                skills_found.append(skill_label)
        if skills_found:
            extracted["skills"] = {
                "skills": skills_found,
                "source": "USER_REPORTED"
            }

        return extracted

    async def extract_with_optional_llm(self, text: str, field_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Uses deterministic extraction first, escalating to LLM only if deterministic results are empty.
        """
        deterministic_res = self.extract_from_text(text, target_field=field_hint)
        if deterministic_res:
            return deterministic_res

        if not llm_client.is_available:
            return deterministic_res

        # LLM NLU extraction
        try:
            system_prompt = (
                "You are an entity extractor for rural Indian micro-entrepreneurs.\n"
                "Extract structured facts from the user statement.\n"
                "Respond ONLY with a valid JSON object matching:\n"
                "{\n"
                "  \"skills\": {\"skills\": [\"...\"]},\n"
                "  \"experience\": {\"years_of_experience\": number, \"domain\": \"...\"},\n"
                "  \"training\": {\"has_formal_training\": boolean, \"certifications\": [\"...\"]},\n"
                "  \"resources\": {\"available_area_sqft\": number, \"power_connection_type\": \"...\"},\n"
                "  \"operations\": {\"commitment_type\": \"FULL_TIME|PART_TIME\"}\n"
                "}\n"
                "Do not invent facts. Only extract what is explicitly stated."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract facts from: '{text}'"}
            ]
            llm_result = await llm_client.chat_completion(
                messages=messages,
                json_mode=True,
                temperature=0.0
            )
            if isinstance(llm_result, dict):
                return {k: v for k, v in llm_result.items() if v}
        except Exception as e:
            logger.warning(f"[CLARIFICATION EXTRACTOR] LLM extraction error: {e}")

        return deterministic_res


clarification_extractor = ClarificationExtractor()
