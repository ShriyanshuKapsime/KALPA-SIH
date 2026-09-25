"""
Question Engine.
Generates MINIMUM structured questions for unresolved high-criticality drivers.
Questions are in simple entrepreneur language, not financial jargon.
"""
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.financial_engine.intelligence.confidence import ResolvedAssumption, AssumptionStatus

logger = logging.getLogger(__name__)


class RequiredUserInput(BaseModel):
    driver_id: str
    question: str
    language: str = "hi"
    reason: str = ""
    criticality: str = "HIGH"
    data_type: str = "currency"
    unit: Optional[str] = None
    options: Optional[List[str]] = None
    default_fallback: Optional[Any] = None
    allows_skip: bool = True
    voice_prompt: Optional[str] = None
    is_blocking: bool = True


class QuestionEngine:
    """
    Generates minimal questions for materially important unresolved drivers.
    Does NOT ask for EBITDA, DSCR, depreciation — those are ENGINE calculations.
    """

    def generate_questions(
        self,
        assumptions: List[Dict[str, Any]],
        language: str = "en",
    ) -> List[RequiredUserInput]:
        """
        Generates minimum questions ONLY for unresolved HIGH-criticality drivers.
        Never asks for EBITDA, DSCR, depreciation — those are engine calculations.
        Respects user's actual language preference (default English, supports Hindi).
        """
        questions: List[RequiredUserInput] = []
        for a in assumptions:
            status = a.get("status", "UNKNOWN")
            # Only unresolved drivers that require user input
            if status not in ("USER_REQUIRED", "UNKNOWN"):
                continue

            crit = a.get("criticality", "MEDIUM")
            # Ask ONLY for unresolved HIGH-criticality drivers
            if crit != "HIGH":
                continue

            did = a.get("driver_id", "")
            q_info = _QUESTION_CATALOG.get(did)
            if not q_info:
                continue

            # Prioritize requested language, then graceful fallbacks
            q_text = (
                q_info.get(f"question_{language}")
                or (q_info.get("question_hi") if language == "hi" else q_info.get("question_en"))
                or q_info.get("question_en")
                or q_info.get("question_hi", "")
            )
            if not q_text:
                continue

            v_prompt = (
                q_info.get(f"voice_{language}")
                or q_info.get("voice_en")
                or q_text
            )

            questions.append(RequiredUserInput(
                driver_id=did,
                question=q_text,
                language=language,
                reason=q_info.get("reason", "Critical driver required for baseline financial model."),
                criticality=crit,
                data_type=q_info.get("data_type", "currency"),
                unit=q_info.get("unit"),
                options=q_info.get("options"),
                default_fallback=q_info.get("default_fallback"),
                allows_skip=q_info.get("allows_skip", True),
                voice_prompt=v_prompt,
                is_blocking=q_info.get("is_blocking", True),
            ))

        logger.info(f"[FINANCE FOUNDATION] Question engine generated {len(questions)} HIGH-criticality questions for lang={language}")
        return questions

    def prioritize_blocking_question(
        self,
        questions: List[RequiredUserInput],
    ) -> Optional[RequiredUserInput]:
        """
        Selects the single highest-priority blocking question to prompt the user one-at-a-time.
        Avoids cognitive overload and voice fatigue.
        """
        if not questions:
            return None

        # Priority order of genuine blockers
        priority_order = [
            "promoter_contribution",
            "business_constitution",
            "ownership_type",
            "monthly_rent",
            "opening_inventory",
            "selling_price",
            "jobs_per_day",
            "installed_capacity",
            "operating_days_per_month",
            "staff_count",
            "store_area",
            "experience_years",
        ]

        priority_map = {driver_id: idx for idx, driver_id in enumerate(priority_order)}
        
        # Sort by priority map, falling back to original order
        sorted_questions = sorted(
            questions,
            key=lambda q: priority_map.get(q.driver_id, 999)
        )
        return sorted_questions[0]


