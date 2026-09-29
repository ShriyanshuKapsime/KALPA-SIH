"""
Stage 1: DPR Question Engine.
Converts unresolved field gaps into prioritized, intent-based, conversational questions.
Integrates with DPRQuestionFramer (LLM + curated multilingual fallbacks) for natural wording
while strictly enforcing deterministic gap selection, field types, and validation rules.
Never asks for calculated financial values (DSCR, Project Cost, EBITDA, Depreciation, Tax).
"""
import logging
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.dpr_stage1.dpr_registry import (
    ALL_DPR_FIELDS,
    DPRFieldDefinition,
    FieldMateriality,
    FieldStatus,
    get_field_definition,
)
from app.services.dpr_stage1.dpr_gap_analyzer import DPRGapAnalysisResult, GapItem
from app.services.dpr_stage1.dpr_question_framer import dpr_question_framer, get_fallback_question
from app.services.dpr_stage1.dpr_canonical_field_registry import (
    CANONICAL_FIELDS,
    NEVER_ASKABLE_FIELD_IDS,
    get_canonical_entry,
    get_canonical_id,
    is_question_allowed,
    build_resolution_trace,
    FieldResolutionStatus,
    NON_ASKABLE_STATUSES,
)
from app.services.sarvam_service import sarvam_tts_service

logger = logging.getLogger(__name__)


