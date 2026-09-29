"""
Stage 14.1 DPR Question Framer: LLM-Generated, Intent-Based, Multilingual Framing.

Architecture Invariant:
- The deterministic Question Engine decides WHICH field is missing, why it is required,
  field type, expected intent, validation, and dependencies.
- The LLM ONLY FRAMES the user-facing wording:
  1. question (1 concise, natural sentence)
  2. helper_text (1 short explanation sentence)
  3. example (1 realistic example sentence)
  4. why_we_are_asking (1 clear sentence explaining why the bank/DPR needs it)
- If the LLM is unconfigured, times out, or fails, the framer falls back to a curated,
  human-friendly deterministic catalog. NEVER outputs raw snake_case or "Please provide detail for <field_id>".
"""
import json
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class FramedQuestionPayload(BaseModel):
    question: str = Field(..., description="One conversational, user-friendly question sentence")
    helper_text: str = Field(..., description="One clear guidance sentence explaining what details to provide")
    example: Optional[str] = Field(None, description="One realistic example sentence for the business")
    why_we_are_asking: str = Field(..., description="One sentence explaining the purpose for bank appraisal/DPR")
    provider: str = Field(default="sarvam", description="Question provider (sarvam or deterministic_catalog)")
    model: str = Field(default="sarvam-105b-conversations", description="Underlying model or catalog")
    fallback_used: bool = Field(default=False, description="Whether fallback catalog was used")


# ============================================================================
# COMPREHENSIVE MULTILINGUAL DETERMINISTIC FALLBACK CATALOG
# ============================================================================

