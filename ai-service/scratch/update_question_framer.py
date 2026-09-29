"""
Update dpr_question_framer.py to include provider, model, and fallback_used fields.
"""
target_file = r"c:\Users\shriy\OneDrive\Documents\KALPA SIH\ai-service\app\services\dpr_stage1\dpr_question_framer.py"

with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update FramedQuestionPayload
old_model = '''class FramedQuestionPayload(BaseModel):
    question: str = Field(..., description="One conversational, user-friendly question sentence")
    helper_text: str = Field(..., description="One clear guidance sentence explaining what details to provide")
    example: Optional[str] = Field(None, description="One realistic example sentence for the business")
    why_we_are_asking: str = Field(..., description="One sentence explaining the purpose for bank appraisal/DPR")'''

new_model = '''class FramedQuestionPayload(BaseModel):
    question: str = Field(..., description="One conversational, user-friendly question sentence")
    helper_text: str = Field(..., description="One clear guidance sentence explaining what details to provide")
    example: Optional[str] = Field(None, description="One realistic example sentence for the business")
    why_we_are_asking: str = Field(..., description="One sentence explaining the purpose for bank appraisal/DPR")
    provider: str = Field(default="sarvam", description="Question provider (sarvam or deterministic_catalog)")
    model: str = Field(default="sarvam-105b-conversations", description="Underlying model or catalog")
    fallback_used: bool = Field(default=False, description="Whether fallback catalog was used")'''

if old_model in code:
    code = code.replace(old_model, new_model)
    print("Updated FramedQuestionPayload")
else:
    print("WARNING: old_model not found")

# 2. Update get_fallback_question returns
# In get_fallback_question, replace all FramedQuestionPayload(...) calls to include provider="deterministic_catalog", model="deterministic_catalog", fallback_used=True
old_ret1 = '''        return FramedQuestionPayload(
            question=lang_dict["question"],
            helper_text=lang_dict["helper_text"],
            example=ex,
            why_we_are_asking=lang_dict["why_we_are_asking"]
        )'''

new_ret1 = '''        return FramedQuestionPayload(
            question=lang_dict["question"],
            helper_text=lang_dict["helper_text"],
            example=ex,
            why_we_are_asking=lang_dict["why_we_are_asking"],
            provider="deterministic_catalog",
            model="deterministic_catalog",
            fallback_used=True
        )'''

if old_ret1 in code:
    code = code.replace(old_ret1, new_ret1)
    print("Updated get_fallback_question curated return")

# For the other generic fallbacks in get_fallback_question:
old_ret2 = '''            return FramedQuestionPayload(
                question=f"आपके उद्यम के लिए {clean_label} का अनुमानित मान क्या है?",
                helper_text=f"कृपया सटीक संख्या या राशि{unit_str} दर्ज करें।",
                example=f"उदाहरण: अपनी व्यावसायिक योजना के अनुसार अनुमानित {clean_label} दर्ज करें।",
                why_we_are_asking=why_required or "यह जानकारी बैंक डीपीआर और वित्तीय विश्लेषण को पूरा करने के लिए आवश्यक है।"
            )'''
new_ret2 = '''            return FramedQuestionPayload(
                question=f"आपके उद्यम के लिए {clean_label} का अनुमानित मान क्या है?",
                helper_text=f"कृपया सटीक संख्या या राशि{unit_str} दर्ज करें।",
                example=f"उदाहरण: अपनी व्यावसायिक योजना के अनुसार अनुमानित {clean_label} दर्ज करें।",
                why_we_are_asking=why_required or "यह जानकारी बैंक डीपीआर और वित्तीय विश्लेषण को पूरा करने के लिए आवश्यक है।",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )'''
if old_ret2 in code:
    code = code.replace(old_ret2, new_ret2)

old_ret3 = '''            return FramedQuestionPayload(
                question=f"कृपया अपने व्यवसाय से संबंधित {clean_label} की जानकारी साझा करें:",
                helper_text="इसके बारे में संक्षिप्त विवरण प्रदान करें ताकि आपका प्रोजेक्ट विवरण स्पष्ट हो सके।",
                example="उदाहरण: अपने उद्यम की वर्तमान या प्रस्तावित स्थिति का संक्षेप में उल्लेख करें।",
                why_we_are_asking=why_required or "बैंक मूल्यांकन और ऋण पात्रता सत्यापन के लिए यह विवरण आवश्यक है।"
            )'''
new_ret3 = '''            return FramedQuestionPayload(
                question=f"कृपया अपने व्यवसाय से संबंधित {clean_label} की जानकारी साझा करें:",
                helper_text="इसके बारे में संक्षिप्त विवरण प्रदान करें ताकि आपका प्रोजेक्ट विवरण स्पष्ट हो सके।",
                example="उदाहरण: अपने उद्यम की वर्तमान या प्रस्तावित स्थिति का संक्षेप में उल्लेख करें।",
                why_we_are_asking=why_required or "बैंक मूल्यांकन और ऋण पात्रता सत्यापन के लिए यह विवरण आवश्यक है।",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )'''
if old_ret3 in code:
    code = code.replace(old_ret3, new_ret3)

old_ret4 = '''            return FramedQuestionPayload(
                question=f"तुमच्या व्यवसायासाठी {clean_label} चे अंदाजे प्रमाण किती आहे?",
                helper_text=f"कृपया अचूक आकडेवारी किंवा रक्कम{unit_str} प्रविष्ट करा.",
                example=f"उदाहरण: तुमच्या प्रकल्प योजनेनुसार {clean_label} ची रक्कम प्रविष्ट करा.",
                why_we_are_asking=why_required or "बँक डीपीआर अहवाल तयार करण्यासाठी ही माहिती आवश्यक आहे."
            )'''