_QUESTION_CATALOG: Dict[str, Dict[str, Any]] = {
    "promoter_contribution": {
        "question_hi": "आप अपनी बचत से इस व्यवसाय में कितना पैसा निवेश कर सकते हैं?",
        "question_en": "How much of your own savings can you invest as margin money?",
        "voice_hi": "अपनी बचत से कितना पैसा लगा सकते हैं?",
        "voice_en": "How much of your own capital can you contribute?",
        "reason": "Required to determine bank loan amount and promoter equity.",
        "data_type": "currency", "unit": "INR",
        "default_fallback": 200000.0,
        "allows_skip": True,
        "is_blocking": True,
    },
    "business_constitution": {
        "question_hi": "आप व्यवसाय को किस रूप में पंजीकृत करने की योजना बना रहे हैं — अपनी प्रोप्राइटरशिप, पार्टनरशिप/LLP, या कंपनी?",
        "question_en": "How are you planning to register the business — as your own proprietorship, partnership/LLP, or company?",
        "voice_hi": "आप व्यवसाय को किस रूप में पंजीकृत करने की योजना बना रहे हैं?",
        "voice_en": "How are you planning to register the business — as a proprietorship, partnership/LLP, or company?",
        "reason": "Required to determine applicable legal entity constitution and statutory tax regime.",
        "data_type": "enum", "unit": "enum",
        "options": ["SOLE_PROPRIETORSHIP", "PARTNERSHIP_FIRM", "LLP", "COMPANY"],
        "default_fallback": "SOLE_PROPRIETORSHIP",
        "allows_skip": False,
        "is_blocking": True,
    },
    "ownership_type": {
        "question_hi": "क्या दुकान/कार्यशाला आपकी अपनी है या किराये पर?",
        "question_en": "Is the shop/workshop owned or rented?",
        "voice_hi": "क्या आप यह जगह किराये पर ले रहे हैं या खुद की है?",
        "voice_en": "Is the premises owned or rented?",
        "reason": "Required to determine occupancy cost.",
        "data_type": "enum", "unit": "enum",
        "options": ["OWN", "RENTED", "LEASED", "SHARED"],
        "default_fallback": "RENTED",
        "allows_skip": True,
        "is_blocking": True,
    },
    "monthly_rent": {
        "question_hi": "मासिक किराया लगभग कितना होगा?",
        "question_en": "What will be the approximate monthly rent?",
        "voice_hi": "दुकान का मासिक किराया कितना होगा?",
        "voice_en": "How much is the expected monthly rent?",
        "reason": "Required to calculate fixed operating costs.",
        "data_type": "currency", "unit": "INR/month",
        "default_fallback": None,
        "allows_skip": True,
        "is_blocking": True,
    },
    "opening_inventory": {
        "question_hi": "शुरुआती स्टॉक/माल में कितना निवेश करेंगे?",
        "question_en": "How much will you invest in opening stock?",
        "voice_hi": "शुरुआती स्टॉक में कितना निवेश करेंगे?",
        "voice_en": "What is your budget for initial inventory?",
        "reason": "Required to estimate working capital requirement.",
        "data_type": "currency", "unit": "INR",
        "default_fallback": 180000.0,
        "allows_skip": True,
        "is_blocking": True,
    },
    "selling_price": {
        "question_hi": "प्रति इकाई बिक्री मूल्य क्या होगा?",
        "question_en": "What will be the selling price per unit?",
        "voice_hi": "एक इकाई का औसत बिक्री मूल्य क्या होगा?",
        "voice_en": "What is the average selling price per unit?",
        "reason": "Required to calculate projected revenue.",
        "data_type": "currency", "unit": "INR/unit",
        "default_fallback": None,
        "allows_skip": True,
        "is_blocking": True,
    },
    "jobs_per_day": {
        "question_hi": "प्रतिदिन कितने ग्राहकों/कार्यों की अपेक्षा है?",
        "question_en": "How many customers/jobs do you expect per day?",
        "voice_hi": "रोजाना कितने ग्राहक आने की उम्मीद है?",
        "voice_en": "How many daily customers do you expect?",
        "reason": "Required to estimate service revenue.",
        "data_type": "integer", "unit": "count/day",
        "default_fallback": 12,
        "allows_skip": True,
        "is_blocking": True,
    },
    "installed_capacity": {
        "question_hi": "प्रतिदिन कितनी इकाइयाँ/मात्रा उत्पादन कर पाएंगे?",
        "question_en": "How many units/quantity can you produce per day?",
        "voice_hi": "प्रतिदिन कितनी मात्रा बना सकेंगे?",
        "voice_en": "What is your daily production capacity?",
        "reason": "Required to estimate revenue potential.",
        "data_type": "float", "unit": "units/day",
        "default_fallback": None,
        "allows_skip": True,
        "is_blocking": True,
    },
    "store_area": {
        "question_hi": "दुकान/कार्यशाला लगभग कितने वर्ग फुट की होगी?",
        "question_en": "What will be the approximate area in square feet?",
        "voice_hi": "दुकान का साइज कितने वर्ग फुट होगा?",
        "voice_en": "What is the store size in square feet?",
        "reason": "Required to estimate setup and utility costs.",
        "data_type": "float", "unit": "sqft",
        "default_fallback": 300.0,
        "allows_skip": True,
        "is_blocking": False,
    },
    "staff_count": {
        "question_hi": "क्या शुरुआत में आप खुद संभालेंगे या कर्मचारी रखेंगे? कितने?",
        "question_en": "Will you manage alone or hire staff? How many?",
        "voice_hi": "शुरुआत में कितने कर्मचारी रखेंगे?",
        "voice_en": "How many staff members do you plan to employ?",
        "reason": "Required to estimate salary expenses.",
        "data_type": "integer", "unit": "persons",
        "default_fallback": 1,
        "allows_skip": True,
        "is_blocking": False,
    },
    "operating_days_per_month": {
        "question_hi": "दुकान या इकाई महीने में कितने दिन खुली रहेगी?",
        "question_en": "How many days per month will your business operate?",
        "voice_hi": "महीने में कितने दिन काम चलेगा?",
        "voice_en": "How many days a month will you operate?",
        "reason": "Required to accurately project monthly revenue from daily transactions.",
        "data_type": "integer", "unit": "days/month",
        "options": ["24", "26", "28", "30"],
        "default_fallback": 26,
        "allows_skip": True,
        "is_blocking": False,
    },
    "experience_years": {
        "question_hi": "इस क्षेत्र में आपका कितने वर्षों का अनुभव है?",
        "question_en": "How many years of experience do you have in this business line?",
        "voice_hi": "इस काम में कितने साल का अनुभव है?",
        "voice_en": "How many years of experience do you have?",
        "reason": "Required for promoter credit profile assessment.",
        "data_type": "float", "unit": "years",
        "default_fallback": 2.0,
        "allows_skip": True,
        "is_blocking": False,
    },
}


# Global singleton
question_engine = QuestionEngine()