CURATED_FALLBACK_CATALOG: Dict[str, Dict[str, Dict[str, str]]] = {
    "promoter_name": {
        "en": {
            "question": "Please provide promoter/entrepreneur name",
            "helper_text": "Enter the full name of the person who owns or is starting this business. This information is used to identify the project promoter in the DPR.",
            "example": "Example: Rajesh Kumar Patil",
            "why_we_are_asking": "The bank requires the exact promoter legal name for credit appraisal, identity verification, and loan sanctioning."
        },
        "hi": {
            "question": "कृपया मुख्य उद्यमी / प्रमोटर का पूरा नाम दर्ज करें",
            "helper_text": "उस व्यक्ति का पूरा नाम दर्ज करें जो इस व्यवसाय का स्वामी है या इसे शुरू कर रहा है। इसका उपयोग डीपीआर में प्रोजेक्ट प्रमोटर की पहचान के लिए किया जाता है।",
            "example": "उदाहरण: राजेश कुमार पाटिल",
            "why_we_are_asking": "बैंक ऋण मूल्यांकन, पहचान सत्यापन और ऋण स्वीकृति के लिए प्रमोटर का आधिकारिक कानूनी नाम आवश्यक है।"
        },
        "mr": {
            "question": "कृपया मुख्य उद्योजक / प्रमोटरचे पूर्ण नाव प्रविष्ट करा",
            "helper_text": "हा व्यवसाय ज्या व्यक्तीच्या मालकीचा आहे किंवा जो सुरू करत आहे त्याचे पूर्ण नाव प्रविष्ट करा. डीपीआरमध्ये प्रकल्प प्रमोटर ओळखण्यासाठी ही माहिती वापरली जाते.",
            "example": "उदाहरण: राजेश कुमार पाटील",
            "why_we_are_asking": "बँक कर्ज मंजुरी आणि अधिकृत दस्तऐवजीकरणासाठी प्रमोटरचे कायदेशीर नाव आवश्यक आहे."
        },
        "kn": {
            "question": "ದಯವಿಟ್ಟು ಮುಖ್ಯ ಉದ್ಯಮಿ / ಪ್ರವರ್ತಕರ ಪೂರ್ಣ ಹೆಸರನ್ನು ನಮೂದಿಸಿ",
            "helper_text": "ಈ ವ್ಯವಹಾರವನ್ನು ಪ್ರಾರಂಭಿಸುತ್ತಿರುವ ಅಥವಾ ಮಾಲೀಕರಾಗಿರುವ ವ್ಯಕ್ತಿಯ ಪೂರ್ಣ ಹೆಸರನ್ನು ನಮೂದಿಸಿ. ಡಿಪಿಆರ್‌ನಲ್ಲಿ ಯೋಜನಾ ಪ್ರವರ್ತಕರನ್ನು ಗುರುತಿಸಲು ಈ ಮಾಹಿತಿಯನ್ನು ಬಳಸಲಾಗುತ್ತದೆ.",
            "example": "ಉದಾಹರಣೆ: ರಾಜೇಶ್ ಕುಮಾರ್ ಪಾಟೀಲ್",
            "why_we_are_asking": "ಸಾಲ ಮೌಲ್ಯಮಾಪನ ಮತ್ತು ದಾಖಲೆ ಪರಿಶೀಲನೆಗಾಗಿ ಬ್ಯಾಂಕಿಗೆ ಪ್ರವರ್ತಕರ ಅಧಿಕೃತ ಹೆಸರು ಅಗತ್ಯವಿದೆ."
        },
        "ta": {
            "question": "முதன்மை தொழில்முனைவோர் / விளம்பரதாரர் பெயரை உள்ளிடவும்",
            "helper_text": "இந்த வணிகத்தின் உரிமையாளர் அல்லது தொடங்குபவரின் முழுப் பெயரை உள்ளிடவும். டிபிஆரில் திட்ட அமைப்பாளரை அடையாளம் காண இது பயன்படுகிறது.",
            "example": "எடுத்துக்காட்டு: ராஜேஷ் குமார் பாட்டீல்",
            "why_we_are_asking": "வங்கி கடன் மதிப்பீடு மற்றும் சரிபார்ப்புக்கு உரிமையாளரின் அதிகாரப்பூர்வ பெயர் அவசியம்."
        },
        "te": {
            "question": "దయచేసి ప్రధాన వ్యవస్థాపకుడు / ప్రమోటర్ పూర్తి పేరును నమోదు చేయండి",
            "helper_text": "ఈ వ్యాపార యజమాని లేదా ప్రారంభిస్తున్న వ్యక్తి పూర్తి పేరును నమోదు చేయండి. డీపీఆర్‌లో ప్రాజెక్ట్ ప్రమోటర్‌ను గుర్తించడానికి ఇది ఉపయోగపడుతుంది.",
            "example": "ఉదాహరణ: రాజేష్ కుమార్ పాటిల్",
            "why_we_are_asking": "బ్యాంక్ రుణ మూల్యాంకనం మరియు గుర్తింపు ధృవీకరణ కోసం ప్రమోటర్ అధికారిక పేరు అవసరం."
        },
        "gu": {
            "question": "કૃપા કરીને મુખ્ય ઉદ્યોગસાહસિક / પ્રમોટરનું પૂરું નામ દાખલ કરો",
            "helper_text": "આ વ્યવસાયના માલિક અથવા શરૂ કરનાર વ્યક્તિનું પૂરું નામ દાખલ કરો. ડીપીઆરમાં પ્રોજેક્ટ પ્રમોટરની ઓળખ માટે આ માહિતીનો ઉપયોગ થાય છે.",
            "example": "ઉદાહરણ: રાજેશ કુમાર પાટીલ",
            "why_we_are_asking": "બેંક લોન મંજૂરી અને ઓળખ ચકાસણી માટે પ્રમોટરનું સત્તાવાર નામ જરૂરી છે."
        }
    },
    "entrepreneur_name": {
        "en": {
            "question": "Please provide promoter/entrepreneur name",
            "helper_text": "Enter the full name of the person who owns or is starting this business. This information is used to identify the project promoter in the DPR.",
            "example": "Example: Rajesh Kumar Patil",
            "why_we_are_asking": "The bank requires the exact promoter legal name for credit appraisal, identity verification, and loan sanctioning."
        },
        "hi": {
            "question": "कृपया मुख्य उद्यमी / प्रमोटर का पूरा नाम दर्ज करें",
            "helper_text": "उस व्यक्ति का पूरा नाम दर्ज करें जो इस व्यवसाय का स्वामी है या इसे शुरू कर रहा है। इसका उपयोग डीपीआर में प्रोजेक्ट प्रमोटर की पहचान के लिए किया जाता है।",
            "example": "उदाहरण: राजेश कुमार पाटिल",
            "why_we_are_asking": "बैंक ऋण मूल्यांकन, पहचान सत्यापन और ऋण स्वीकृति के लिए प्रमोटर का आधिकारिक कानूनी नाम आवश्यक है।"
        }
    },
    "business_activity": {
        "en": {
            "question": "Describe your business activity",
            "helper_text": "Explain what your business does, including product/service type, scale of operation, and target customers.",
            "example": "Example: Dairy farming with 10 cattle producing milk for local collection centers",
            "why_we_are_asking": "Establishes the core economic engine and operational model for bank feasibility appraisal."
        },
        "hi": {
            "question": "अपनी व्यावसायिक गतिविधि का विवरण दें",
            "helper_text": "बताएं कि आपका व्यवसाय क्या करता है, जिसमें उत्पाद/सेवा का प्रकार, संचालन का पैमाना और लक्षित ग्राहक शामिल हैं।",
            "example": "उदाहरण: 10 गाय-भैंसों के साथ डेयरी फार्मिंग, जो स्थानीय संग्रह केंद्रों को दूध आपूर्ति करती है।",
            "why_we_are_asking": "बैंक को परियोजना की व्यावसायिक व्यवहार्यता और दैनिक संचालन समझने के लिए यह आवश्यक है।"
        },
        "mr": {
            "question": "तुमच्या व्यावसायिक उपक्रमाचे वर्णन करा",
            "helper_text": "तुमचा व्यवसाय काय करतो, उत्पादनाचा/सेवेचा प्रकार, कामाचे प्रमाण आणि मुख्य ग्राहक कोणते ते स्पष्ट करा.",
            "example": "उदाहरण: १० जनावरांसह दुग्ध व्यवसाय आणि स्थानिक संकलन केंद्रांना दूध पुरवठा.",
            "why_we_are_asking": "बँकेला व्यवसायाची आर्थिक व्यवहार्यता समजण्यासाठी ही माहिती आवश्यक आहे."
        },
        "kn": {
            "question": "ನಿಮ್ಮ ವ್ಯಾಪಾರ ಚಟುವಟಿಕೆಯನ್ನು ವಿವರಿಸಿ",
            "helper_text": "ನಿಮ್ಮ ವ್ಯಾಪಾರ ಏನು ಮಾಡುತ್ತದೆ, ಉತ್ಪನ್ನ/ಸೇವೆಯ ಪ್ರಕಾರ ಮತ್ತು ಗ್ರಾಹಕರ ವಿವರಗಳನ್ನು ವಿವರಿಸಿ.",
            "example": "ಉದಾಹರಣೆ: ಸ್ಥಳೀಯ ಹಾಲು ಸಂಗ್ರಹ ಕೇಂದ್ರಗಳಿಗೆ ಹಾಲು ಪೂರೈಸುವ 10 ಹಸುಗಳ ಡೈರಿ ಫಾರ್ಮಿಂಗ್.",
            "why_we_are_asking": "ಯೋಜನೆಯ ಆರ್ಥಿಕ ಕಾರ್ಯಸಾಧ್ಯತೆಯನ್ನು ಮೌಲ್ಯಮಾಪನ ಮಾಡಲು ಬ್ಯಾಂಕ್‌ಗೆ ಇದು ಅಗತ್ಯವಿದೆ."
        },
        "ta": {
            "question": "உங்கள் வணிகச் செயல்பாட்டை விவரிக்கவும்",
            "helper_text": "தயாரிப்பு/சேவை வகை மற்றும் வாடிக்கையாளர்கள் உட்பட உங்கள் வணிகம் என்ன செய்கிறது என்பதை விளக்குங்கள்.",
            "example": "எடுத்துக்காட்டு: உள்ளூர் பால் சேகரிப்பு மையங்களுக்கு பால் வழங்கும் 10 மாடுகளுடன் கூடிய பால் பண்ணை.",
            "why_we_are_asking": "திட்டத்தின் சாத்தியக்கூறுகளை மதிப்பிட வங்கிக்கு இந்த தகவல் தேவை."
        },
        "te": {
            "question": "మీ వ్యాపార కార్యకలాపాన్ని వివరించండి",
            "helper_text": "ఉత్పత్తి/సేవ రకం, కార్యకలాపాల స్థాయి మరియు లక్ష్య కస్టమర్లతో సహా మీ వ్యాపారం ఏమి చేస్తుందో వివరించండి.",
            "example": "ఉదాహరణ: స్థానిక సేకరణ కేంద్రాలకు పాలు సరఫరా చేసే 10 పాడి పశువులతో డెయిరీ ఫార్మింగ్.",
            "why_we_are_asking": "ప్రాజెక్ట్ ఆర్థిక సాధ్యతను అంచనా వేయడానికి బ్యాంకుకు ఇది అవసరం."
        },
        "gu": {
            "question": "તમારી વ્યવસાયિક પ્રવૃત્તિનું વર્ણન કરો",
            "helper_text": "તમારો વ્યવસાય શું કરે છે, ઉત્પાદન/સેવાનો પ્રકાર અને લક્ષિત ગ્રાહકો વિશે વિગતવાર જણાવો.",
            "example": "ઉદાહરણ: સ્થાનિક કલેક્શન સેન્ટરો માટે દૂધ ઉત્પાદન કરતી 10 ગાયો સાથે ડેરી ફાર્મિંગ.",
            "why_we_are_asking": "પ્રોજેક્ટની વ્યવહારિકતા ચકાસવા માટે બેંકને આ માહિતી જરૂરી છે."
        }
    },
    "location": {
        "en": {
            "question": "Where is your business located?",
            "helper_text": "Provide village, district and state details. Location is used for market, scheme and feasibility analysis.",
            "example": "Example: Kolhapur, Maharashtra",
            "why_we_are_asking": "Required to determine regional government subsidies, local market catchment size, and bank branch jurisdiction."
        },
        "hi": {
            "question": "आपका व्यवसाय कहाँ स्थित है?",
            "helper_text": "गांव/कस्बा, जिला और राज्य का विवरण दें। स्थान का उपयोग बाजार मांग, सरकारी योजना और व्यवहार्यता विश्लेषण के लिए किया जाता है।",
            "example": "उदाहरण: कोल्हापुर, महाराष्ट्र",
            "why_we_are_asking": "क्षेत्रीय सरकारी सब्सिडी, स्थानीय बाजार आकार और बैंक शाखा अधिकार क्षेत्र तय करने के लिए यह आवश्यक है।"
        },
        "mr": {
            "question": "तुमचा व्यवसाय कुठे स्थित आहे?",
            "helper_text": "गाव/शहर, जिल्हा आणि राज्याचा तपशील द्या. बाजारपेठ, शासकीय योजना आणि व्यवहार्यता विश्लेषणासाठी स्थानाचा वापर केला जातो.",
            "example": "उदाहरण: कोल्हापूर, महाराष्ट्र",
            "why_we_are_asking": "शासकीय अनुदान, स्थानिक बाजारपेठेची व्याप्ती आणि बँक कार्यक्षेत्र निश्चित करण्यासाठी हे आवश्यक आहे."
        },
        "kn": {
            "question": "ನಿಮ್ಮ ವ್ಯವಹಾರ ಎಲ್ಲಿ ನೆಲೆಗೊಂಡಿದೆ?",
            "helper_text": "ಗ್ರಾಮ/ಪಟ್ಟಣ, ಜಿಲ್ಲೆ ಮತ್ತು ರಾಜ್ಯದ ವಿವರಗಳನ್ನು ನೀಡಿ. ಮಾರುಕಟ್ಟೆ, ಯೋಜನೆ ಮತ್ತು ಕಾರ್ಯಸಾಧ್ಯತೆಯ ವಿಶ್ಲೇಷಣೆಗಾಗಿ ಸ್ಥಳವನ್ನು ಬಳಸಲಾಗುತ್ತದೆ.",
            "example": "ಉದಾಹರಣೆ: ಕೊಲ್ಲಾಪುರ, ಮಹಾರಾಷ್ಟ್ರ",
            "why_we_are_asking": "ಸರ್ಕಾರಿ ಸಬ್ಸಿಡಿಗಳು ಮತ್ತು ಮಾರುಕಟ್ಟೆ ವ್ಯಾಪ್ತಿಯನ್ನು ನಿರ್ಧರಿಸಲು ಈ ವಿವರಗಳು ಅಗತ್ಯವಿದೆ."
        },
        "ta": {
            "question": "உங்கள் வணிகம் எங்கு அமைந்துள்ளது?",
            "helper_text": "கிராமம், மாவட்டம் மற்றும் மாநில விவரங்களை வழங்கவும். சந்தை, திட்டம் மற்றும் சாத்தியக்கூறு பகுப்பாய்விற்கு இருப்பிடம் பயன்படுகிறது.",
            "example": "எடுத்துக்காட்டு: கோலாப்பூர், மகாராஷ்டிரா",
            "why_we_are_asking": "அரசு மானியங்கள் மற்றும் சந்தை வாய்ப்புகளைத் தீர்மானிக்க இருப்பிட விவரங்கள் அவசியம்."
        },
        "te": {
            "question": "మీ వ్యాపారం ఎక్కడ ఉంది?",
            "helper_text": "గ్రామం, జిల్లా మరియు రాష్ట్ర వివరాలను అందించండి. మార్కెట్, పథకం మరియు సాధ్యత విశ్లేషణ కోసం స్థానాన్ని ఉపయోగిస్తారు.",
            "example": "ఉదాహరణ: కొల్హాపూర్, మహారాష్ట్ర",
            "why_we_are_asking": "ప్రభుత్వ రాయితీలు మరియు స్థానిక మార్కెట్ పరిమాణాన్ని నిర్ణయించడానికి ఈ వివరాలు అవసరం."
        },
        "gu": {
            "question": "તમારો વ્યવસાય ક્યાં આવેલો છે?",
            "helper_text": "ગામ, જિલ્લો અને રાજ્યની વિગતો આપો. બજાર, યોજના અને શક્યતા વિશ્લેષણ માટે સ્થાનનો ઉપયોગ થાય છે.",
            "example": "ઉદાહરણ: કોલ્હાપુર, મહારાષ્ટ્ર",
            "why_we_are_asking": "સરકારી સબસિડી અને સ્થાનિક બજારના કદને નિર્ધારિત કરવા માટે સ્થાન જરૂરી છે."
        }
    },
    "location_district": {
        "en": {
            "question": "Where is your business located?",
            "helper_text": "Provide village, district and state details. Location is used for market, scheme and feasibility analysis.",
            "example": "Example: Kolhapur, Maharashtra",
            "why_we_are_asking": "Required to determine regional government subsidies, local market catchment size, and bank branch jurisdiction."
        },
        "hi": {
            "question": "आपका व्यवसाय किस जिले और राज्य में स्थित है?",
            "helper_text": "गांव/कस्बा, जिला और राज्य का विवरण दें। स्थान का उपयोग बाजार मांग, सरकारी योजना और व्यवहार्यता विश्लेषण के लिए किया जाता है।",
            "example": "उदाहरण: कोल्हापुर, महाराष्ट्र",
            "why_we_are_asking": "क्षेत्रीय सरकारी सब्सिडी, स्थानीय बाजार आकार और बैंक शाखा अधिकार क्षेत्र तय करने के लिए यह आवश्यक है।"
        },
        "mr": {
            "question": "तुमचा व्यवसाय कोणत्या जिल्ह्यात आणि राज्यात आहे?",
            "helper_text": "गाव/शहर, जिल्हा आणि राज्याचा तपशील द्या. बाजारपेठ, शासकीय योजना आणि व्यवहार्यता विश्लेषणासाठी स्थानाचा वापर केला जातो.",
            "example": "उदाहरण: कोल्हापूर, महाराष्ट्र",
            "why_we_are_asking": "शासकीय अनुदान आणि बँक कार्यक्षेत्र निश्चित करण्यासाठी हे आवश्यक आहे."
        }
    },
    "total_project_cost": {
        "en": {
            "question": "How much investment is required?",
            "helper_text": "Enter the estimated project cost including machinery, infrastructure, working capital and other setup expenses.",
            "example": "Example: ₹5,00,000",
            "why_we_are_asking": "Banks evaluate total outlay against financial benchmarks to determine loan eligibility and capital structure."
        },
        "hi": {
            "question": "इस प्रोजेक्ट के लिए कुल कितने निवेश (प्रोजेक्ट लागत) की आवश्यकता है?",
            "helper_text": "मशीनरी, शेड/दुकान निर्माण, कार्यशील पूंजी और अन्य प्रारंभिक सेटअप खर्च सहित अनुमानित कुल लागत दर्ज करें।",
            "example": "उदाहरण: ₹5,00,000",
            "why_we_are_asking": "बैंक कुल निवेश के आधार पर ऋण पात्रता, सब्सिडी और ईएमआई भुगतान क्षमता का आकलन करता है।"
        },
        "mr": {
            "question": "या प्रकल्पासाठी एकूण किती गुंतवणुकीची (प्रकल्प खर्चाची) आवश्यकता आहे?",
            "helper_text": "यंत्रसामग्री, शेड/दुकान, खेळते भांडवल आणि इतर प्राथमिक सेटअप खर्चासह अंदाजे एकूण खर्च प्रविष्ट करा.",
            "example": "उदाहरण: ₹5,00,000",
            "why_we_are_asking": "बँक एकूण गुंतवणुकीच्या आधारे कर्ज मर्यादा आणि अनुदानाची रक्कम निश्चित करते."
        },
        "kn": {
            "question": "ಈ ಯೋಜನೆಗೆ ಎಷ್ಟು ಹೂಡಿಕೆಯ ಅಗತ್ಯವಿದೆ?",
            "helper_text": "ಯಂತ್ರೋಪಕರಣಗಳು, ಮೂಲಸೌಕರ್ಯ, ದುಡಿಯುವ ಬಂಡವಾಳ ಮತ್ತು ಇತರ ಆರಂಭಿಕ ವೆಚ್ಚಗಳು ಸೇರಿದಂತೆ ಅಂದಾಜು ಯೋಜನಾ ವೆಚ್ಚವನ್ನು ನಮೂದಿಸಿ.",
            "example": "ಉದಾಹರಣೆ: ₹5,00,000",
            "why_we_are_asking": "ಸಾಲದ ಅರ್ಹತೆ ಮತ್ತು ಬಂಡವಾಳ ರಚನೆಯನ್ನು ನಿರ್ಧರಿಸಲು ಬ್ಯಾಂಕ್ ಒಟ್ಟು ಯೋಜನಾ ವೆಚ್ಚವನ್ನು ಪರಿಶೀಲಿಸುತ್ತದೆ."
        },
        "ta": {
            "question": "இந்தத் திட்டத்திற்கு எவ்வளவு முதலீடு தேவைப்படுகிறது?",
            "helper_text": "இயந்திரங்கள், உள்கட்டமைப்பு, நடைமுறை மூலதனம் மற்றும் தொடக்க செலவுகள் உட்பட மதிப்பிடப்பட்ட திட்டச் செலவை உள்ளிடவும்.",
            "example": "எடுத்துக்காட்டு: ₹5,00,000",
            "why_we_are_asking": "கடன் தகுதி மற்றும் மானியத் தொகையைத் தீர்மானிக்க மொத்த திட்டச் செலவு வங்கிக்குத் தேவை."
        },
        "te": {
            "question": "ఈ ప్రాజెక్ట్ కోసం ఎంత పెట్టుబడి అవసరం?",
            "helper_text": "యంత్రాలు, మౌలిక సదుపాయాలు, వర్కింగ్ క్యాపిటల్ మరియు ఇతర ప్రారంభ ఖర్చులతో సహా అంచనా వేసిన ప్రాజెక్ట్ ఖర్చును నమోదు చేయండి.",
            "example": "ఉదాహరణ: ₹5,00,000",
            "why_we_are_asking": "రుణ అర్హతను మరియు రాయితీని నిర్ణయించడానికి బ్యాంక్ మొత్తం ప్రాజెక్ట్ వ్యయాన్ని పరిశీలిస్తుంది."
        },
        "gu": {
            "question": "આ પ્રોજેક્ટ માટે કેટલા રોકાણની જરૂર છે?",
            "helper_text": "મશીનરી, ઈન્ફ્રાસ્ટ્રક્ચર, કાર્યકારી મૂડી અને અન્ય શરૂઆતી ખર્ચ સહિત અંદાજિત પ્રોજેક્ટ ખર્ચ દાખલ કરો.",
            "example": "ઉદાહરણ: ₹5,00,000",
            "why_we_are_asking": "લોન પાત્રતા અને સબસિડી નક્કી કરવા માટે બેંક કુલ પ્રોજેક્ટ ખર્ચનું મૂલ્યાંકન કરે છે."
        }
    },
    "proposed_project_cost": {
        "en": {
            "question": "How much investment is required?",
            "helper_text": "Enter the estimated project cost including machinery, infrastructure, working capital and other setup expenses.",
            "example": "Example: ₹5,00,000",
            "why_we_are_asking": "Banks evaluate total outlay against financial benchmarks to determine loan eligibility and capital structure."
        },
        "hi": {
            "question": "इस प्रोजेक्ट के लिए कुल कितने निवेश (प्रोजेक्ट लागत) की आवश्यकता है?",
            "helper_text": "मशीनरी, शेड/दुकान निर्माण, कार्यशील पूंजी और अन्य प्रारंभिक सेटअप खर्च सहित अनुमानित कुल लागत दर्ज करें।",
            "example": "उदाहरण: ₹5,00,000",
            "why_we_are_asking": "बैंक कुल निवेश के आधार पर ऋण पात्रता, सब्सिडी और ईएमआई भुगतान क्षमता का आकलन करता है।"
        },
        "mr": {
            "question": "या प्रकल्पासाठी एकूण किती गुंतवणुकीची (प्रकल्प खर्चाची) आवश्यकता आहे?",
            "helper_text": "यंत्रसामग्री, शेड/दुकान, खेळते भांडवल आणि इतर प्राथमिक सेटअप खर्चासह अंदाजे एकूण खर्च प्रविष्ट करा.",
            "example": "उदाहरण: ₹5,00,000",
            "why_we_are_asking": "बँक एकूण गुंतवणुकीच्या आधारे कर्ज मर्यादा आणि अनुदानाची रक्कम निश्चित करते."
        }
    },
    "business_name": {
        "en": {
            "question": "What is the official or proposed name of your enterprise?",
            "helper_text": "Enter the business trade name that will appear on your bank account and DPR.",
            "example": "For example: {biz} or {biz} Store.",
            "why_we_are_asking": "The bank requires the exact trade name for credit appraisal and entity registration."
        },
        "hi": {
            "question": "आपके व्यवसाय या उद्यम का क्या नाम है?",
            "helper_text": "वह व्यापारिक नाम दर्ज करें जो आपके बैंक खाते और डीपीआर पर दर्ज किया जाएगा।",
            "example": "उदाहरण: {biz} या {biz} केंद्र।",
            "why_we_are_asking": "बैंक ऋण आवेदन और सरकारी योजनाओं के लिए आधिकारिक व्यापार नाम अनिवार्य है।"
        },
        "mr": {
            "question": "तुमच्या व्यवसायाचे किंवा उपक्रमाचे नाव काय आहे?",
            "helper_text": "तुमच्या बँक खात्यावर आणि डीपीआर अहवालात नोंदवले जाणारे व्यावसायिक नाव प्रविष्ट करा.",
            "example": "उदाहरण: {biz} किंवा {biz} केंद्र.",
            "why_we_are_asking": "बँक कर्ज प्रस्तावासाठी आणि अधिकृत नोंदींसाठी व्यवसायाचे नाव आवश्यक असते."
        },
        "kn": {
            "question": "ನಿಮ್ಮ ಉದ್ಯಮ ಅಥವಾ ವ್ಯವಹಾರದ ಹೆಸರೇನು?",
            "helper_text": "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆ ಮತ್ತು ಡಿಪಿಆರ್ ವರದಿಯಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳುವ ವ್ಯಾಪಾರದ ಹೆಸರನ್ನು ನಮೂದಿಸಿ.",
            "example": "ಉದಾಹರಣೆಗೆ: {biz} ಅಥವಾ {biz} ಸ್ಟೋರ್.",
            "why_we_are_asking": "ಸಾಲ ಮೌಲ್ಯಮಾಪನ ಮತ್ತು ನೋಂದಣಿಗಾಗಿ ಬ್ಯಾಂಕಿಗೆ ಅಧಿಕೃತ ವ್ಯಾಪಾರ ಹೆಸರು ಅಗತ್ಯವಿದೆ."
        },
        "ta": {
            "question": "உங்கள் நிறுவனத்தின் அதிகாரப்பூர்வ அல்லது உத்தேச பெயர் என்ன?",
            "helper_text": "உங்கள் வங்கிக் கணக்கு மற்றும் டிபிಆர் அறிக்கையில் இடம்பெறும் வணிகப் பெயரை உள்ளிடவும்.",
            "example": "எடுத்துக்காட்டாக: {biz} அல்லது {biz} ஸ்டோர்.",
            "why_we_are_asking": "கடன் மதிப்பீடு மற்றும் நிறுவன பதிவிற்காக வங்கிக்கு வணிகப் பெயர் தேவைப்படுகிறது."
        },
        "te": {
            "question": "మీ వ్యాపారం లేదా సంస్థ యొక్క పేరు ఏమిటి?",
            "helper_text": "మీ బ్యాంక్ ఖాతా మరియు డీపీఆర్ నివేదికలో కనిపించే వ్యాపార పేరును నమోదు చేయండి.",
            "example": "ఉదాహరణకు: {biz} లేదా {biz} స్టోర్.",
            "why_we_are_asking": "రుణ మూల్యాంకనం మరియు రిజిస్ట్రేషన్ కోసం బ్యాంక్‌కు ఖచ్చితమైన వ్యాపార పేరు అవసరం."
        },
        "gu": {
            "question": "તમારા વ્યવસાય અથવા સાહસનું નામ શું છે?",
            "helper_text": "તમારા બેંક ખાતા અને ડીપીઆર પર દર્શાવવામાં આવનાર વ્યાપારી નામ દાખલ કરો.",
            "example": "ઉદાહરણ તરીકે: {biz} અથવા {biz} સ્ટોર.",
            "why_we_are_asking": "લોન મૂલ્યાંકન અને સંસ્થા નોંધણી માટે બેંકને સત્તાવાર વ્યવસાય નામ જરૂરી છે."
        }
    },
    "legal_constitution": {
        "en": {
            "question": "What is the ownership structure (constitution) of your enterprise?",
            "helper_text": "Select whether you are the sole individual owner, working in partnership, or running a registered company.",
            "example": "For example: Sole Proprietorship if you own and manage the business entirely on your own.",
            "why_we_are_asking": "Loan agreements, security documentation, and liability limits depend strictly on your enterprise constitution."
        },
        "hi": {
            "question": "आपके व्यवसाय का स्वामित्व स्वरूप (कानूनी संविधान) क्या है?",
            "helper_text": "चुनें कि क्या आप अकेले मालिक (एकल स्वामित्व) हैं, साझेदारी में हैं या कोई पंजीकृत कंपनी चला रहे हैं।",
            "example": "उदाहरण: यदि आप पूरी तरह अकेले व्यवसाय चला रहे हैं तो 'एकल स्वामित्व (Proprietorship)' चुनें।",
            "why_we_are_asking": "बैंक ऋण अनुबंध और कानूनी दस्तावेजों को सही ढंग से तैयार करने के लिए यह अनिवार्य है।"
        },
        "mr": {
            "question": "तुमच्या व्यवसायाचे मालकी स्वरूप (कायदेशीर संविधान) काय आहे?",
            "helper_text": "तुम्ही स्वतः वैयक्तिक मालक (एकल मालकी) आहात, भागीदारीत आहात की नोंदणीकृत कंपनी आहे ते निवडा.",
            "example": "उदाहरण: स्वतः एकटेच व्यवसाय चालवत असल्यास 'एकल मालकी (Proprietorship)' निवडा.",
            "why_we_are_asking": "बँकेच्या कायदेशीर प्रक्रियेसाठी आणि कर्ज करारासाठी व्यवसायाची मालकी स्पष्ट असणे आवश्यक आहे."
        },
        "kn": {
            "question": "ನಿಮ್ಮ ಉದ್ಯಮದ ಮಾಲೀಕತ್ವದ ರಚನೆ (ಕಾನೂನು ಸಂವಿಧಾನ) ಯಾವುದು?",
            "helper_text": "ನೀವು ಏಕ ಮಾಲೀಕರಾಗಿದ್ದೀರಾ, ಪಾಲುದಾರಿಕೆಯಲ್ಲಿ ಕೆಲಸ ಮಾಡುತ್ತಿದ್ದೀರಾ ಅಥವಾ ಕಂಪನಿ ನಡೆಸುತ್ತಿದ್ದೀರಾ ಎಂಬುದನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
            "example": "ಉದಾಹರಣೆಗೆ: ನೀವು ಒಬ್ಬರೇ ವ್ಯಾಪಾರವನ್ನು ನಿರ್ವಹಿಸುತ್ತಿದ್ದರೆ 'ಏಕ ಮಾಲೀಕತ್ವ (Proprietorship)' ಆಯ್ಕೆಮಾಡಿ.",
            "why_we_are_asking": "ಸಾಲ ಒಪ್ಪಂದಗಳು ಮತ್ತು ಕಾನೂನು ದಾಖಲೆಗಳು ನಿಮ್ಮ ಮಾಲೀಕತ್ವ ರಚನೆಯ ಮೇಲೆ ಅವಲಂಬಿತವಾಗಿವೆ."
        },
        "ta": {
            "question": "உங்கள் நிறுவனத்தின் உரிமையாளர் அமைப்பு (சட்ட வடிவம்) என்ன?",
            "helper_text": "நீங்கள் தனி உரிமையாளரா, கூட்டாண்மையா அல்லது பதிவு செய்யப்பட்ட நிறுவனமா என்பதைத் தேர்வுசெய்க.",
            "example": "எடுத்துக்காட்டாக: நீங்களே முழுமையாக வணிகத்தை நடத்தினால் 'தனி உரிமையாளர்' என்பதைத் தேர்ந்தெடுக்கவும்.",
            "why_we_are_asking": "வங்கி கடன் ஒப்பந்தங்கள் மற்றும் ஆவணங்கள் உங்கள் நிறுவன சட்ட வடிவத்தைப் பொறுத்தது."
        },
        "te": {
            "question": "మీ వ్యాపారం యొక్క యాజమాన్య నిర్మాణం (చట్టపరమైన రాజ్యాంగం) ఏమిటి?",
            "helper_text": "మీరు ఏకైక యజమానినా, భాగస్వామ్యమా లేదా నమోదిత కంపెనీనా అనేది ఎంచుకోండి.",
            "example": "ఉదాహరణకు: మీరే స్వయంగా వ్యాపారాన్ని నిర్వహిస్తుంటే 'ఏకైక యాజమాన్యం' ఎంచుకోండి.",
            "why_we_are_asking": "బ్యాంక్ రుణ ఒప్పందాలు మరియు చట్టపరమైన పత్రాల కోసం ఇది చాలా అవసరం."
        },
        "gu": {
            "question": "તમારા વ્યવસાયનું માલિકીનું માળખું (કાનૂની બંધારણ) શું છે?",
            "helper_text": "તમે એકમાત્ર માલિક છો, ભાગીદારીમાં છો કે નોંધાયેલી કંપની ચલાવો છો તે પસંદ કરો.",
            "example": "ઉદાહરણ તરીકે: જો તમે એકલા વ્યવસાયનું સંચાલન કરતા હોવ તો 'એકલ માલિકી' પસંદ કરો.",
            "why_we_are_asking": "લોન કરારો અને કાનૂની દસ્તાવેજો માટે વ્યવસાયનું માલિકીનું માળખું જરૂરી છે."
        }
    },
    "operating_premises": {
        "en": {
            "question": "Where will your business operate from, and what is the premises arrangement?",
            "helper_text": "Specify whether you own the workspace/shop, are renting it, leasing it, or planning to purchase land.",
            "example": "For example: Rented commercial shop of 300 sq.ft at ₹8,000 monthly rent.",
            "why_we_are_asking": "Determines whether rental expenses or civil construction outlays must be factored into the project cost."
        },
        "hi": {
            "question": "आपका व्यवसाय कहाँ से संचालित होगा और दुकान/परिसर की क्या स्थिति है?",
            "helper_text": "बताएं कि क्या परिसर आपका खुद का है, किराए पर लिया गया है, पट्टे (लीज़) पर है या नया निर्माण प्रस्तावित है।",
            "example": "उदाहरण: मुख्य बाजार में 250 वर्ग फीट की दुकान, जिसका मासिक किराया ₹6,000 है।",
            "why_we_are_asking": "इससे बैंक को यह जानने में मदद मिलती है कि प्रोजेक्ट खर्च में किराया या भवन निर्माण लागत जोड़नी है या नहीं।"
        },
        "mr": {
            "question": "तुमचा व्यवसाय कुठून चालणार आहे आणि त्या जागेची स्थिती काय आहे?",
            "helper_text": "जागा स्वतःच्या मालकीची आहे, भाड्याने घेतली आहे, लीजवर आहे की नवीन खरेदी करायची आहे ते सांगा.",
            "example": "उदाहरण: मुख्य बाजारपेठेत 300 चौरस फुटांचे भाड्याचे दुकान (मासिक भाडे ₹7,000).",
            "why_we_are_asking": "प्रकल्पाच्या खर्चात जागेचे भाडे किंवा बांधकाम खर्च जोडायचा की नाही हे ठरवण्यासाठी ही माहिती आवश्यक आहे."
        }
    },
    "premises_status": {
        "en": {
            "question": "Do you already have a shop or premises secured for this business?",
            "helper_text": "Indicate if the space is owned, rented, leased, or proposed to be built.",
            "example": "For example: Select 'RENTED' if you have an active shop rent agreement.",
            "why_we_are_asking": "Ensures operating overheads and civil construction allocations are correctly scheduled in the financial model."
        },
        "hi": {
            "question": "क्या आपके पास इस व्यवसाय के लिए दुकान या कार्यस्थल उपलब्ध है?",
            "helper_text": "चुनें कि क्या जगह खुद की है, किराए पर है, लीज़ पर है या निर्माण करना बाकी है।",
            "example": "उदाहरण: यदि दुकान किराए पर है तो 'किराए पर (RENTED)' विकल्प चुनें।",
            "why_we_are_asking": "यह सुनिश्चित करता है कि वित्तीय मॉडल में किराया या निर्माण खर्च सटीक रूप से शामिल हो।"
        },
        "mr": {
            "question": "या व्यवसायासाठी तुमच्याकडे दुकान किंवा कामाची जागा उपलब्ध आहे का?",
            "helper_text": "जागा स्वतःची आहे, भाड्याची आहे, लीजची आहे की विकत घ्यायची आहे ते निवडा.",
            "example": "उदाहरण: जागा भाड्याने असल्यास 'RENTED' हा पर्याय निवडा.",
            "why_we_are_asking": "प्रकल्प खर्चात भाडे किंवा बांधकाम खर्चाचे अचूक नियोजन करण्यासाठी हे गरजेचे आहे."
        }
    },
    "promoter_contribution": {
        "en": {
            "question": "How much money are you planning to invest from your own savings into this project?",
            "helper_text": "Enter your own capital contribution (promoter margin) in Indian Rupees (₹).",
            "example": "For example: If you plan to put in ₹1,50,000 from personal savings, enter 150000.",
            "why_we_are_asking": "Banks require 5% to 25% promoter equity margin before sanctioning term loans and government subsidies."
        },
        "hi": {
            "question": "आप इस प्रोजेक्ट में अपनी खुद की बचत से कितना पैसा लगाने की योजना बना रहे हैं?",
            "helper_text": "अपनी खुद की पूंजी (प्रमोटर मार्जिन) की राशि भारतीय रुपये (₹) में दर्ज करें।",
            "example": "उदाहरण: यदि आप अपनी बचत से ₹1,50,000 निवेश कर रहे हैं, तो 150000 दर्ज करें।",
            "why_we_are_asking": "बैंक और सरकारी योजनाओं के तहत ऋण स्वीकृत करने से पहले 5% से 25% प्रमोटर योगदान आवश्यक होता है।"
        },
        "mr": {
            "question": "या प्रकल्पात तुम्ही स्वतःच्या बचतीमधून किती रक्कम गुंतवणार आहात?",
            "helper_text": "तुमचे स्वतःचे भांडवल (प्रमोटर मार्जिन) भारतीय रुपयांमध्ये (₹) प्रविष्ट करा.",
            "example": "उदाहरण: जर तुम्ही बचतीतून ₹1,50,000 गुंतवणार असाल तर 150000 प्रविष्ट करा.",
            "why_we_are_asking": "बँक कर्ज मंजूर करण्यापूर्वी ५% ते २५% स्वतःचे भांडवल (मार्जिन मनी) आवश्यक असते."
        }
    },
    "promoter_education": {
        "en": {
            "question": "What is the highest educational qualification of the promoter?",
            "helper_text": "Select the highest education level completed by the primary entrepreneur.",
            "example": "For example: Graduate if you have completed a Bachelor's degree.",
            "why_we_are_asking": "Assists bank appraisal officers in evaluating technical capability and subsidy scheme eligibility."
        },
        "hi": {
            "question": "मुख्य उद्यमी (प्रमोटर) की उच्चतम शैक्षणिक योग्यता क्या है?",
            "helper_text": "मुख्य उद्यमी द्वारा पूरी की गई उच्चतम शैक्षणिक योग्यता का चयन करें।",
            "example": "उदाहरण: यदि आपने कॉलेज की डिग्री पूरी की है तो 'स्नातक (Graduate)' चुनें।",
            "why_we_are_asking": "बैंक अधिकारी इसके आधार पर उद्यमी की तकनीकी क्षमता और सरकारी योजना पात्रता की जांच करते हैं।"
        },
        "mr": {
            "question": "मुख्य उद्योजकाची (प्रमोटरची) सर्वोच्च शैक्षणिक पात्रता काय आहे?",
            "helper_text": "मुख्य उद्योजकाने पूर्ण केलेल्या सर्वोच्च शिक्षणाचा पर्याय निवडा.",
            "example": "उदाहरण: पदवी पूर्ण केली असल्यास 'पदवीधर (Graduate)' निवडा.",
            "why_we_are_asking": "बँक कर्ज प्रस्तावात उद्योजकाची शैक्षणिक पार्श्वभूमी आणि योजना पात्रता तपासण्यासाठी हे आवश्यक आहे."
        }
    },
    "promoter_social_category": {
        "en": {
            "question": "Which social category or affirmative category applies to you?",
            "helper_text": "Indicate your category (General, Women, OBC, SC, ST, Minority, PH/Ex-Servicemen) for government scheme benefits.",
            "example": "For example: Women Entrepreneur or General Category.",
            "why_we_are_asking": "Enables KALPA to automatically unlock special government subsidies (such as higher PMEGP margin money)."
        },
        "hi": {
            "question": "आप किस सामाजिक या विशेष उद्यमी श्रेणी के अंतर्गत आते हैं?",
            "helper_text": "सरकारी योजनाओं में विशेष लाभ और सब्सिडी के लिए अपनी श्रेणी का चयन करें।",
            "example": "उदाहरण: महिला उद्यमी, अन्य पिछड़ा वर्ग (OBC) या सामान्य वर्ग।",
            "why_we_are_asking": "इससे सरकार द्वारा दी जाने वाली विशेष सब्सिडी (जैसे पीएमईजीपी में 25% से 35% अनुदान) का लाभ मिलता है।"
        },
        "mr": {
            "question": "तुम्ही कोणत्या सामाजिक किंवा विशेष उद्योजक प्रवर्गात मोडता?",
            "helper_text": "शासकीय योजनांमधील विशेष अनुदानासाठी आपला प्रवर्ग निवडा.",
            "example": "उदाहरण: महिला उद्योजक, इतर मागासवर्गीय (OBC) किंवा खुला प्रवर्ग.",
            "why_we_are_asking": "यामुळे पीएमईजीपी व इतर योजनांतर्गत मिळणारे जास्तीचे शासकीय अनुदान निश्चित होते."
        }
    },
    "promoter_edp_training_status": {
        "en": {
            "question": "Have you completed an Entrepreneurship Development Programme (EDP) training?",
            "helper_text": "Indicate whether you have completed EDP training, are currently enrolled, or plan to take it online.",
            "example": "For example: Select 'Completed' if you hold an RSETI, MSME, or certified EDP certificate.",
            "why_we_are_asking": "Mandatory compliance step under PMEGP and MSME lending schemes before loan disbursement."
        },
        "hi": {
            "question": "क्या आपने उद्यमिता विकास कार्यक्रम (EDP) का प्रशिक्षण पूरा किया है?",
            "helper_text": "बताएं कि क्या आपके पास ईडीपी प्रमाणपत्र है, वर्तमान में प्रशिक्षण ले रहे हैं या ऑनलाइन प्रशिक्षण करेंगे।",
            "example": "उदाहरण: यदि आपने आरसेटी (RSETI) या अन्य संस्थान से प्रशिक्षण लिया है तो 'हाँ, प्रमाणपत्र प्राप्त है' चुनें।",
            "why_we_are_asking": "पीएमईजीपी और अन्य सरकारी योजनाओं में ऋण वितरण से पूर्व यह प्रशिक्षण अनिवार्य होता है।"
        },
        "mr": {
            "question": "तुम्ही उद्योजकता विकास प्रशिक्षण (EDP Training) पूर्ण केले आहे का?",
            "helper_text": "तुमच्याकडे ईडीपी प्रमाणपत्र आहे का, सध्या प्रशिक्षण घेत आहात की ऑनलाइन प्रशिक्षण घेणार आहात ते सांगा.",
            "example": "उदाहरण: प्रशिक्षण पूर्ण झाले असल्यास 'होय, प्रमाणपत्र पूर्ण झाले आहे' निवडा.",
            "why_we_are_asking": "शासकीय कर्ज योजनांमध्ये कर्ज वितरणापूर्वी हे प्रशिक्षण पूर्ण असणे आवश्यक असते."
        }
    },
    "gst_applicability": {
        "en": {
            "question": "What is your GST registration status?",
            "helper_text": "Indicate if your business is registered for GST, exempt below turnover threshold, or currently applied.",
            "example": "For example: Exempted below threshold if your expected annual sales are under ₹20-40 Lakhs.",
            "why_we_are_asking": "Verifies statutory tax compliance readiness and input tax credit treatment in financial projections."
        },
        "hi": {
            "question": "आपके व्यवसाय की जीएसटी (GST) पंजीकरण स्थिति क्या है?",
            "helper_text": "बताएं कि क्या आपके पास जीएसटी नंबर है, टर्नओवर सीमा से कम है (छूट प्राप्त) या आवेदन किया गया है।",
            "example": "उदाहरण: यदि वार्षिक बिक्री ₹20-40 लाख से कम है तो 'टर्नओवर सीमा से कम (छूट प्राप्त)' चुनें।",
            "why_we_are_asking": "वित्तीय मॉडल में टैक्स अनुपालन और इनपुट टैक्स क्रेडिट का सही हिसाब लगाने के लिए यह आवश्यक है।"
        },
        "mr": {
            "question": "तुमच्या व्यवसायाची जीएसटी नोंदणी स्थिती काय आहे?",
            "helper_text": "जीएसटी क्रमांक उपलब्ध आहे, उलाढाल मर्यादेपेक्षा कमी आहे की नोंदणीसाठी अर्ज केला आहे ते सांगा.",
            "example": "उदाहरण: वार्षिक विक्री २०-४० लाखांपेक्षा कमी असल्यास 'उलाढाल मर्यादेपेक्षा कमी' निवडा.",
            "why_we_are_asking": "प्रकल्प अहवालात कर अनुपालन आणि अचूक आर्थिक अंदाज नोंदवण्यासाठी हे आवश्यक आहे."
        }
    },
    "target_customers": {
        "en": {
            "question": "Who are your primary target customers and buyers?",
            "helper_text": "Describe the main people or businesses who will purchase your goods or services regularly.",
            "example": "For example: Local village households, neighborhood residents, and regular buyers of {biz}.",
            "why_we_are_asking": "Demonstrates commercial demand and sales viability to the bank credit appraisal team."
        },
        "hi": {
            "question": "आपके मुख्य लक्षित ग्राहक और खरीदार कौन होंगे?",
            "helper_text": "उन लोगों, परिवारों या स्थानीय दुकानों का वर्णन करें जो आपके उत्पाद या सेवाएँ नियमित रूप से खरीदेंगे।",
            "example": "उदाहरण: आसपास के गांवों के ग्रामीण परिवार, स्थानीय निवासी और {biz} के नियमित ग्राहक।",
            "why_we_are_asking": "बैंक को यह विश्वास दिलाना आवश्यक है कि आपके व्यवसाय में नियमित ग्राहक और निरंतर बिक्री होगी।"
        },
        "mr": {
            "question": "तुमचे मुख्य ग्राहक किंवा खरेदीदार कोण असणार आहेत?",
            "helper_text": "तुमचा माल किंवा सेवा नियमितपणे खरेदी करणाऱ्या लोकांचे किंवा दुकानांचे वर्णन करा.",
            "example": "उदाहरण: स्थानिक गावातील कुटुंबे, परिसरातील रहिवासी आणि {biz} चे नियमित ग्राहक.",
            "why_we_are_asking": "बँकेला व्यवसायाच्या बाजारातील मागणीची आणि विक्रीच्या शक्यतेची खात्री देण्यासाठी हे आवश्यक आहे."
        }
    }
}