new_ret4 = '''            return FramedQuestionPayload(
                question=f"तुमच्या व्यवसायासाठी {clean_label} चे अंदाजे प्रमाण किती आहे?",
                helper_text=f"कृपया अचूक आकडेवारी किंवा रक्कम{unit_str} प्रविष्ट करा.",
                example=f"उदाहरण: तुमच्या प्रकल्प योजनेनुसार {clean_label} ची रक्कम प्रविष्ट करा.",
                why_we_are_asking=why_required or "बँक डीपीआर अहवाल तयार करण्यासाठी ही माहिती आवश्यक आहे.",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )'''
if old_ret4 in code:
    code = code.replace(old_ret4, new_ret4)

old_ret5 = '''            return FramedQuestionPayload(
                question=f"कृपया तुमच्या व्यवसायाबाबत {clean_label} ची माहिती द्या:",
                helper_text="तुमच्या प्रकल्पाची मांडणी स्पष्ट करण्यासाठी याबद्दल थोडक्यात सांगा.",
                example="उदाहरण: तुमच्या व्यवसायाच्या सद्यस्थितीबद्दल थोडक्यात माहिती प्रविष्ट करा.",
                why_we_are_asking=why_required or "बँक कर्ज मूल्यांकन आणि शासकीय योजनांसाठी हे तपशील आवश्यक आहेत."
            )'''
new_ret5 = '''            return FramedQuestionPayload(
                question=f"कृपया तुमच्या व्यवसायाबाबत {clean_label} ची माहिती द्या:",
                helper_text="तुमच्या प्रकल्पाची मांडणी स्पष्ट करण्यासाठी याबद्दल थोडक्यात सांगा.",
                example="उदाहरण: तुमच्या व्यवसायाच्या सद्यस्थितीबद्दल थोडक्यात माहिती प्रविष्ट करा.",
                why_we_are_asking=why_required or "बँक कर्ज मूल्यांकन आणि शासकीय योजनांसाठी हे तपशील आवश्यक आहेत.",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )'''
if old_ret5 in code:
    code = code.replace(old_ret5, new_ret5)

old_ret6 = '''            return FramedQuestionPayload(
                question=f"What is the estimated {clean_label.lower()} for your enterprise?",
                helper_text=f"Please provide the expected numeric value or amount{unit_str}.",
                example=f"For example: Enter the planned {clean_label.lower()} based on your initial project outlay.",
                why_we_are_asking=why_required or "Required to calculate project economics and bank borrowing limits."
            )'''
new_ret6 = '''            return FramedQuestionPayload(
                question=f"What is the estimated {clean_label.lower()} for your enterprise?",
                helper_text=f"Please provide the expected numeric value or amount{unit_str}.",
                example=f"For example: Enter the planned {clean_label.lower()} based on your initial project outlay.",
                why_we_are_asking=why_required or "Required to calculate project economics and bank borrowing limits.",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )'''
if old_ret6 in code:
    code = code.replace(old_ret6, new_ret6)

old_ret7 = '''            return FramedQuestionPayload(
                question=f"Could you tell us about the {clean_label.lower()} for your enterprise?",
                helper_text="Provide a clear, brief description explaining how your business will operate.",
                example="For example: Describe the current or proposed arrangement for your business.",
                why_we_are_asking=why_required or "Required by commercial lenders and nodal agencies for appraisal."
            )'''
new_ret7 = '''            return FramedQuestionPayload(
                question=f"Could you tell us about the {clean_label.lower()} for your enterprise?",
                helper_text="Provide a clear, brief description explaining how your business will operate.",
                example="For example: Describe the current or proposed arrangement for your business.",
                why_we_are_asking=why_required or "Required by commercial lenders and nodal agencies for appraisal.",
                provider="deterministic_catalog",
                model="deterministic_catalog",
                fallback_used=True
            )'''
if old_ret7 in code:
    code = code.replace(old_ret7, new_ret7)

# 3. Update successful Sarvam call return in frame_question
old_sarvam_ret = '''                    parsed = json.loads(clean_str)
                    if isinstance(parsed, dict) and "question" in parsed:
                        return FramedQuestionPayload(
                            question=str(parsed["question"]).strip(),
                            helper_text=str(parsed.get("helper_text", "")).strip(),
                            example=str(parsed.get("example", "")).strip() if parsed.get("example") else None,
                            why_we_are_asking=str(parsed.get("why_we_are_asking", why_required)).strip()
                        )'''

new_sarvam_ret = '''                    parsed = json.loads(clean_str)
                    if isinstance(parsed, dict) and "question" in parsed:
                        return FramedQuestionPayload(
                            question=str(parsed["question"]).strip(),
                            helper_text=str(parsed.get("helper_text", "")).strip(),
                            example=str(parsed.get("example", "")).strip() if parsed.get("example") else None,
                            why_we_are_asking=str(parsed.get("why_we_are_asking", why_required)).strip(),
                            provider="sarvam",
                            model="sarvam-105b-conversations",
                            fallback_used=False
                        )'''

if old_sarvam_ret in code:
    code = code.replace(old_sarvam_ret, new_sarvam_ret)
    print("Updated Sarvam return")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(code)

print("Finished updating dpr_question_framer.py")