# Deterministic Fallback Option Templates for Choice Fields
DETERMINISTIC_OPTION_TEMPLATES: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "premises_status": {
        "en": [
            {"label": "Already own the premises", "value": "OWNED"},
            {"label": "Rented shop / building", "value": "RENTED"},
            {"label": "Leased long term", "value": "LEASED"},
            {"label": "Planning to purchase / construct", "value": "PROPOSED_PURCHASE"}
        ],
        "hi": [
            {"label": "खुद की दुकान/परिसर है (OWNED)", "value": "OWNED"},
            {"label": "किराए पर है (RENTED)", "value": "RENTED"},
            {"label": "पट्टे (लीज़) पर है (LEASED)", "value": "LEASED"},
            {"label": "खरीदने/निर्माण की योजना है", "value": "PROPOSED_PURCHASE"}
        ],
        "mr": [
            {"label": "स्वतःच्या मालकीची जागा (OWNED)", "value": "OWNED"},
            {"label": "भाड्याने घेतलेली जागा (RENTED)", "value": "RENTED"},
            {"label": "दीर्घकालीन लीजवर (LEASED)", "value": "LEASED"},
            {"label": "जागा खरेदी/बांधकाम करणार", "value": "PROPOSED_PURCHASE"}
        ],
        "kn": [
            {"label": "ಸ್ವಂತ ಜಾಗ/ಮಳಿಗೆ ಇದೆ (OWNED)", "value": "OWNED"},
            {"label": "ಬಾಡಿಗೆ ಮಳಿಗೆ / ಕಟ್ಟಡ (RENTED)", "value": "RENTED"},
            {"label": "ದೀರ್ಘಾವಧಿ ಗುತ್ತಿಗೆ (LEASED)", "value": "LEASED"},
            {"label": "ಖರೀದಿಸಲು/ನಿರ್ಮಿಸಲು ಯೋಜನೆ ಇದೆ", "value": "PROPOSED_PURCHASE"}
        ],
        "ta": [
            {"label": "சொந்த கடை / இடம் உள்ளது (OWNED)", "value": "OWNED"},
            {"label": "வாடகை கடை / கட்டிடம் (RENTED)", "value": "RENTED"},
            {"label": "நீண்ட கால குத்தகை (LEASED)", "value": "LEASED"},
            {"label": "வாங்க/கட்ட திட்டம் உள்ளது", "value": "PROPOSED_PURCHASE"}
        ],
        "te": [
            {"label": "సొంత దుకాణం / స్థలం ఉంది (OWNED)", "value": "OWNED"},
            {"label": "అద్దె దుకాణం / భవనం (RENTED)", "value": "RENTED"},
            {"label": "దీర్ಘకాలిక లీజు (LEASED)", "value": "LEASED"},
            {"label": "కొనుగోలు/నిర్మించే ప్రణాళిక ఉంది", "value": "PROPOSED_PURCHASE"}
        ],
        "gu": [
            {"label": "પોતાની દુકાન / જગ્યા છે (OWNED)", "value": "OWNED"},
            {"label": "ભાડાની દુકાન / ઇમારત (RENTED)", "value": "RENTED"},
            {"label": "લાંબા ગાળાના પટ્ટે (LEASED)", "value": "LEASED"},
            {"label": "ખરીદવા/બાંધવાની યોજના છે", "value": "PROPOSED_PURCHASE"}
        ]
    },
    "legal_constitution": {
        "en": [
            {"label": "Sole Proprietorship (Single Owner)", "value": "PROPRIETORSHIP"},
            {"label": "Partnership Firm", "value": "PARTNERSHIP"},
            {"label": "Limited Liability Partnership (LLP)", "value": "LLP"},
            {"label": "Private Limited Company", "value": "PRIVATE_LIMITED"},
            {"label": "Farmer Producer Org (FPO) / Cooperative", "value": "FPO"}
        ],
        "hi": [
            {"label": "एकल स्वामित्व (Proprietorship)", "value": "PROPRIETORSHIP"},
            {"label": "साझेदारी फर्म (Partnership)", "value": "PARTNERSHIP"},
            {"label": "एलएलपी (LLP)", "value": "LLP"},
            {"label": "प्राइवेट लिमिटेड कंपनी", "value": "PRIVATE_LIMITED"},
            {"label": "किसान उत्पादक संगठन (FPO) / सहकारी", "value": "FPO"}
        ],
        "mr": [
            {"label": "एकल मालकी (Proprietorship)", "value": "PROPRIETORSHIP"},
            {"label": "भागीदारी संस्था (Partnership)", "value": "PARTNERSHIP"},
            {"label": "मर्यादित दायित्व भागीदारी (LLP)", "value": "LLP"},
            {"label": "प्रायव्हेट लिमिटेड कंपनी", "value": "PRIVATE_LIMITED"},
            {"label": "शेतकरी उत्पादक संस्था (FPO) / सहकारी", "value": "FPO"}
        ],
        "kn": [
            {"label": "ಏಕ ಮಾಲೀಕತ್ವ (Proprietorship)", "value": "PROPRIETORSHIP"},
            {"label": "ಪಾಲುದಾರಿಕೆ ಸಂಸ್ಥೆ (Partnership)", "value": "PARTNERSHIP"},
            {"label": "ಸೀಮಿತ ಹೊಣೆಗಾರಿಕೆ ಪಾಲುದಾರಿಕೆ (LLP)", "value": "LLP"},
            {"label": "ಖಾಸಗಿ ನಿಯಮಿತ ಕಂಪನಿ (Pvt Ltd)", "value": "PRIVATE_LIMITED"},
            {"label": "ರೈತ ಉತ್ಪಾದಕ ಸಂಸ್ಥೆ (FPO) / ಸಹಕಾರಿ", "value": "FPO"}
        ],
        "ta": [
            {"label": "தனி உரிமையாளர் (Proprietorship)", "value": "PROPRIETORSHIP"},
            {"label": "கூட்டாண்மை நிறுவனம் (Partnership)", "value": "PARTNERSHIP"},
            {"label": "வரையறுக்கப்பட்ட பொறுப்பு கூட்டாண்மை (LLP)", "value": "LLP"},
            {"label": "பிரைவேட் லிமிடெட் நிறுவனம்", "value": "PRIVATE_LIMITED"},
            {"label": "உழவர் உற்பத்தியாளர் அமைப்பு (FPO) / கூட்டுறவு", "value": "FPO"}
        ],
        "te": [
            {"label": "ఏకైక యాజమాన్యం (Proprietorship)", "value": "PROPRIETORSHIP"},
            {"label": "భాగస్వామ్య సంస్థ (Partnership)", "value": "PARTNERSHIP"},
            {"label": "పరిమిత బాధ్యత భాగస్వామ్యం (LLP)", "value": "LLP"},
            {"label": "ప్రైవేట్ లిమిటెడ్ కంపెనీ", "value": "PRIVATE_LIMITED"},
            {"label": "రైతు ఉత్పత్తిదారుల సంస్థ (FPO) / సహకార", "value": "FPO"}
        ],
        "gu": [
            {"label": "એકલ માલિકી (Proprietorship)", "value": "PROPRIETORSHIP"},
            {"label": "ભાગીદારી પેઢી (Partnership)", "value": "PARTNERSHIP"},
            {"label": "મર્યાદિત જવાબદારી ભાગીદારી (LLP)", "value": "LLP"},
            {"label": "પ્રાઇવેટ લિમિટેડ કંપની", "value": "PRIVATE_LIMITED"},
            {"label": "ખેડૂત ઉત્પાદક સંસ્થા (FPO) / સહકારી", "value": "FPO"}
        ]
    },
    "promoter_education": {
        "en": [
            {"label": "Below 8th Standard", "value": "BELOW_8TH"},
            {"label": "8th to 10th Standard", "value": "10TH_PASS"},
            {"label": "12th / Intermediate", "value": "12TH_PASS"},
            {"label": "Graduate / Degree Holder", "value": "GRADUATE"},
            {"label": "Post Graduate / Professional", "value": "POST_GRADUATE"}
        ],
        "hi": [
            {"label": "8वीं कक्षा से कम", "value": "BELOW_8TH"},
            {"label": "8वीं से 10वीं पास", "value": "10TH_PASS"},
            {"label": "12वीं पास", "value": "12TH_PASS"},
            {"label": "स्नातक (Graduate)", "value": "GRADUATE"},
            {"label": "स्नातकोत्तर या पेशेवर डिग्री", "value": "POST_GRADUATE"}
        ],
        "mr": [
            {"label": "८ वी पेक्षा कमी", "value": "BELOW_8TH"},
            {"label": "८ वी ते १० वी पास", "value": "10TH_PASS"},
            {"label": "१२ वी पास", "value": "12TH_PASS"},
            {"label": "पदवीधर (Graduate)", "value": "GRADUATE"},
            {"label": "पदव्युत्तर किंवा व्यावसायिक पदवी", "value": "POST_GRADUATE"}
        ],
        "kn": [
            {"label": "೮ ನೇ ತರಗತಿಗಿಂತ ಕಡಿಮೆ", "value": "BELOW_8TH"},
            {"label": "೮ ರಿಂದ ೧೦ ನೇ ತರಗತಿ ಪಾಸ್", "value": "10TH_PASS"},
            {"label": "೧೨ ನೇ ತರಗತಿ / ಪಿಯುಸಿ ಪಾಸ್", "value": "12TH_PASS"},
            {"label": "ಪದವೀಧರ (Graduate)", "value": "GRADUATE"},
            {"label": "ಸ್ನಾತಕೋತ್ತರ / ವೃತ್ತಿಪರ ಪದವಿ", "value": "POST_GRADUATE"}
        ],
        "ta": [
            {"label": "8 ஆம் வகுப்புக்கு கீழ்", "value": "BELOW_8TH"},
            {"label": "8 முதல் 10 ஆம் வகுப்பு வரை", "value": "10TH_PASS"},
            {"label": "12 ஆம் வகுப்பு / மேல்நிலை", "value": "12TH_PASS"},
            {"label": "பட்டதாரி (Graduate)", "value": "GRADUATE"},
            {"label": "முதுகலை / தொழில்முறை பட்டம்", "value": "POST_GRADUATE"}
        ],
        "te": [
            {"label": "8వ తరగతి కంటే తక్కువ", "value": "BELOW_8TH"},
            {"label": "8 నుండి 10వ తరగతి ఉత్తీర్ణత", "value": "10TH_PASS"},
            {"label": "12వ తరగతి / ఇంటర్మీడియట్", "value": "12TH_PASS"},
            {"label": "గ్రాడ్యుయేట్ (డిగ్రీ)", "value": "GRADUATE"},
            {"label": "పోస్ట్ గ్రాడ్యుయేట్ / ప్రొఫెషనల్", "value": "POST_GRADUATE"}
        ],
        "gu": [
            {"label": "૮ ધોરણથી ઓછું", "value": "BELOW_8TH"},
            {"label": "૮ થી ૧૦ પાસ", "value": "10TH_PASS"},
            {"label": "૧૨ પાસ / ઇન્ટરમીડિયેટ", "value": "12TH_PASS"},
            {"label": "સ્નાતક (Graduate)", "value": "GRADUATE"},
            {"label": "અનુસ્નાતક / વ્યવસાયિક ડિગ્રી", "value": "POST_GRADUATE"}
        ]
    },
    "promoter_social_category": {
        "en": [
            {"label": "General", "value": "GENERAL"},
            {"label": "Women Entrepreneur", "value": "WOMEN"},
            {"label": "OBC (Other Backward Classes)", "value": "OBC"},
            {"label": "SC (Scheduled Caste)", "value": "SC"},
            {"label": "ST (Scheduled Tribe)", "value": "ST"},
            {"label": "Minority Community", "value": "MINORITY"},
            {"label": "Ex-Servicemen / Person with Disability", "value": "PH_PWD"}
        ],
        "hi": [
            {"label": "सामान्य (General)", "value": "GENERAL"},
            {"label": "महिला उद्यमी (Women)", "value": "WOMEN"},
            {"label": "अन्य पिछड़ा वर्ग (OBC)", "value": "OBC"},
            {"label": "अनुसूचित जाति (SC)", "value": "SC"},
            {"label": "अनुसूचित जनजाति (ST)", "value": "ST"},
            {"label": "अल्पसंख्यक समुदाय", "value": "MINORITY"},
            {"label": "दिव्यांग / भूतपूर्व सैनिक", "value": "PH_PWD"}
        ],
        "mr": [
            {"label": "खुला प्रवर्ग (General)", "value": "GENERAL"},
            {"label": "महिला उद्योजक (Women)", "value": "WOMEN"},
            {"label": "इतर मागासवर्गीय (OBC)", "value": "OBC"},
            {"label": "अनुसूचित जाती (SC)", "value": "SC"},
            {"label": "अनुसूचित जमाती (ST)", "value": "ST"},
            {"label": "अल्पसंख्याक समुदाय", "value": "MINORITY"},
            {"label": "दिव्यांग / माजी सैनिक", "value": "PH_PWD"}
        ],
        "kn": [
            {"label": "ಸಾಮಾನ್ಯ (General)", "value": "GENERAL"},
            {"label": "ಮಹಿಳಾ ಉದ್ಯಮಿ (Women)", "value": "WOMEN"},
            {"label": "ಇತರ ಹಿಂದುಳಿದ ವರ್ಗಗಳು (OBC)", "value": "OBC"},
            {"label": "ಪರಿಶಿಷ್ಟ ಜಾತಿ (SC)", "value": "SC"},
            {"label": "ಪರಿಶಿಷ್ಟ ಪಂಗಡ (ST)", "value": "ST"},
            {"label": "ಅಲ್ಪಸಂಖ್ಯಾತ ಸಮುದಾಯ", "value": "MINORITY"},
            {"label": "ವಿಕಲಚೇತನರು / ಮಾಜಿ ಸೈನಿಕರು", "value": "PH_PWD"}
        ],
        "ta": [
            {"label": "பொதுப் பிரிவு (General)", "value": "GENERAL"},
            {"label": "பெண் தொழில்முனைவோர் (Women)", "value": "WOMEN"},
            {"label": "இதர பிற்படுத்தப்பட்டோர் (OBC)", "value": "OBC"},
            {"label": "பட்டியல் சாதியினர் (SC)", "value": "SC"},
            {"label": "பட்டியல் பழங்குடியினர் (ST)", "value": "ST"},
            {"label": "சிறுபான்மையினர் சமூகம்", "value": "MINORITY"},
            {"label": "மாற்றுத்திறனாளி / முன்னாள் ராணுவத்தினர்", "value": "PH_PWD"}
        ],
        "te": [
            {"label": "సాధారణ (General)", "value": "GENERAL"},
            {"label": "మహిళా వ్యవస్థాపకురాలు (Women)", "value": "WOMEN"},
            {"label": "ఇతర వెనుకబడిన తరగతులు (OBC)", "value": "OBC"},
            {"label": "షెడ్యూల్డ్ కులాలు (SC)", "value": "SC"},
            {"label": "షెడ్యూల్డ్ తెగలు (ST)", "value": "ST"},
            {"label": "మైనారిటీ కమ్యూనిటీ", "value": "MINORITY"},
            {"label": "దివ్యాంగులు / మాజీ సైనికులు", "value": "PH_PWD"}
        ],
        "gu": [
            {"label": "સામાન્ય (General)", "value": "GENERAL"},
            {"label": "મહિલા ઉદ્યોગસાહસિક (Women)", "value": "WOMEN"},
            {"label": "અન્ય પછાત વર્ગ (OBC)", "value": "OBC"},
            {"label": "અનુસૂચિત જાતિ (SC)", "value": "SC"},
            {"label": "અનુસૂચિત જનજાતિ (ST)", "value": "ST"},
            {"label": "લઘુમતી સમુદાય", "value": "MINORITY"},
            {"label": "દિવ્યાંગ / ભૂતપૂર્વ સૈનિક", "value": "PH_PWD"}
        ]
    },
    "promoter_edp_training_status": {
        "en": [
            {"label": "Yes, completed with certificate", "value": "COMPLETED"},
            {"label": "Currently enrolled / in progress", "value": "IN_PROGRESS"},
            {"label": "Not yet, planning online training", "value": "NOT_UNDERTAKEN"}
        ],
        "hi": [
            {"label": "हाँ, प्रमाणपत्र प्राप्त है", "value": "COMPLETED"},
            {"label": "वर्तमान में जारी है", "value": "IN_PROGRESS"},
            {"label": "अभी नहीं, ऑनलाइन करने की योजना है", "value": "NOT_UNDERTAKEN"}
        ],
        "mr": [
            {"label": "होय, प्रमाणपत्र पूर्ण झाले आहे", "value": "COMPLETED"},
            {"label": "सध्या प्रशिक्षण सुरू आहे", "value": "IN_PROGRESS"},
            {"label": "अद्याप नाही, प्रशिक्षण घेणार आहे", "value": "NOT_UNDERTAKEN"}
        ],
        "kn": [
            {"label": "ಹೌದು, ಪ್ರಮಾಣಪತ್ರ ಪಡೆದಿದ್ದೇನೆ", "value": "COMPLETED"},
            {"label": "ಪ್ರಸ್ತುತ ತರಬೇತಿ ನಡೆಯುತ್ತಿದೆ", "value": "IN_PROGRESS"},
            {"label": "ಇನ್ನೂ ಇಲ್ಲ, ಆನ್‌ಲೈನ್ ತರಬೇತಿ ಪಡೆಯುವ ಯೋಜನೆ ಇದೆ", "value": "NOT_UNDERTAKEN"}
        ],
        "ta": [
            {"label": "ஆம், சான்றிதழுடன் முடித்துள்ளேன்", "value": "COMPLETED"},
            {"label": "தற்போது பயிற்சி நடைபெற்று வருகிறது", "value": "IN_PROGRESS"},
            {"label": "இன்னும் இல்லை, ஆன்லைனில் பயிற்சி பெற திட்டம்", "value": "NOT_UNDERTAKEN"}
        ],
        "te": [
            {"label": "అవును, సర్టిఫికేట్ పూర్తయింది", "value": "COMPLETED"},
            {"label": "ప్రస్తుతం శిక్షణ కొనసాగుతోంది", "value": "IN_PROGRESS"},
            {"label": "ఇంకా లేదు, ఆన్‌లైన్ శిక్షణ ప్రణాళిక", "value": "NOT_UNDERTAKEN"}
        ],
        "gu": [
            {"label": "હા, પ્રમાણપત્ર સાથે પૂર્ણ કર્યું છે", "value": "COMPLETED"},
            {"label": "હાલમાં તાલીમ ચાલુ છે", "value": "IN_PROGRESS"},
            {"label": "હજુ સુધી નથી, ઓનલાઇન તાલીમ લેવાની યોજના છે", "value": "NOT_UNDERTAKEN"}
        ]
    },
    "gst_applicability": {
        "en": [
            {"label": "Already have GST registration", "value": "REGISTERED"},
            {"label": "Turnover is below threshold (Exempted)", "value": "EXEMPTED_BELOW_THRESHOLD"},
            {"label": "Applied for GST registration", "value": "APPLIED"}
        ],
        "hi": [
            {"label": "जीएसटी नंबर उपलब्ध है", "value": "REGISTERED"},
            {"label": "टर्नओवर सीमा से कम है (छूट प्राप्त)", "value": "EXEMPTED_BELOW_THRESHOLD"},
            {"label": "पंजीकरण के लिए आवेदन किया है", "value": "APPLIED"}
        ],
        "mr": [
            {"label": "जीएसटी क्रमांक उपलब्ध आहे", "value": "REGISTERED"},
            {"label": "उलाढाल मर्यादेपेक्षा कमी (सूट)", "value": "EXEMPTED_BELOW_THRESHOLD"},
            {"label": "नोंदणीसाठी अर्ज केला आहे", "value": "APPLIED"}
        ],
        "kn": [
            {"label": "ಈಗಾಗಲೇ ಜಿಎಸ್‌ಟಿ ನೋಂದಣಿ ಇದೆ", "value": "REGISTERED"},
            {"label": "ವಹಿವಾಟು ಮಿತಿಗಿಂತ ಕಡಿಮೆಯಿದೆ (ವಿನಾಯಿತಿ)", "value": "EXEMPTED_BELOW_THRESHOLD"},
            {"label": "ಜಿಎಸ್‌ಟಿ ನೋಂದಣಿಗೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಲಾಗಿದೆ", "value": "APPLIED"}
        ],
        "ta": [
            {"label": "ஏற்கனவே ஜிஎஸ்டி பதிவு உள்ளது", "value": "REGISTERED"},
            {"label": "விற்றுமுதல் வரம்புக்கு கீழே உள்ளது (விலக்கு)", "value": "EXEMPTED_BELOW_THRESHOLD"},
            {"label": "ஜிஎஸ்டி பதிவுக்கு விண்ணப்பிக்கப்பட்டுள்ளது", "value": "APPLIED"}
        ],
        "te": [
            {"label": "ఇప్పటికే జీఎస్టీ నమోదు ఉంది", "value": "REGISTERED"},
            {"label": "టర్నోవర్ పరిమితి కంటే తక్కువగా ఉంది (మినహాయింపు)", "value": "EXEMPTED_BELOW_THRESHOLD"},
            {"label": "జీఎస్టీ నమోదు కోసం దరఖాస్తు చేయబడింది", "value": "APPLIED"}
        ],
        "gu": [
            {"label": "પહેલેથી જીએસટી નંબર ઉપલબ્ધ છે", "value": "REGISTERED"},
            {"label": "ટર્નઓવર મર્યાદાથી ઓછું છે (મુક્તિ)", "value": "EXEMPTED_BELOW_THRESHOLD"},
            {"label": "જીએસટી નોંધણી માટે અરજી કરેલ છે", "value": "APPLIED"}
        ]
    }
}