def get_fallback_question(
    field_id: str,
    field_label: str,
    field_type: str,
    intent: str,
    why_required: str,
    unit: Optional[str] = None,
    language: str = "en",
    business_name: Optional[str] = None,
    specific_business: Optional[str] = None
) -> FramedQuestionPayload:
    """
    Returns a high quality, human-friendly fallback question for the field.
    """
    clean_lang = language.strip().lower() if language else "en"
    clean_fid = str(field_id).strip().lower()
    biz_placeholder = specific_business or business_name or "dairy farming / retail enterprise"

    # 1. Direct Catalog Match
    if clean_fid in CURATED_FALLBACK_CATALOG:
        entry = CURATED_FALLBACK_CATALOG[clean_fid]
        lang_dict = entry.get(clean_lang) or entry.get("en")
        if lang_dict:
            q_text = lang_dict.get("question", "").replace("{biz}", biz_placeholder)
            h_text = lang_dict.get("helper_text", "").replace("{biz}", biz_placeholder)
            ex_text = lang_dict.get("example", "").replace("{biz}", biz_placeholder)
            why_text = lang_dict.get("why_we_are_asking", why_required).replace("{biz}", biz_placeholder)
            return FramedQuestionPayload(
                question=q_text,
                helper_text=h_text,
                example=ex_text if ex_text else None,
                why_we_are_asking=why_text,
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )

    # 2. Dynamic Smart Fallback based on field name and type
    clean_label = (field_label or clean_fid.replace("_", " ")).strip().title()

    if clean_lang == "hi":
        if field_type in ["number", "currency"]:
            unit_str = f" ({unit})" if unit else " (रुपये में)"
            return FramedQuestionPayload(
                question=f"आपके व्यवसाय के लिए {clean_label} की अनुमानित राशि या संख्या क्या है?",
                helper_text=f"कृपया सटीक संख्या या अनुमानित राशि{unit_str} दर्ज करें।",
                example=f"उदाहरण: अपनी परियोजना योजना के अनुसार {clean_label} दर्ज करें।",
                why_we_are_asking=why_required or "बैंक डीपीआर और वित्तीय विश्लेषण को पूरा करने के लिए यह जानकारी आवश्यक है।",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )
        else:
            return FramedQuestionPayload(
                question=f"कृपया अपने व्यवसाय के {clean_label} के बारे में बताएं:",
                helper_text="अपने प्रोजेक्ट के संचालन को स्पष्ट करने के लिए इसके बारे में संक्षिप्त विवरण दें।",
                example="उदाहरण: अपने व्यवसाय की वर्तमान या प्रस्तावित स्थिति का संक्षिप्त विवरण दें।",
                why_we_are_asking=why_required or "बैंक ऋण मूल्यांकन और सरकारी योजनाओं की पात्रता के लिए यह विवरण आवश्यक है।",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )
    elif clean_lang == "mr":
        if field_type in ["number", "currency"]:
            unit_str = f" ({unit})" if unit else " (रुपयांमध्ये)"
            return FramedQuestionPayload(
                question=f"तुमच्या व्यवसायासाठी {clean_label} ची अंदाजे रक्कम किंवा संख्या किती आहे?",
                helper_text=f"कृपया अचूक संख्या किंवा अंदाजे रक्कम{unit_str} प्रविष्ट करा.",
                example=f"उदाहरण: तुमच्या प्रकल्पानुसार {clean_label} प्रविष्ट करा.",
                why_we_are_asking=why_required or "बँक डीपीआर आणि आर्थिक विश्लेषणासाठी ही माहिती आवश्यक आहे.",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )
        else:
            return FramedQuestionPayload(
                question=f"कृपया तुमच्या व्यवसायातील {clean_label} बद्दल माहिती द्या:",
                helper_text="तुमच्या प्रकल्पाचे स्वरूप स्पष्ट करण्यासाठी याबद्दल थोडक्यात माहिती सांगा.",
                example="उदाहरण: तुमच्या व्यवसायाची सद्य किंवा प्रस्तावित स्थिती सांगा.",
                why_we_are_asking=why_required or "बँक कर्ज मूल्यमापन आणि योजनांच्या पात्रतेसाठी हा तपशील आवश्यक आहे.",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )
    else:
        if field_type in ["number", "currency"]:
            unit_str = f" in {unit}" if unit else " in INR (₹)"
            return FramedQuestionPayload(
                question=f"What is the estimated {clean_label.lower()} for your enterprise?",
                helper_text=f"Please provide the expected numeric value or amount{unit_str}.",
                example=f"Example: Enter the planned {clean_label.lower()} based on your project outlay.",
                why_we_are_asking=why_required or "Required to calculate project economics and bank borrowing limits.",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )
        else:
            return FramedQuestionPayload(
                question=f"Could you provide details about {clean_label.lower()}?",
                helper_text=f"Explain how {clean_label.lower()} will be managed in your business operations.",
                example=f"Example: Describe the current or proposed arrangement for {clean_label.lower()}.",
                why_we_are_asking=why_required or "Required by commercial lenders and nodal agencies for project appraisal.",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )


# ============================================================================
# LLM QUESTION FRAMER ENGINE
# ============================================================================

class DPRQuestionFramer:
    """
    Empathetic, multilingual question framing engine.
    Prompts the LLM with minimal deterministic context to generate conversational,
    rural-friendly questions with helper text and realistic examples.
    """

    SYSTEM_PROMPT = """You are KALPA's Empathetic Rural Business Assistant in India.
Your task is to take a required DPR (Detailed Project Report) field and frame ONE clear, conversational, friendly question for an entrepreneur who may have basic literacy.

RULES:
1. Output MUST be a valid JSON object with EXACTLY these four keys:
   {
     "question": "One friendly, conversational question sentence.",
     "helper_text": "One short guidance sentence explaining what specifics to mention.",
     "example": "One realistic, practical example sentence.",
     "why_we_are_asking": "One simple sentence explaining why the bank/DPR needs this without technical jargon."
   }
2. Language: Use the requested target language natively and fluently.
   - For Hindi / Marathi / Indic languages, use natural native vocabulary in the native script (Devanagari, etc.). DO NOT do literal machine translation.
3. Brevity: Keep each part concise (1 sentence each). No long paragraphs.
4. Simplicity: Avoid jargon like 'amortization', 'constitution', 'working capital cycle', 'DSCR'. Use simple terms like 'money from savings', 'who owns the shop', 'daily customers'.
5. Determinism: Strictly ground examples in the resolved business activity / specific business provided in the context. DO NOT assume or inject 'Saree Retail' unless the context explicitly specifies saree. If business type is not specified, use a general neutral business example.
6. JSON ONLY: Return strictly valid JSON with no markdown fences, no prefixes, no commentary.
"""

    async def frame_question(
        self,
        field_id: str,
        field_label: str,
        field_type: str,
        intent: str,
        why_required: str,
        unit: Optional[str] = None,
        allowed_values: Optional[List[Any]] = None,
        business_name: Optional[str] = None,
        archetype: Optional[str] = None,
        location: Optional[str] = None,
        language: str = "en",
        specific_business: Optional[str] = None
    ) -> FramedQuestionPayload:
        """
        Attempts Sarvam LLM framing. On failure or unconfigured state, returns the safe curated fallback.
        """
        clean_lang = language.strip().lower() if language else "en"

        # Check if Sarvam LLM is available
        sarvam_key = settings.SARVAM_API_KEY
        sarvam_enabled = settings.is_sarvam_llm_enabled() if callable(getattr(settings, "is_sarvam_llm_enabled", None)) else bool(getattr(settings, "is_sarvam_llm_enabled", True))
        is_sarvam_available = bool(sarvam_enabled and sarvam_key and len(str(sarvam_key).strip()) > 8 and not str(sarvam_key).startswith("your_"))

        if not is_sarvam_available:
            logger.info(f"[DPRQuestionFramer] Sarvam LLM unconfigured/disabled; using curated multilingual fallback for field='{field_id}', lang='{clean_lang}'")
            return get_fallback_question(
                field_id, field_label, field_type, intent, why_required, unit, clean_lang,
                business_name=business_name, specific_business=specific_business
            )

        # Build minimum relevant context for Sarvam
        user_prompt_dict = {
            "target_field_id": field_id,
            "field_label": field_label or field_id.replace("_", " ").title(),
            "field_data_type": field_type,
            "unit": unit or "None",
            "allowed_options": [str(v) for v in allowed_values] if allowed_values else "Free Text",
            "business_intent": intent or why_required,
            "why_bank_requires": why_required,
            "resolved_business_name": business_name if business_name and business_name != "your enterprise" else "None",
            "resolved_business_type": specific_business or (archetype if archetype and archetype != "retail" else "None"),
            "resolved_location": location or "None",
            "target_language": clean_lang
        }

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Frame the DPR question in language '{clean_lang}' based on this context:\n{json.dumps(user_prompt_dict, ensure_ascii=False)}"}
        ]

        endpoint = settings.SARVAM_LLM_ENDPOINT or "https://api.sarvam.ai/v1/chat/completions"
        model_name = settings.SARVAM_LLM_MODEL or "sarvam-105b-conversations"
        headers = {
            "api-subscription-key": str(sarvam_key),
            "Authorization": f"Bearer {sarvam_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 400,
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(endpoint, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.warning(f"[DPRQuestionFramer] Sarvam HTTP {resp.status_code} for '{field_id}'; using fallback.")
                    return get_fallback_question(
                        field_id, field_label, field_type, intent, why_required, unit, clean_lang,
                        business_name=business_name, specific_business=specific_business
                    )

                data = resp.json()
                if not isinstance(data, dict):
                    return get_fallback_question(
                        field_id, field_label, field_type, intent, why_required, unit, clean_lang,
                        business_name=business_name, specific_business=specific_business
                    )

                choices = data.get("choices") or []
                if not choices or not isinstance(choices[0], dict):
                    return get_fallback_question(
                        field_id, field_label, field_type, intent, why_required, unit, clean_lang,
                        business_name=business_name, specific_business=specific_business
                    )

                msg = choices[0].get("message") or {}
                raw_content = msg.get("content") or msg.get("reasoning_content") or ""

                if isinstance(raw_content, str) and raw_content.strip():
                    # Parse JSON from string
                    clean_str = raw_content.strip()
                    if "```json" in clean_str:
                        clean_str = clean_str.split("```json")[1].split("```")[0].strip()
                    elif "```" in clean_str:
                        clean_str = clean_str.split("```")[1].split("```")[0].strip()

                    parsed = json.loads(clean_str)
                    if isinstance(parsed, dict) and "question" in parsed:
                        return FramedQuestionPayload(
                            question=str(parsed["question"]).strip(),
                            helper_text=str(parsed.get("helper_text", "")).strip(),
                            example=str(parsed.get("example", "")).strip() if parsed.get("example") else None,
                            why_we_are_asking=str(parsed.get("why_we_are_asking", why_required)).strip(),
                            provider="sarvam",
                            model="sarvam-105b-conversations",
                            fallback_used=False
                        )

                logger.warning(f"[DPRQuestionFramer] Sarvam payload missing expected fields for '{field_id}'; using fallback.")
                return get_fallback_question(
                    field_id, field_label, field_type, intent, why_required, unit, clean_lang,
                    business_name=business_name, specific_business=specific_business
                )

        except Exception as e:
            logger.warning(f"[DPRQuestionFramer] Exception during Sarvam LLM question framing for '{field_id}': {e}; using fallback.")
            return get_fallback_question(
                field_id, field_label, field_type, intent, why_required, unit, clean_lang,
                business_name=business_name, specific_business=specific_business
            )


dpr_question_framer = DPRQuestionFramer()