class QuestionOption(BaseModel):
    label: str
    value: Any


class DPRQuestion(BaseModel):
    field_id: str
    question_id: str = ""
    intent: str = ""
    question_type: str = "OPEN_ENDED"  # OPEN_ENDED, NUMERIC, CHOICE, YES_NO, DATE, LOCATION
    question: str = ""
    question_text: str = ""  # alias for backward-compatibility
    title: str = ""          # user question title
    description: str = ""    # dynamic purpose description
    helper_text: str = ""
    example: Optional[str] = None
    why_we_are_asking: str = ""
    validationHint: str = "" # validation guidance / why bank asks
    validation_hint: str = "" # snake_case alias
    language: str = "en"
    input_type: str = "voice_or_text"  # voice_or_text, options, number, currency, text, boolean
    section_id: str = ""
    module_id: str = ""
    explanation: str = ""  # alias for backward-compatibility
    reason: str = ""       # alias for backward-compatibility
    expected_type: str = "string"
    options: Optional[List[QuestionOption]] = None
    allowed_values: Optional[List[Any]] = None
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_blocking: bool = False
    can_skip: bool = True
    audio_tts_supported: bool = True
    benchmark_value: Optional[Any] = None
    source_status: str = "USER_REQUIRED"
    dependencies: List[str] = Field(default_factory=list)
    impact_if_unanswered: str = ""
    downstream_impact_summary: str = ""
    resolution_trace: Optional[List[str]] = None
    provider: str = "sarvam"
    model: str = "sarvam-105b-conversations"
    fallback_used: bool = False


class DPRQuestionEngine:
    """
    Evaluates prioritized gaps and generates conversational, rural-friendly user questions.
    Strictly filters out calculated, benchmarkable, policy, and Stage 2 classification fields.
    """

    NON_ASKABLE_FIELDS: Set[str] = {
        # Stage 2 classification fields
        "business_archetype", "nic_code",
        # Calculated financial totals & schedules (Stage 9 / M1-M6)
        "total_project_cost", "glance_total_project_cost", "cost_land_building",
        "promoter_equity_amount", "bank_term_loan_amount", "glance_promoter_contribution",
        "glance_term_loan", "glance_average_dscr", "glance_break_even_utilization",
        "glance_employment_generation", "means_of_finance_reconciliation",
        "working_capital_bank_facility", "scheme_subsidy_percentage",
        "scheme_beneficiary_contribution_pct", "depreciation_schedule_summary",
        "projected_pnl_statements", "projected_balance_sheet", "projected_cash_flow",
        "loan_amortization_schedule", "dscr_analysis_multi_year", "break_even_metrics",
        "banking_ratios_summary", "stress_scenarios_appraisal", "risk_mitigation_matrix",
        "dynamic_swot_matrix", "feasibility_viability_synthesis", "evidence_source_register",
        "financial_integrity_verification", "alternative_scheme_recommendations",
        "cma_statement_summary", "contingency_mitigation_protocol",
        "inspection_sanction_signoff_box", "project_at_a_glance_summary",
    } | NEVER_ASKABLE_FIELD_IDS

    async def get_next_question(
        self,
        gap_analysis: DPRGapAnalysisResult,
        dpr_context_package: Dict[str, Any],
        language: Optional[str] = None,
    ) -> Optional[DPRQuestion]:
        """
        Picks the single highest-priority unresolved USER_REQUIRED gap and frames it
        conversationally via the LLM / curated multilingual framer.
        Prioritization Order:
          1. Blocking + CRITICAL materiality
          2. Blocking + HIGH materiality
          3. Blocking + MEDIUM materiality
          4. Non-blocking + HIGH materiality
          5. Non-blocking + MEDIUM materiality
        """
        raw_lang = language or dpr_context_package.get("raw_intake", {}).get("user_language") or dpr_context_package.get("user_language") or "en"
        clean_lang = raw_lang.strip().lower()

        fields_dict = dpr_context_package.get("fields", {})

        # Collect all eligible candidate gaps
        all_gaps: List[GapItem] = []
        all_gaps.extend(gap_analysis.blocking_gaps)
        all_gaps.extend(gap_analysis.high_priority_gaps)
        all_gaps.extend(gap_analysis.optional_gaps)

        # Deduplicate preserving order
        seen_fids = set()
        candidate_gaps: List[GapItem] = []
        for g in all_gaps:
            if g.field_id not in seen_fids:
                seen_fids.add(g.field_id)
                candidate_gaps.append(g)

        # Filter to only genuinely USER_REQUIRED fields
        eligible_gaps: List[GapItem] = []
        for g in candidate_gaps:
            fid = g.field_id
            if fid in self.NON_ASKABLE_FIELDS or fid in NEVER_ASKABLE_FIELD_IDS:
                continue

            # Check canonical registry permission
            if not is_question_allowed(fid):
                continue

            fdef = get_field_definition(fid)
            if not fdef or not fdef.editable:
                continue

            f_record = fields_dict.get(fid, {})
            f_status = str(f_record.get("status") or "")
            f_val = f_record.get("value")

            # If value is already present, never ask again
            if f_val is not None:
                continue

            # If status is non-askable / resolved, skip
            if f_status.startswith("RESOLVED_") or f_status in NON_ASKABLE_STATUSES or f_status in [
                "NOT_APPLICABLE", "DERIVED", "SOURCE_PENDING", "SOURCE_MAPPING_ERROR", "DOCUMENT_PENDING"
            ]:
                continue

            # Check resolution trace: if question is not allowed or status is non-askable, skip
            res_trace = build_resolution_trace(fid, fields_dict)
            if not res_trace.question_allowed or res_trace.status.startswith("RESOLVED_") or res_trace.status in NON_ASKABLE_STATUSES:
                continue

            if f_status in [FieldStatus.USER_REQUIRED.value, "USER_REQUIRED", FieldStatus.UNRESOLVED.value, "UNRESOLVED"]:
                eligible_gaps.append(g)

        if not eligible_gaps:
            return None

        # Sort by strict prioritization
        def _gap_priority(gap: GapItem) -> int:
            fdef = get_field_definition(gap.field_id)
            mat = fdef.materiality if fdef else FieldMateriality.MEDIUM
            if gap.is_blocking and mat == FieldMateriality.CRITICAL:
                return 1
            elif gap.is_blocking and mat == FieldMateriality.HIGH:
                return 2
            elif gap.is_blocking and mat == FieldMateriality.MEDIUM:
                return 3
            elif not gap.is_blocking and mat == FieldMateriality.HIGH:
                return 4
            elif not gap.is_blocking and mat == FieldMateriality.MEDIUM:
                return 5
            return 6

        eligible_gaps.sort(key=_gap_priority)
        target_gap = eligible_gaps[0]
        fid = target_gap.field_id
        fdef = get_field_definition(fid)

        if not fdef:
            logger.error(f"[DPRQuestionEngine] Could not find field definition for field_id='{fid}'.")
            return None

        # Determine question type
        if fid in DETERMINISTIC_OPTION_TEMPLATES or fdef.allowed_values:
            question_type = "CHOICE"
        elif fdef.field_type in ["number", "currency", "percentage"]:
            question_type = "NUMERIC"
        elif fdef.field_type == "boolean":
            question_type = "YES_NO"
        elif fdef.field_type in ["date", "datetime"]:
            question_type = "DATE"
        elif fid in ["location_district", "location_state", "location_pincode", "district", "state", "pincode", "village_name", "location"]:
            question_type = "LOCATION"
        else:
            question_type = "OPEN_ENDED"

        # Determine options if CHOICE
        options: Optional[List[QuestionOption]] = None
        if fid in DETERMINISTIC_OPTION_TEMPLATES:
            tpl_opts = DETERMINISTIC_OPTION_TEMPLATES[fid].get(clean_lang) or DETERMINISTIC_OPTION_TEMPLATES[fid]["en"]
            options = [QuestionOption(label=o["label"], value=o["value"]) for o in tpl_opts]
        elif fdef.allowed_values:
            options = [
                QuestionOption(label=str(av).replace("_", " ").title(), value=av)
                for av in fdef.allowed_values
            ]

        # Extract minimal relevant context for framing
        biz_name = (
            dpr_context_package.get("business_profile", {}).get("business_name")
            or dpr_context_package.get("raw_intake", {}).get("business_name")
        )
        specific_biz = (
            dpr_context_package.get("business_profile", {}).get("specific_business")
            or dpr_context_package.get("business_profile", {}).get("business_activity")
            or dpr_context_package.get("raw_intake", {}).get("specific_business")
            or dpr_context_package.get("raw_intake", {}).get("business_activity")
        )
        archetype = (
            dpr_context_package.get("business_profile", {}).get("archetype")
            or dpr_context_package.get("raw_intake", {}).get("archetype")
        )
        location = (
            dpr_context_package.get("location_profile", {}).get("district")
            or dpr_context_package.get("raw_intake", {}).get("district")
        )

        # Call LLM / Curated Multilingual Framer
        framed = await dpr_question_framer.frame_question(
            field_id=fid,
            field_label=fdef.label,
            field_type=fdef.field_type,
            intent=fdef.why_required,
            why_required=fdef.why_required,
            unit=fdef.unit,
            allowed_values=fdef.allowed_values,
            business_name=biz_name,
            archetype=archetype,
            location=location,
            language=clean_lang,
            specific_business=specific_biz
        )

        # Determine user-facing input_type
        if options:
            input_type = "options"
        elif fdef.field_type == "currency":
            input_type = "currency"
        elif fdef.field_type in ["number", "percentage"]:
            input_type = "number"
        elif fdef.field_type == "boolean":
            input_type = "boolean"
        else:
            input_type = "voice_or_text"

        downstream = (
            "Recalculates financial engine projections, project cost, and borrowing schedules."
            if fdef.field_type in ["number", "currency"]
            else "Enriches qualitative appraisal profiles and enterprise structure."
        )

        return DPRQuestion(
            field_id=fid,
            question_id=f"{fid}:v1",
            intent=fdef.why_required,
            question_type=question_type,
            question=framed.question,
            question_text=framed.question,
            title=framed.question,
            description=framed.helper_text,
            helper_text=framed.helper_text,
            example=framed.example,
            why_we_are_asking=framed.why_we_are_asking,
            validationHint=framed.why_we_are_asking,
            validation_hint=framed.why_we_are_asking,
            language=clean_lang,
            input_type=input_type,
            section_id=target_gap.section_id,
            module_id=target_gap.module_id,
            explanation=framed.helper_text,
            reason=framed.why_we_are_asking,
            expected_type=fdef.field_type,
            options=options,
            allowed_values=[o.value for o in options] if options else fdef.allowed_values,
            unit=fdef.unit,
            min_value=fdef.min_value,
            max_value=fdef.max_value,
            is_blocking=target_gap.is_blocking,
            can_skip=not target_gap.is_blocking,
            audio_tts_supported=True,
            source_status="USER_REQUIRED",
            dependencies=fdef.downstream_dependencies,
            impact_if_unanswered="Required to complete statutory entity and loan eligibility evaluation." if target_gap.is_blocking else "Optional operational detail.",
            downstream_impact_summary=downstream,
            resolution_trace=build_resolution_trace(fid, fields_dict).trace_steps,
            provider=getattr(framed, "provider", "sarvam"),
            model=getattr(framed, "model", "sarvam-105b-conversations"),
            fallback_used=getattr(framed, "fallback_used", False)
        )

    async def pick_next_question(
        self,
        arg1: Any,
        arg2: Any,
        language: Optional[str] = None
    ) -> Optional[DPRQuestion]:
        """Flexible method supporting either (gap_analysis, ctx) or (ctx, gaps)."""
        if isinstance(arg1, DPRGapAnalysisResult):
            return await self.get_next_question(gap_analysis=arg1, dpr_context_package=arg2, language=language)
        elif isinstance(arg2, DPRGapAnalysisResult):
            return await self.get_next_question(gap_analysis=arg2, dpr_context_package=arg1, language=language)
        elif isinstance(arg1, dict):
            return await self.get_next_question(gap_analysis=arg2, dpr_context_package=arg1, language=language)
        else:
            return await self.get_next_question(gap_analysis=arg1, dpr_context_package=arg2, language=language)

    async def synthesize_question_audio(self, question: DPRQuestion) -> Optional[Dict[str, Any]]:
        """
        Synthesizes audio for question + helper_text + example using Sarvam Bulbul TTS.
        Omits internal 'why_we_are_asking' metadata to keep audio natural and uncluttered.
        """
        try:
            parts = [question.question or question.question_text]
            if question.helper_text:
                parts.append(question.helper_text)
            if question.example:
                parts.append(question.example)
            
            full_speech_text = "\n".join(p for p in parts if p)

            audio_res = await sarvam_tts_service.synthesize_speech(
                text=full_speech_text,
                language_code=question.language
            )
            return audio_res
        except Exception as e:
            logger.warning(f"[DPRQuestionEngine] TTS audio synthesis note: {e}")
            return None


dpr_question_engine = DPRQuestionEngine()
