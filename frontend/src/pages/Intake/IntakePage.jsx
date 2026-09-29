import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Mic, 
  MicOff, 
  Square, 
  Globe2, 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle, 
  RotateCcw, 
  Lock, 
  Send, 
  MapPin, 
  IndianRupee, 
  Briefcase, 
  User, 
  Volume2, 
  VolumeX, 
  Edit3, 
  Compass, 
  Check, 
  X,
  HelpCircle,
  ChevronRight
} from 'lucide-react';
import Card, { CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';
import { SUPPORTED_LANGUAGES } from '../../i18n/translations';
import { reverseGeocodeCoords } from '../../services/geocoding';
import AgenticWorkflowThread from '../../components/workflow/AgenticWorkflowThread';

// Localized UI Texts across 7 Indian Languages
const UI_STRINGS = {
  en: {
    badge: 'Step 1 of KALPA Journey',
    title: 'Tell Us About Your Business Idea',
    subtitle: 'You can speak naturally in your mother tongue or type in your preferred language.',
    guidanceHeading: 'Tell us about your business idea naturally:',
    guidancePoints: [
      'What business you want to start or expand',
      'How much money you can invest',
      'Where you want to run it (village, town, district)',
      'Your relevant skills or experience'
    ],
    quickExamples: 'Quick Examples to Try:',
    textTab: 'Text Input',
    voiceTab: 'Voice Input',
    textPlaceholder: 'e.g. I want to start a dairy farm in Mandya with ₹2 lakh. I have experience in cattle farming.',
    continueBtn: 'Continue',
    processingText: 'Understanding your business idea...',
    readyToListen: 'Ready to listen. Tap to Speak',
    listening: 'Listening... Speak clearly in your language',
    processingSpeech: 'Processing speech with AI...',
    transcriptReceived: 'Transcript received. You can review or edit below:',
    confirmAndAnalyze: 'Confirm & Understand Business Idea',
    reRecord: 'Re-record',
    clarificationTitle: 'Clarification Needed',
    typeAnswerTab: 'Type Answer',
    speakAnswerTab: 'Speak Answer',
    submitAnswer: 'Submit Answer',
    listenQuestion: 'Listen',
    stopSpeaking: 'Stop Speaking',
    useCurrentLocation: 'Use Current Location',
    gpsLocating: 'Resolving location...',
    gpsSuccess: 'Device Location detected',
    noExperienceBtn: "I don't have experience",
    stage1CompleteTitle: 'Stage 1 Intake & Extraction Complete!',
    stage1CompleteDesc: 'Your business profile, capital, location, and skills have been structured and verified.',
    readyForPhase2: 'Ready for Stage 2: Business Classification & NIC Mapping',
    startOver: 'Start Over',
    edit: 'Edit',
    save: 'Save',
    cancel: 'Cancel',
    sourceUser: 'Provided by you',
    sourceGPS: 'Device Location'
  },
  hi: {
    badge: 'कल्पा यात्रा का चरण 1',
    title: 'अपने व्यवसाय का विचार हमें बताएं',
    subtitle: 'अपनी मातृभाषा में सहजता से बोलें या अपनी पसंदीदा भाषा में लिखें।',
    guidanceHeading: 'अपने व्यवसाय के बारे में स्वाभाविक रूप से बताएं:',
    guidancePoints: [
      'आप कौन सा व्यवसाय शुरू या बढ़ाना चाहते हैं',
      'आप कितना पैसा/बजट निवेश कर सकते हैं',
      'आप इसे कहाँ चलाना चाहते हैं (गाँव, कस्बा, जिला)',
      'आपका संबंधित अनुभव या कौशल'
    ],
    quickExamples: 'आज़माने के लिए त्वरित उदाहरण:',
    textTab: 'लिखकर बताएं',
    voiceTab: 'बोलकर बताएं',
    textPlaceholder: 'उदा: मैं मांड्या में ₹2 लाख के साथ डेयरी फार्म शुरू करना चाहता हूँ। मुझे पशुपालन का अनुभव है।',
    continueBtn: 'आगे बढ़ें',
    processingText: 'आपके व्यवसाय के विचार को समझा जा रहा है...',
    readyToListen: 'सुनने के लिए तैयार। बोलने के लिए टैप करें',
    listening: 'सुन रहे हैं... कृपया स्पष्ट बोलें',
    processingSpeech: 'सर्वम AI द्वारा आवाज़ को समझा जा रहा है...',
    transcriptReceived: 'आवाज़ प्राप्त हुई। नीचे समीक्षा करें या सुधारें:',
    confirmAndAnalyze: 'पुष्टि करें और विचार समझें',
    reRecord: 'फिर से रिकॉर्ड करें',
    clarificationTitle: 'स्पष्टीकरण की आवश्यकता है',
    typeAnswerTab: 'लिखकर उत्तर दें',
    speakAnswerTab: 'बोलकर उत्तर दें',
    submitAnswer: 'उत्तर भेजें',
    listenQuestion: 'प्रश्न सुनें',
    stopSpeaking: 'रोकें',
    useCurrentLocation: 'वर्तमान स्थान का उपयोग करें',
    gpsLocating: 'स्थान खोजा जा रहा है...',
    gpsSuccess: 'स्थान मिल गया',
    noExperienceBtn: 'मुझे पूर्व अनुभव नहीं है',
    stage1CompleteTitle: 'चरण 1 - जानकारी निष्कर्षण पूर्ण!',
    stage1CompleteDesc: 'आपकी व्यावसायिक अवधारणा, पूंजी, स्थान और कौशल का सत्यापन हो चुका है।',
    readyForPhase2: 'चरण 2: व्यवसाय वर्गीकरण और NIC मैपिंग के लिए तैयार',
    startOver: 'शुरू से शुरू करें',
    edit: 'बदलें',
    save: 'सहेजें',
    cancel: 'रद्द करें',
    sourceUser: 'आपके द्वारा दिया गया',
    sourceGPS: 'डिवाइस स्थान'
  },
  kn: {
    badge: 'ಕಲ್ಪ ಪ್ರಯಾಣದ ಹಂತ 1',
    title: 'ನಿಮ್ಮ ವ್ಯಾಪಾರ ಕಲ್ಪನೆಯನ್ನು ನಮಗೆ ತಿಳಿಸಿ',
    subtitle: 'ನಿಮ್ಮ ಮಾತೃಭಾಷೆಯಲ್ಲಿ ಮುಕ್ತವಾಗಿ ಮಾತನಾಡಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ.',
    guidanceHeading: 'ನಿಮ್ಮ ವ್ಯಾಪಾರ ಕಲ್ಪನೆಯ ಬಗ್ಗೆ ವಿವರವಾಗಿ ತಿಳಿಸಿ:',
    guidancePoints: [
      'ನೀವು ಯಾವ ವ್ಯವಹಾರವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೀರಿ',
      'ನೀವು ಎಷ್ಟು ಬಂಡವಾಳ ಹೂಡಿಕೆ ಮಾಡಬಹುದು',
      'ನೀವು ಅದನ್ನು ಎಲ್ಲಿ ನಡೆಸಲು ಬಯಸುತ್ತೀರಿ (ಗ್ರಾಮ, ಪಟ್ಟಣ, ಜಿಲ್ಲೆ)',
      'ನಿಮ್ಮ ಕೌಶಲ್ಯ ಅಥವಾ ಹಿಂದಿನ ಅನುಭವ'
    ],
    quickExamples: 'ಪ್ರಾರಂಭಿಸಲು ಮಾದರಿ ಉದಾಹರಣೆಗಳು:',
    textTab: 'ಪಠ್ಯ ಇನ್‌ಪುಟ್',
    voiceTab: 'ಧ್ವನಿ ಇನ್‌ಪುಟ್',
    textPlaceholder: 'ಉದಾ: ನಾನು ಮಂಡ್ಯದಲ್ಲಿ ₹2 ಲಕ್ಷ ಬಂಡವಾಳದೊಂದಿಗೆ ಡೈರಿ ಫಾರ್ಮ್ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ. ನನಗೆ ಹೈನುಗಾರಿಕೆ ಅನುಭವವಿದೆ.',
    continueBtn: 'ಮುಂದುವರಿಯಿರಿ',
    processingText: 'ವ್ಯಾಪಾರ ಕಲ್ಪನೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...',
    readyToListen: 'ಆಲಿಸಲು ಸಿದ್ಧವಾಗಿದೆ. ಮಾತನಾಡಲು ಒತ್ತಿ',
    listening: 'ಆಲಿಸಲಾಗುತ್ತಿದೆ... ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ',
    processingSpeech: 'ಧ್ವನಿಯನ್ನು ಪಠ್ಯಕ್ಕೆ ಪರಿವರ್ತಿಸಲಾಗುತ್ತಿದೆ...',
    transcriptReceived: 'ಧ್ವನಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ಪರಿಶೀಲಿಸಿ:',
    confirmAndAnalyze: 'ದೃಢೀಕರಿಸಿ ಮತ್ತು ವಿಶ್ಲೇಷಿಸಿ',
    reRecord: 'ಮರು ರೆಕಾರ್ಡ್ ಮಾಡಿ',
    clarificationTitle: 'ಸ್ಪಷ್ಟೀಕರಣ ಅಗತ್ಯವಿದೆ',
    typeAnswerTab: 'ಟೈಪ್ ಮಾಡಿ',
    speakAnswerTab: 'ಮಾತನಾಡಿ ಉತ್ತರಿಸಿ',
    submitAnswer: 'ಉತ್ತರ ಸಲ್ಲಿಸಿ',
    listenQuestion: 'ಪ್ರಶ್ನೆ ಆಲಿಸಿ',
    stopSpeaking: 'ನಿಲ್ಲಿಸಿ',
    useCurrentLocation: 'ಪ್ರಸ್ತುತ ಸ್ಥಳ ಬಳಸಿ',
    gpsLocating: 'ಸ್ಥಳ ಪತ್ತೆಹಚ್ಚಲಾಗುತ್ತಿದೆ...',
    gpsSuccess: 'ಸಾಧನದ ಸ್ಥಳ ಪತ್ತೆಯಾಗಿದೆ',
    noExperienceBtn: 'ನನಗೆ ಹಿಂದಿನ ಅನುಭವವಿಲ್ಲ',
    stage1CompleteTitle: 'ಹಂತ 1 - ಮಾಹಿತಿ ಸಂಗ್ರಹ ಪೂರ್ಣಗೊಂಡಿದೆ!',
    stage1CompleteDesc: 'ನಿಮ್ಮ ವ್ಯಾಪಾರ ವಿವರ, ಬಂಡವಾಳ, ಸ್ಥಳ ಮತ್ತು ಕೌಶಲ್ಯಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗಿದೆ.',
    readyForPhase2: 'ಹಂತ 2: ವ್ಯಾಪಾರ ವರ್ಗೀಕರಣಕ್ಕೆ ಸಿದ್ಧವಾಗಿದೆ',
    startOver: 'ಮತ್ತೆ ಪ್ರಾರಂಭಿಸಿ',
    edit: 'ತಿದ್ದುಪಡಿ',
    save: 'ಉಳಿಸಿ',
    cancel: 'ರದ್ದುಮಾಡಿ',
    sourceUser: 'ನೀವು ನೀಡಿದ ಮಾಹಿತಿ',
    sourceGPS: 'ಜಿಪಿಎಸ್ ಸ್ಥಳ'
  },
  mr: {
    badge: 'कल्पा प्रवासाचा टप्पा 1',
    title: 'तुमच्या व्यवसाय कल्पनेबद्दल सांगा',
    subtitle: 'तुमच्या मातृभाषेत सहज बोला किंवा तुमच्या पसंतीच्या भाषेत टाइप करा.',
    guidanceHeading: 'तुमच्या व्यवसायाबद्दल थोडक्यात सांगा:',
    guidancePoints: [
      'तुम्हाला कोणता व्यवसाय सुरू अथवा विस्तार करायचा आहे',
      'तुम्ही किती भांडवल गुंतवू शकता',
      'तुम्हाला हा व्यवसाय कुठे करायचा आहे (गाव, शहर, जिल्हा)',
      'तुमचे कौशल्य किंवा कामाचा अनुभव'
    ],
    quickExamples: 'सुरुवात करण्यासाठी नमुना कल्पना:',
    textTab: 'मजकूर इनपुट',
    voiceTab: 'आवाज इनपुट',
    textPlaceholder: 'उदा: मला ₹२ लाखांसह डेअरी फार्म सुरू करायचा आहे. मला पशुपालनाचा अनुभव आहे.',
    continueBtn: 'पुढे जा',
    processingText: 'व्यवसाय कल्पना समजून घेत आहे...',
    readyToListen: 'ऐकण्यासाठी सज्ज. बोलण्यासाठी टॅप करा',
    listening: 'ऐकत आहे... कृपया स्पष्ट बोला',
    processingSpeech: 'आवाज मजकुरात बदलत आहे...',
    transcriptReceived: 'आवाज प्राप्त झाला. खाली तपासा:',
    confirmAndAnalyze: 'पुष्टी करा आणि विश्लेषण करा',
    reRecord: 'पुन्हा रेकॉर्ड करा',
    clarificationTitle: 'स्पष्टीकरण आवश्यक आहे',
    typeAnswerTab: 'टाइप करा',
    speakAnswerTab: 'बोलून सांगा',
    submitAnswer: 'उत्तर पाठवा',
    listenQuestion: 'प्रश्न ऐका',
    stopSpeaking: 'थांबवा',
    useCurrentLocation: 'सध्याचे स्थान वापरा',
    gpsLocating: 'स्थान शोधत आहे...',
    gpsSuccess: 'स्थान सापडले',
    noExperienceBtn: 'मला अनुभव नाही',
    stage1CompleteTitle: 'टप्पा 1 - माहिती संकलन पूर्ण झाले!',
    stage1CompleteDesc: 'तुमची व्यावसायिक माहिती, भांडवल, स्थान आणि कौशल्यांची पडताळणी झाली आहे.',
    readyForPhase2: 'टप्पा 2: व्यवसाय वर्गीकरणासाठी तयार',
    startOver: 'पुन्हा सुरुवात करा',
    edit: 'बदला',
    save: 'जतन करा',
    cancel: 'रद्द करा',
    sourceUser: 'तुम्ही दिलेली माहिती',
    sourceGPS: 'डिव्हाइस स्थान'
  },
  ta: {
    badge: 'கல்பா பயணத்தின் படி 1',
    title: 'உங்கள் தொழில் யோசனையைப் பற்றி எங்களிடம் கூறுங்கள்',
    subtitle: 'உங்கள் தாய்மொழியில் இயல்பாகப் பேசுங்கள் அல்லது தட்டச்சு செய்யுங்கள்.',
    guidanceHeading: 'உங்கள் வணிக யோசனை குறித்து தெளிவாக விவரிக்கவும்:',
    guidancePoints: [
      'நீங்கள் என்ன தொழில் தொடங்க அல்லது விரிவாக்க விரும்புகிறீர்கள்',
      'நீங்கள் எவ்வளவு மூலதனம் முதலீடு செய்ய முடியும்',
      'எங்கு தொழில் நடத்த விரும்புகிறீர்கள் (கிராமம், நகரம், மாவட்டம்)',
      'உங்கள் திறன்கள் அல்லது முந்தைய அனுபவம்'
    ],
    quickExamples: 'மாதிரி உதாரணங்கள்:',
    textTab: 'உரை உள்ளீடு',
    voiceTab: 'குரல் உள்ளீடு',
    textPlaceholder: 'உதா: நான் ₹2 லட்சம் முதலீட்டில் பால் பண்ணை தொடங்க விரும்புகிறேன். எனக்கு கால்நடை வளர்ப்பு அனுபவம் உள்ளது.',
    continueBtn: 'தொடரவும்',
    processingText: 'வணிக யோசனை பகுப்பாய்வு செய்யப்படுகிறது...',
    readyToListen: 'கேட்க தயார். பேச கிளிக் செய்க',
    listening: 'கேட்கிறது... தெளிவாகப் பேசுங்கள்',
    processingSpeech: 'குரல் செயலாக்கப்படுகிறது...',
    transcriptReceived: 'குரல் பெறப்பட்டது. கீழே சரிபார்க்கவும்:',
    confirmAndAnalyze: 'உறுதிப்படுத்தி பகுப்பாய்வு செய்க',
    reRecord: 'மீண்டும் பதிவு செய்',
    clarificationTitle: 'விளக்கம் தேவைப்படுகிறது',
    typeAnswerTab: 'தட்டச்சு செய்',
    speakAnswerTab: 'பேசிப் பதிலளிக்கவும்',
    submitAnswer: 'பதிலைச் சமர்ப்பிக்கவும்',
    listenQuestion: 'கேள்வியைக் கேளுங்கள்',
    stopSpeaking: 'நிறுத்து',
    useCurrentLocation: 'தற்போதைய இருப்பிடத்தைப் பயன்படுத்து',
    gpsLocating: 'இருப்பிடம் கண்டறியப்படுகிறது...',
    gpsSuccess: 'இருப்பிடம் கண்டறியப்பட்டது',
    noExperienceBtn: 'எனக்கு முன் அனுபவம் இல்லை',
    stage1CompleteTitle: 'படி 1 - தகவல் பதிவு நிறைவுற்றது!',
    stage1CompleteDesc: 'உங்கள் தொழில் விவரம், மூலதனம், இடம் மற்றும் திறன்கள் சரிபார்க்கப்பட்டன.',
    readyForPhase2: 'படி 2: தொழில் வகைப்பாடுக்கு தயாராக உள்ளது',
    startOver: 'மீண்டும் தொடங்கவும்',
    edit: 'திருத்து',
    save: 'சேமி',
    cancel: 'ரத்து செய்',
    sourceUser: 'நீங்கள் வழங்கியது',
    sourceGPS: 'ஜிபிஎஸ் இருப்பிடம்'
  },
  te: {
    badge: 'కల్పా ప్రయాణం దశ 1',
    title: 'మీ వ్యాపార ఆలోచన గురించి మాకు చెప్పండి',
    subtitle: 'మీ మాతృభాషలో స్పష్టంగా మాట్లాడండి లేదా టైప్ చేయండి.',
    guidanceHeading: 'మీ వ్యాపార ఆలోచనను సహజంగా వివరించండి:',
    guidancePoints: [
      'మీరు ఏ వ్యాపారాన్ని ప్రారంభించాలనుకుంటున్నారు లేదా విస్తరించాలనుకుంటున్నారు',
      'మీరు ఎంత పెట్టుబడి పెట్టగలరు',
      'మీరు ఎక్కడ వ్యాపారం చేయాలనుకుంటున్నారు (గ్రామం, పట్టణం, జిల్లా)',
      'మీ నైపుణ్యాలు లేదా మునుపటి అనుభవం'
    ],
    quickExamples: 'ప్రారంభించడానికి నమూనా ఆలోచనలు:',
    textTab: 'వచన నమోదు',
    voiceTab: 'వాయిస్ నమోదు',
    textPlaceholder: 'ఉదా: నేను ₹2 లక్షల పెట్టుబడితో పాడి పరిశ్రమను ప్రారంభించాలనుకుంటున్నాను. నాకు అనుభవం ఉంది.',
    continueBtn: 'కొనసాగించండి',
    processingText: 'వ్యాపార ఆలోచన విశ్లేషించబడుతోంది...',
    readyToListen: 'వినడానికి సిద్ధంగా ఉంది. మాట్లాడటానికి నొక్కండి',
    listening: 'వింటోంది... స్పష్టంగా మాట్లాడండి',
    processingSpeech: 'వాయిస్ ప్రాసెస్ అవుతోంది...',
    transcriptReceived: 'వాయిస్ స్వీకరించబడింది. సమీక్షించండి:',
    confirmAndAnalyze: 'నిర్ధారించి విశ్లేషించండి',
    reRecord: 'మళ్ళీ రికార్డ్ చేయండి',
    clarificationTitle: 'స్పష్టత అవసరం',
    typeAnswerTab: 'టైప్ చేయండి',
    speakAnswerTab: 'మాట్లాడి సమాధానం ఇవ్వండి',
    submitAnswer: 'సమాధానం పంపండి',
    listenQuestion: 'ప్రశ్న వినండి',
    stopSpeaking: 'ఆపు',
    useCurrentLocation: 'ప్రస్తుత స్థానాన్ని ఉపయోగించండి',
    gpsLocating: 'స్థానం కనుగొనబడుతోంది...',
    gpsSuccess: 'స్థానం కనుగొనబడింది',
    noExperienceBtn: 'నాకు మునుపటి అనుభవం లేదు',
    stage1CompleteTitle: 'దశ 1 - సమాచార సేకరణ పూర్తయింది!',
    stage1CompleteDesc: 'మీ వ్యాపార వివరాలు, మూలధనం, స్థానం మరియు నైపుణ్యాలు ధృవీకరించబడ్డాయి.',
    readyForPhase2: 'దశ 2: వ్యాపార వర్గీకరణకు సిద్ధంగా ఉంది',
    startOver: 'మళ్లీ ప్రారంభించండి',
    edit: 'సవరించండి',
    save: 'సేవ్ చేయండి',
    cancel: 'రద్దు చేయి',
    sourceUser: 'మీరు అందించిన సమాచారం',
    sourceGPS: 'GPS స్థానం'
  },
  gu: {
    badge: 'કલ્પા યાત્રાનો તબક્કો 1',
    title: 'તમારા વ્યવસાય વિચાર વિશે જણાવો',
    subtitle: 'તમારી માતૃભાષામાં મુક્તપણે બોલો અથવા તમારી પસંદગીની ભાષામાં લખો.',
    guidanceHeading: 'તમારા વ્યવસાય વિચાર વિશે વિગતવાર જણાવો:',
    guidancePoints: [
      'તમે કયો વ્યવસાય શરૂ અથવા વિસ્તૃત કરવા માંગો છો',
      'તમે કેટલું મૂડી રોકાણ કરી શકો છો',
      'તમે તેને ક્યાં ચલાવવા માંગો છો (ગામ, નગર, જિલ્લો)',
      'તમારું કૌશલ્ય અથવા પૂર્વ અનુભવ'
    ],
    quickExamples: 'શરૂ કરવા માટે ઉદાહરણ વિચારો:',
    textTab: 'ટેક્સ્ટ ઇનપુટ',
    voiceTab: 'વૉઇસ ઇનપુટ',
    textPlaceholder: 'દા.ત.: હું ₹2 લાખના રોકાણ સાથે ડેરી ફાર્મ શરૂ કરવા માંગુ છું. મને પશુપાલનનો અનુભવ છે.',
    continueBtn: 'આગળ વધો',
    processingText: 'વ્યવસાય વિચારનું વિશ્લેષણ થઈ રહ્યું છે...',
    readyToListen: 'સાંભળવા માટે તૈયાર. બોલવા માટે ક્લિક કરો',
    listening: 'સાંભળી રહ્યા છીએ... કૃપા કરીને સ્પષ્ટ બોલો',
    processingSpeech: 'અવાજ લખાણમાં રૂપાંતરિત થઈ રહ્યો છે...',
    transcriptReceived: 'અવાજ પ્રાપ્ત થયો. નીચે ચકાસો:',
    confirmAndAnalyze: 'પુષ્ટિ કરો અને વિશ્લેષણ કરો',
    reRecord: 'ફરીથી રેકોર્ડ કરો',
    clarificationTitle: 'સ્પષ્ટીકરણ જરૂરી છે',
    typeAnswerTab: 'લખીને જવાબ આપો',
    speakAnswerTab: 'બોલીને જવાબ આપો',
    submitAnswer: 'જવાબ સબમિટ કરો',
    listenQuestion: 'પ્રશ્ન સાંભળો',
    stopSpeaking: 'રોકો',
    useCurrentLocation: 'હાલનું સ્થાન વાપરો',
    gpsLocating: 'સ્થાન શોધાઈ રહ્યું છે...',
    gpsSuccess: 'સ્થાન મળી ગયું',
    noExperienceBtn: 'મને પૂર્વ અનુભવ નથી',
    stage1CompleteTitle: 'તબક્કો 1 - માહિતી ઇનટેક પૂર્ણ!',
    stage1CompleteDesc: 'તમારી વ્યવસાય રૂપરેખા, મૂડી, સ્થાન અને કૌશલ્યોની ચકાસણી પૂર્ણ થઈ છે.',
    readyForPhase2: 'તબક્કો 2: વ્યવસાય વર્ગીકરણ માટે તૈયાર',
    startOver: 'ફરીથી શરૂ કરો',
    edit: 'સુધારો',
    save: 'સાચવો',
    cancel: 'રદ કરો',
    sourceUser: 'તમે આપેલી માહિતી',
    sourceGPS: 'GPS સ્થાન'
  }
};

// Display-safe error normalization helper (Guarantees strings; never renders objects as React children)
function getDisplayError(err, fallback = 'Something went wrong. Please try again.') {
  if (!err) return null;
  if (typeof err === 'string') return err;

  // Known STT error codes with friendly human explanations
  const code = err.code || err.error || (err.details && (err.details.error || err.details.code));
  if (code === 'STT_PROCESSING_FAILED') {
    return 'Voice recognition could not process your recording. Please try speaking clearly or enter your idea as text.';
  }
  if (code === 'STT_LANGUAGE_CODE_INVALID') {
    return 'The selected language is not supported for voice recognition. Please try typing your idea.';
  }
  if (code === 'STT_CONFIG_ERROR' || code === 'STT_INTERNAL_ERROR') {
    return 'Voice recognition service is temporarily unavailable. Please type your business idea below.';
  }

  // String message on error object
  if (typeof err.message === 'string' && err.message.trim()) {
    return err.message;
  }
  // Nested message object
  if (err.message && typeof err.message === 'object') {
    return getDisplayError(err.message, fallback);
  }

  // String detail
  if (typeof err.detail === 'string' && err.detail.trim()) {
    return err.detail;
  }
  if (err.detail && typeof err.detail === 'object') {
    return getDisplayError(err.detail, fallback);
  }

  // Details dictionary
  if (err.details && typeof err.details === 'object') {
    if (typeof err.details.message === 'string' && err.details.message.trim()) {
      return err.details.message;
    }
    if (typeof err.details.provider_error === 'string' && err.details.provider_error.trim()) {
      return err.details.provider_error;
    }
  }

  if (typeof err.error === 'string' && err.error.trim()) {
    return err.error;
  }

  return fallback;
}

export const IntakePage = () => {
  const navigate = useNavigate();
  const { updateWorkflowState, markStageComplete } = useWorkflow();
  const { language: universalLanguage, setLanguage: setUniversalLanguage } = useLanguage();
  const selectedLanguage = universalLanguage || 'en';

  const setSelectedLanguage = (code) => {
    setUniversalLanguage(code);
    if (profile?.session_id) {
      // Update language on active session
      apiService.intake.continueIntake({
        session_id: profile.session_id,
        language_code: code,
      }).then(setSessionResponse).catch(console.warn);
    }
  };
  
  // Intake Mode State
  const [activeTab, setActiveTab] = useState('text'); // 'text' | 'voice'
  const [textInput, setTextInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Main Voice Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceStatus, setVoiceStatus] = useState('idle'); // 'idle' | 'listening' | 'transcribing' | 'received'
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const browserRecognitionRef = useRef(null);
  const browserTranscriptRef = useRef('');

  // Stage 1 API Response & Canonical Profile Adapter
  const [sessionResponse, setSessionResponse] = useState(null);
  const profile = sessionResponse?.profile || (sessionResponse?.session_id ? sessionResponse : null);
  const nextAction = sessionResponse?.next_action || (profile?.next_action || null);

  // Sync Stage 1 structured result to sessionStorage and central workflow context
  useEffect(() => {
    if (sessionResponse) {
      console.log('[STAGE 1 CANONICAL RESULT]', sessionResponse);
      const activeProfile = sessionResponse.profile || sessionResponse;
      const sid = sessionResponse.session_id || activeProfile?.session_id;
      const bName = activeProfile?.business_concept || activeProfile?.business_idea;
      if (sid) {
        updateWorkflowState({
          sessionId: sid,
          businessName: bName,
          currentStage: 1,
          completedStages: [1],
          nextStage: 2
        });
      }
      try {
        sessionStorage.setItem('kalpa_stage1_response', JSON.stringify(sessionResponse));
      } catch (e) {
        console.warn('Unable to store Stage 1 result in sessionStorage:', e);
      }
    }
  }, [sessionResponse, updateWorkflowState]);

  // Follow-up interaction state
  const [followUpTab, setFollowUpTab] = useState('text'); // 'text' | 'voice'
  const [followUpAnswer, setFollowUpAnswer] = useState('');
  const [isSubmittingFollowUp, setIsSubmittingFollowUp] = useState(false);

  // Follow-up Voice State
  const [isFollowUpRecording, setIsFollowUpRecording] = useState(false);
  const [followUpRecordingTime, setFollowUpRecordingTime] = useState(0);
  const followUpMediaRecorderRef = useRef(null);
  const followUpAudioChunksRef = useRef([]);
  const followUpTimerRef = useRef(null);
  const followUpBrowserRecognitionRef = useRef(null);
  const followUpBrowserTranscriptRef = useRef('');

  // Text-To-Speech (TTS) State
  const [isSpeaking, setIsSpeaking] = useState(false);

  // GPS Fallback State
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsData, setGpsData] = useState(null);

  // Inline Profile Edit State
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState('');

  const t = UI_STRINGS[selectedLanguage] || UI_STRINGS.en;

  // Sample Prompts for Instant Multilingual Testing
  const samplePrompts = [
    {
      label: 'Saree Shop (Hindi)',
      lang: 'hi',
      text: 'मुझे साड़ी का दुकान खोलना है, मेरा बजट एक लाख रुपये।',
    },
    {
      label: 'Dairy Farm (Kannada)',
      lang: 'kn',
      text: 'ನಾನು ಮಂಡ್ಯದಲ್ಲಿ ₹2 ಲಕ್ಷ ಬಂಡವಾಳದೊಂದಿಗೆ ಡೈರಿ ಫಾರ್ಮ್ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ. ನನಗೆ ಹೈನುಗಾರಿಕೆ ಅನುಭವವಿದೆ.',
    },
    {
      label: 'Rice Mill (English)',
      lang: 'en',
      text: 'I want to start a rice mill in Mandya with ₹2 lakh. I have experience in agriculture.',
    },
    {
      label: 'Dairy Farm (Hindi)',
      lang: 'hi',
      text: 'मैं मांड्या में ₹2 लाख के साथ डेयरी फार्म शुरू करना चाहता हूँ। मुझे पशुपालन का अनुभव है।',
    },
    {
      label: 'Expand Grocery (Hinglish)',
      lang: 'en',
      text: 'Mera chhota kirana dukan hai aur expand karne ke liye 1.5 lakh budget hai.',
    },
  ];

  // Main Recording Timer
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(timerRef.current);
      setRecordingTime(0);
    }
    return () => clearInterval(timerRef.current);
  }, [isRecording]);

  // Follow-up Recording Timer
  useEffect(() => {
    if (isFollowUpRecording) {
      followUpTimerRef.current = setInterval(() => {
        setFollowUpRecordingTime((prev) => prev + 1);
      }, 1000);
    } else {
      clearInterval(followUpTimerRef.current);
      setFollowUpRecordingTime(0);
    }
    return () => clearInterval(followUpTimerRef.current);
  }, [isFollowUpRecording]);

  // Stop TTS on unmount or question change
  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [nextAction?.question]);

  // Synchronize language when profile returns auto-detected language
  useEffect(() => {
    if (sessionResponse?.language?.selected) {
      const code = sessionResponse.language.selected;
      if (['en', 'kn', 'hi'].includes(code)) {
        setSelectedLanguage(code);
      }
    }
  }, [sessionResponse]);

  // Text-To-Speech (TTS) Handler
  const handleToggleTTS = (textToSpeak) => {
    if (!('speechSynthesis' in window)) {
      setErrorMessage('Browser Text-to-Speech is not supported on this device.');
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const text = textToSpeak || nextAction?.question;
    if (!text) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Choose voice based on language code
    const voices = window.speechSynthesis.getVoices();
    const langVoiceMap = {
      kn: 'kn',
      hi: 'hi',
      mr: 'mr',
      ta: 'ta',
      te: 'te',
      gu: 'gu',
      en: 'en',
    };
    const prefix = langVoiceMap[selectedLanguage] || 'en';
    const matchedVoice = voices.find((v) => v.lang.toLowerCase().startsWith(prefix));

    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }
    utterance.lang = `${prefix}-IN`;
    utterance.rate = 0.95;

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  // Main Voice Recording Handlers
  const startRecording = async () => {
    setErrorMessage(null);
    setVoiceTranscript('');
    browserTranscriptRef.current = '';

    // Initialize browser speech recognition concurrently if supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = `${langVoiceMap[selectedLanguage] || 'en'}-IN`;
        recognition.onresult = (event) => {
          let text = '';
          for (let i = 0; i < event.results.length; ++i) {
            text += event.results[i][0].transcript + ' ';
          }
          const trimmed = text.trim();
          if (trimmed) {
            browserTranscriptRef.current = trimmed;
            setVoiceTranscript(trimmed);
          }
        };
        recognition.onerror = (e) => {
          console.warn('[BROWSER SPEECH REC ERROR]', e);
        };
        recognition.start();
        browserRecognitionRef.current = recognition;
      } catch (recErr) {
        console.warn('[BROWSER SPEECH REC INIT FAILED]', recErr);
      }
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        await handleVoiceSTT(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setVoiceStatus('listening');
    } catch (err) {
      console.error('Microphone access denied:', err);
      if (browserRecognitionRef.current) {
        try { browserRecognitionRef.current.stop(); } catch (e) {}
      }
      setErrorMessage('Microphone access was denied or not available. Please type your business idea below.');
      setVoiceStatus('idle');
    }
  };

  const stopRecording = () => {
    if (browserRecognitionRef.current) {
      try { browserRecognitionRef.current.stop(); } catch (e) {}
    }
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setVoiceStatus('transcribing');
    }
  };

  // Upload Voice to Sarvam STT (with graceful browser-transcript fallback)
  const handleVoiceSTT = async (audioBlob) => {
    setIsProcessing(true);
    setVoiceStatus('transcribing');
    setErrorMessage(null);

    const clientTranscript = (browserTranscriptRef.current || voiceTranscript || '').trim();

    const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage) || SUPPORTED_LANGUAGES[0];
    const formData = new FormData();
    formData.append('file', audioBlob, 'intake_recording.webm');
    if (clientTranscript) {
      formData.append('transcript', clientTranscript);
    }
    formData.append('language_code', langConfig.sarvamCode || 'unknown');
    formData.append('selected_language', langConfig.appCode === 'unknown' ? 'en' : langConfig.appCode);

    try {
      const response = await apiService.intake.submitVoice(formData);
      if (response && (response.transcript || response.profile)) {
        setVoiceTranscript(String(response.transcript || clientTranscript));
        setVoiceStatus('received');
        setSessionResponse(response);
      } else if (clientTranscript) {
        // Direct fallback to text submit using client transcript
        console.log('[INTAKE → VOICE] Falling back to text submit with transcript:', clientTranscript);
        await handleTextSubmit(clientTranscript);
      } else {
        throw {
          code: 'STT_PROCESSING_FAILED',
          message: 'Could not detect clear speech in the recording. Please speak closer to the microphone or enter your idea as text.'
        };
      }
    } catch (err) {
      console.error('[INTAKE → VOICE]', err);
      // Resilient fallback: If browser captured transcript, submit it as text!
      if (clientTranscript) {
        console.log('[INTAKE → VOICE RECOVERY] Submitting browser transcript as text:', clientTranscript);
        try {
          await handleTextSubmit(clientTranscript);
          return;
        } catch (textErr) {
          console.error('[INTAKE → VOICE RECOVERY FAILED]', textErr);
        }
      }
      const displayMsg = getDisplayError(err, 'Voice recognition could not process your recording. Please try speaking clearly or enter your idea as text below.');
      setErrorMessage(displayMsg);
      setVoiceStatus('idle');
      if (clientTranscript) {
        setTextInput(clientTranscript);
      }
      setActiveTab('text');
      setTimeout(() => {
        const inputEl = document.querySelector('textarea, input[type="text"]');
        if (inputEl) inputEl.focus();
      }, 100);
    } finally {
      setIsProcessing(false);
      setIsRecording(false);
      setRecordingTime(0);
    }
  };

  // Main Text Submission Handler
  const handleTextSubmit = async (customText = null, langOverride = null) => {
    const textToSubmit = customText || textInput;
    if (!textToSubmit || !textToSubmit.trim()) {
      setErrorMessage('Please enter a brief description of your business idea.');
      return;
    }

    setIsProcessing(true);
    setErrorMessage(null);

    const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage) || SUPPORTED_LANGUAGES[1];
    const lang = langOverride || (langConfig.appCode === 'unknown' ? 'en' : langConfig.appCode);

    try {
      const response = await apiService.intake.submitText({
        text: textToSubmit.trim(),
        language_code: lang,
        selected_language: lang,
      });
      setSessionResponse(response);
    } catch (err) {
      console.error('[INTAKE → TEXT]', err);
      const displayMsg = getDisplayError(err, 'Failed to process business intake. Please try again.');
      setErrorMessage(displayMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  // Follow-Up Voice Recording Handlers
  const startFollowUpRecording = async () => {
    setErrorMessage(null);
    followUpBrowserTranscriptRef.current = '';

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = selectedLanguage === 'kn' ? 'kn-IN' : selectedLanguage === 'hi' ? 'hi-IN' : 'en-IN';
        recognition.onresult = (event) => {
          let text = '';
          for (let i = 0; i < event.results.length; ++i) {
            text += event.results[i][0].transcript + ' ';
          }
          const trimmed = text.trim();
          if (trimmed) {
            followUpBrowserTranscriptRef.current = trimmed;
            setFollowUpAnswer(trimmed);
          }
        };
        recognition.onerror = (e) => {
          console.warn('[FOLLOW-UP SPEECH REC ERROR]', e);
        };
        recognition.start();
        followUpBrowserRecognitionRef.current = recognition;
      } catch (e) {
        console.warn('[FOLLOW-UP SPEECH REC INIT FAILED]', e);
      }
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      followUpAudioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      followUpMediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          followUpAudioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(followUpAudioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        await handleFollowUpVoiceSTT(audioBlob);
      };

      mediaRecorder.start();
      setIsFollowUpRecording(true);
    } catch (err) {
      console.error('Follow-up mic access denied:', err);
      if (followUpBrowserRecognitionRef.current) {
        try { followUpBrowserRecognitionRef.current.stop(); } catch (e) {}
      }
      setErrorMessage('Microphone access denied. You can type your answer instead.');
      setIsFollowUpRecording(false);
    }
  };

  const stopFollowUpRecording = () => {
    if (followUpBrowserRecognitionRef.current) {
      try { followUpBrowserRecognitionRef.current.stop(); } catch (e) {}
    }
    if (followUpMediaRecorderRef.current && isFollowUpRecording) {
      followUpMediaRecorderRef.current.stop();
      setIsFollowUpRecording(false);
    }
  };

  const handleFollowUpVoiceSTT = async (audioBlob) => {
    setIsSubmittingFollowUp(true);
    setErrorMessage(null);

    const clientTranscript = (followUpBrowserTranscriptRef.current || followUpAnswer || '').trim();

    const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage) || SUPPORTED_LANGUAGES[0];
    const formData = new FormData();
    formData.append('file', audioBlob, 'followup_recording.webm');
    if (clientTranscript) {
      formData.append('transcript', clientTranscript);
    }
    formData.append('language_code', langConfig.sarvamCode || 'unknown');
    formData.append('selected_language', langConfig.appCode === 'unknown' ? 'en' : langConfig.appCode);

    try {
      const response = await apiService.intake.submitVoice(formData);
      const resText = (response && response.transcript) ? String(response.transcript) : clientTranscript;
      if (resText) {
        setFollowUpAnswer(resText);
        // Automatically submit transcribed text to follow up
        await submitFollowUpPayload({ text: resText });
      } else {
        throw {
          code: 'STT_PROCESSING_FAILED',
          message: 'Could not detect clear speech. Please type your response.'
        };
      }
    } catch (err) {
      console.error('[INTAKE → FOLLOW-UP VOICE]', err);
      if (clientTranscript) {
        console.log('[INTAKE → FOLLOW-UP RECOVERY] Submitting client transcript:', clientTranscript);
        try {
          setFollowUpAnswer(clientTranscript);
          await submitFollowUpPayload({ text: clientTranscript });
          return;
        } catch (subErr) {
          console.error('[INTAKE → FOLLOW-UP RECOVERY FAILED]', subErr);
        }
      }
      const displayMsg = getDisplayError(err, 'Could not process voice answer. Please type your response below.');
      setErrorMessage(displayMsg);
      setFollowUpTab('text');
    } finally {
      setIsSubmittingFollowUp(false);
      setIsFollowUpRecording(false);
      setFollowUpRecordingTime(0);
    }
  };

  // Follow-Up Submission
  const submitFollowUpPayload = async (payloadOverride = {}) => {
    if (!profile?.session_id) return;

    setIsSubmittingFollowUp(true);
    setErrorMessage(null);

    const currentField = nextAction?.field;
    const payload = {
      session_id: profile.session_id,
      field: currentField,
      language_code: selectedLanguage,
      answers: {},
      ...payloadOverride,
    };

    if (payloadOverride.text && currentField) {
      payload.answers[currentField] = payloadOverride.text;
    }

    try {
      const updatedResponse = await apiService.intake.continueIntake(payload);
      setSessionResponse(updatedResponse);
      setFollowUpAnswer('');
    } catch (err) {
      console.error('[INTAKE → FOLLOW-UP SUBMIT]', err);
      const displayMsg = getDisplayError(err, 'Could not update profile. Please try again.');
      setErrorMessage(displayMsg);
    } finally {
      setIsSubmittingFollowUp(false);
    }
  };

  const handleFollowUpSubmit = (e) => {
    e?.preventDefault();
    if (!followUpAnswer || !followUpAnswer.trim()) return;
    submitFollowUpPayload({ text: followUpAnswer.trim() });
  };

  // GPS Location Request Handler with Reverse Geocoding
  const handleRequestGPS = () => {
    if (!navigator.geolocation) {
      setErrorMessage('Geolocation is not supported by your browser.');
      return;
    }

    setGpsLoading(true);
    setErrorMessage(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const coords = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          };
          setGpsData(coords);

          // Reverse geocode coordinates to human-readable Indian location
          const resolved = await reverseGeocodeCoords(coords.latitude, coords.longitude);
          const resolvedLocationName = resolved?.resolvedName || 'Location coordinates captured';

          setGpsLoading(false);

          // Submit resolved human-readable address & GPS coordinates to session
          await submitFollowUpPayload({
            gps_location: coords,
            answers: {
              proposed_location: resolvedLocationName,
              location: resolvedLocationName,
              location_details: resolved?.details || null,
            },
          });
        } catch (geoErr) {
          console.warn('[GPS RESOLUTION ERROR]', geoErr);
          setGpsLoading(false);
          await submitFollowUpPayload({
            gps_location: {
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
            },
            answers: {
              proposed_location: 'Location coordinates captured',
              location: 'Location coordinates captured',
            },
          });
        }
      },
      (error) => {
        console.warn('Geolocation error:', error);
        setGpsLoading(false);
        setErrorMessage('Location permission was denied. Please enter your village, town or district instead.');
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  };

  // Inline Profile Edit Handlers
  const handleStartEdit = (fieldKey, currentValue) => {
    setEditingField(fieldKey);
    setEditValue(currentValue || '');
  };

  const handleSaveEdit = async () => {
    if (!editingField || !profile?.session_id) return;
    
    const answers = {};
    if (editingField === 'available_capital') {
      answers.available_capital = editValue;
    } else if (editingField === 'proposed_location') {
      answers.proposed_location = editValue;
    } else if (editingField === 'entrepreneur_skills') {
      answers.entrepreneur_skills = editValue;
    } else if (editingField === 'intent') {
      answers.intent = editValue;
    } else if (editingField === 'business_concept') {
      answers.business_concept = editValue;
    }

    try {
      const updatedResponse = await apiService.intake.continueIntake({
        session_id: profile.session_id,
        field: editingField,
        language_code: selectedLanguage,
        answers,
      });
      setSessionResponse(updatedResponse);
      setEditingField(null);
    } catch (err) {
      console.error('[INTAKE → INLINE EDIT]', err);
      const displayMsg = getDisplayError(err, 'Could not update field. Please try again.');
      setErrorMessage(displayMsg);
    }
  };

  const handleReset = () => {
    setSessionResponse(null);
    setTextInput('');
    setVoiceTranscript('');
    setVoiceStatus('idle');
    setErrorMessage(null);
    setFollowUpAnswer('');
    setGpsData(null);
    setEditingField(null);
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  };

  const formatCurrency = (val, curr = 'INR') => {
    if (val === null || val === undefined || isNaN(val)) return 'Not specified';
    try {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: curr || 'INR',
        maximumFractionDigits: 0,
      }).format(val);
    } catch {
      return `₹${Number(val).toLocaleString('en-IN')}`;
    }
  };

  return (
    <div className="relative min-h-screen">
      {/* Subtle Animated Topographic Contour Background */}

      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-8">
        {/* Agentic Workflow Thread */}
        <AgenticWorkflowThread currentStepNumber={1} className="mb-2" />

        {/* Language Selector Toolbar */}
        <div className="flex items-center justify-between flex-wrap gap-3 pt-1">
          <div className="flex items-center gap-2">
            <Globe2 className="w-4 h-4 text-[#7A563E]" />
            <span className="text-xs font-bold text-[#7A563E]">Language / भाषा:</span>
          </div>

          <div className="inline-flex p-1 rounded-full bg-[#EFE8DE] border border-[#D6CDBC]/70 shadow-2xs">
            {SUPPORTED_LANGUAGES.map((lang) => {
              const isSelected = selectedLanguage === lang.code;
              return (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => {
                    setSelectedLanguage(lang.code);
                    if (profile?.session_id) {
                      // Update language on active session
                      apiService.intake.continueIntake({
                        session_id: profile.session_id,
                        language_code: lang.code,
                      }).then(setSessionResponse).catch(console.warn);
                    }
                  }}
                  className={`px-3.5 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[#7A563E] text-[#FAF4E8] shadow-sm font-bold'
                      : 'text-[#6F746E] hover:text-[#26332F] bg-transparent'
                  }`}
                >
                  {lang.label === 'Auto Detect' ? 'Auto Detect' : lang.native}
                </button>
              );
            })}
          </div>
        </div>

        {/* Header Banner */}
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <Badge variant="brown" className="mb-2">
            <Sparkles className="w-3 h-3 mr-1" /> {t.badge}
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
            {t.title}
          </h1>
          <p className="text-sm text-[#57534E]">
            {t.subtitle}
          </p>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3 animate-fadeIn">
            <AlertCircle className="w-4 h-4 text-rose-600 mt-0.5 shrink-0" />
            <div className="flex-grow font-medium">
              {typeof errorMessage === 'string' ? errorMessage : getDisplayError(errorMessage)}
            </div>
            <button onClick={() => setErrorMessage(null)} className="text-rose-600 font-bold text-sm">×</button>
          </div>
        )}

        {/* Initial Intake Section */}
        {!profile ? (
          <div className="rounded-3xl p-6 sm:p-8 space-y-6 bg-[#F1E4CC] border border-[#7A563E]/20 shadow-sm">
            {/* User Guidance Card */}
            <div className="p-4 sm:p-5 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/15 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#C2410C] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" />
                {t.guidanceHeading}
              </h3>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#57534E]">
                {t.guidancePoints.map((point, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#EA580C] shrink-0" />
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Input Mode Tabs */}
            <div className="flex items-center justify-center">
              <div className="inline-flex p-1 rounded-2xl bg-[#E8DCC7] border border-[#7A563E]/20">
                <button
                  type="button"
                  onClick={() => { setActiveTab('text'); setErrorMessage(null); }}
                  className={`flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-bold transition-all ${
                    activeTab === 'text'
                      ? 'bg-[#FAF2E3] text-[#1C1917] shadow-2xs font-bold'
                      : 'text-[#7A563E]/80 hover:text-[#1C1917]'
                  }`}
                >
                  <Globe2 className="w-4 h-4 text-[#EA580C]" />
                  <span>{t.textTab}</span>
                </button>
                <button
                  type="button"
                  onClick={() => { setActiveTab('voice'); setErrorMessage(null); }}
                  className={`flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-bold transition-all ${
                    activeTab === 'voice'
                      ? 'bg-[#FAF2E3] text-[#1C1917] shadow-2xs font-bold'
                      : 'text-[#7A563E]/80 hover:text-[#1C1917]'
                  }`}
                >
                  <Mic className="w-4 h-4 text-[#EA580C]" />
                  <span>{t.voiceTab}</span>
                </button>
              </div>
            </div>

            {/* Tab 1: Text Input Mode */}
            {activeTab === 'text' && (
              <div className="space-y-5">
                <div className="space-y-2">
                  <textarea
                    rows={4}
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder={t.textPlaceholder}
                    className="w-full bg-[#FAF2E3] border border-[#7A563E]/20 rounded-2xl p-4 text-sm text-[#1C1917] placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-[#7A563E]/30 focus:border-[#7A563E] resize-none transition-all leading-relaxed"
                  />
                </div>

                {/* Quick Examples Pills */}
                <div className="space-y-2">
                  <span className="text-[11px] font-semibold text-[#78716C]">{t.quickExamples}</span>
                  <div className="flex flex-wrap gap-2">
                    {samplePrompts.map((sample, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setTextInput(sample.text);
                          setSelectedLanguage(sample.lang);
                          handleTextSubmit(sample.text, sample.lang);
                        }}
                        className="text-left px-3 py-1.5 rounded-xl bg-[#FAF2E3] hover:bg-[#FAF2E3]/90 border border-[#7A563E]/20 hover:border-[#7A563E]/40 text-xs text-[#44403C] transition-all"
                      >
                        <span className="font-semibold text-[#EA580C]">{sample.label}:</span>{' '}
                        <span className="text-stone-600 truncate max-w-[200px] inline-block align-bottom">{sample.text}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <Button
                    size="lg"
                    icon={ArrowRight}
                    onClick={() => handleTextSubmit()}
                    disabled={isProcessing || !textInput.trim()}
                    className="w-full sm:w-auto px-8 py-3"
                  >
                    {isProcessing ? t.processingText : t.continueBtn}
                  </Button>
                </div>
              </div>
            )}

            {/* Tab 2: Voice Input Mode */}
            {activeTab === 'voice' && (
              <div className="space-y-6 py-4 text-center">
                <div className="max-w-md mx-auto space-y-4">
                  {/* Microphone Action Button */}
                  <div className="relative flex items-center justify-center py-2">
                    {isRecording && (
                      <div className="absolute w-36 h-36 rounded-full bg-orange-500/25 animate-ping pointer-events-none" />
                    )}
                    <button
                      type="button"
                      onClick={isRecording ? stopRecording : startRecording}
                      disabled={isProcessing}
                      className={`relative w-28 h-28 rounded-full flex items-center justify-center shadow-xl transition-all duration-300 ${
                        isRecording
                          ? 'bg-rose-600 text-white scale-105 shadow-rose-600/30 ring-4 ring-rose-300'
                          : voiceStatus === 'transcribing'
                          ? 'bg-amber-500 text-white animate-pulse'
                          : 'bg-gradient-to-br from-[#EA580C] to-[#C2410C] text-white hover:scale-105 shadow-orange-600/30'
                      }`}
                    >
                      {isRecording ? (
                        <Square className="w-10 h-10 fill-current" />
                      ) : (
                        <Mic className="w-12 h-12" />
                      )}
                    </button>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-[#1C1917]">
                      {isRecording
                        ? `${t.listening} (${recordingTime}s)`
                        : voiceStatus === 'transcribing'
                        ? t.processingSpeech
                        : t.readyToListen}
                    </h3>
                    <p className="text-xs text-[#78716C] mt-1">
                      {isRecording
                        ? 'Tap the red button when finished speaking.'
                        : 'Language: ' + (SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage)?.native || 'English')}
                    </p>
                  </div>

                  {/* Transcript Review Box */}
                  {voiceTranscript && (
                    <div className="text-left p-4 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/20 space-y-3 animate-fadeIn">
                      <div className="flex items-center justify-between text-xs text-[#78716C] font-semibold">
                        <span>{t.transcriptReceived}</span>
                        <Badge variant="saffron">Voice Input</Badge>
                      </div>
                      <textarea
                        rows={3}
                        value={voiceTranscript}
                        onChange={(e) => setVoiceTranscript(e.target.value)}
                        className="w-full bg-[#FAF2E3] border border-[#7A563E]/25 rounded-xl p-3 text-sm text-[#1C1917] focus:outline-none focus:ring-2 focus:ring-[#7A563E]/30"
                      />
                      <div className="flex gap-2 justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setVoiceTranscript('');
                            setVoiceStatus('idle');
                          }}
                        >
                          {t.reRecord}
                        </Button>
                        <Button
                          size="sm"
                          icon={ArrowRight}
                          onClick={() => handleTextSubmit(voiceTranscript)}
                          disabled={isProcessing || !voiceTranscript.trim()}
                        >
                          {t.confirmAndAnalyze}
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Structured Understanding & Stage 1 Review Screen */
          <div className="space-y-8 animate-fadeIn">
            {/* Overview Header */}
            <div className="rounded-3xl p-6 sm:p-8 space-y-6 bg-[#F1E4CC] border border-[#7A563E]/20 shadow-sm">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#7A563E]/15 pb-4">
                <div>
                  <Badge variant="brown" className="mb-1">Stage 1 Profile</Badge>
                  <h2 className="text-2xl font-bold tracking-tight text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <CheckCircle2 className="w-6 h-6 text-emerald-600" />
                    Understood Business Profile
                  </h2>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  icon={RotateCcw}
                  onClick={handleReset}
                >
                  {t.startOver}
                </Button>
              </div>

              {/* 6 Dimension Profile Grid with Inline Editing */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {/* 1. Business Concept */}
                <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/15 space-y-2 relative group">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                      <Briefcase className="w-3.5 h-3.5 text-[#EA580C]" />
                      Business Concept
                    </span>
                    <button
                      onClick={() => handleStartEdit('business_concept', profile.business_concept)}
                      className="text-[11px] text-[#EA580C] hover:underline font-semibold flex items-center gap-0.5"
                    >
                      <Edit3 className="w-3 h-3" />
                      {t.edit}
                    </button>
                  </div>
                  {editingField === 'business_concept' ? (
                    <div className="space-y-2 pt-1">
                      <input
                        type="text"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-orange-500 bg-white"
                      />
                      <div className="flex gap-1 justify-end">
                        <button onClick={() => setEditingField(null)} className="px-2 py-1 text-[10px] text-stone-500 font-bold">{t.cancel}</button>
                        <button onClick={handleSaveEdit} className="px-2 py-1 text-[10px] bg-[#EA580C] text-white rounded font-bold">{t.save}</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-base font-bold text-[#1C1917]">
                        {profile.business_concept || <span className="text-amber-600 italic">Pending answer</span>}
                      </p>
                      {profile.business_category_hint && (
                        <p className="text-xs text-[#78716C]">{profile.business_category_hint}</p>
                      )}
                    </>
                  )}
                </div>

                {/* 2. Intent & Stage */}
                <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/15 space-y-2 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-[#EA580C]" />
                      Intent & Stage
                    </span>
                    <button
                      onClick={() => handleStartEdit('intent', profile.intent)}
                      className="text-[11px] text-[#EA580C] hover:underline font-semibold flex items-center gap-0.5"
                    >
                      <Edit3 className="w-3 h-3" />
                      {t.edit}
                    </button>
                  </div>
                  {editingField === 'intent' ? (
                    <div className="space-y-2 pt-1">
                      <select
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none bg-white"
                      >
                        <option value="start_business">Start New Business</option>
                        <option value="expand_business">Expand Existing Business</option>
                      </select>
                      <div className="flex gap-1 justify-end">
                        <button onClick={() => setEditingField(null)} className="px-2 py-1 text-[10px] text-stone-500 font-bold">{t.cancel}</button>
                        <button onClick={handleSaveEdit} className="px-2 py-1 text-[10px] bg-[#EA580C] text-white rounded font-bold">{t.save}</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm font-bold text-[#1C1917] capitalize">
                        {profile.intent === 'expand_business' ? 'Expand Existing Business' : 'Start New Business'}
                      </p>
                      <span className="inline-block text-[11px] px-2 py-0.5 rounded bg-[#FAF2E3] text-[#C2410C] font-semibold capitalize border border-[#7A563E]/10">
                        Stage: {profile.business_stage || 'Planning'}
                      </span>
                    </>
                  )}
                </div>

                {/* 3. Available Capital */}
                <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/15 space-y-2 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                      <IndianRupee className="w-3.5 h-3.5 text-[#EA580C]" />
                      Available Capital
                    </span>
                    <button
                      onClick={() => handleStartEdit('available_capital', profile.available_capital)}
                      className="text-[11px] text-[#EA580C] hover:underline font-semibold flex items-center gap-0.5"
                    >
                      <Edit3 className="w-3 h-3" />
                      {t.edit}
                    </button>
                  </div>
                  {editingField === 'available_capital' ? (
                    <div className="space-y-2 pt-1">
                      <input
                        type="text"
                        placeholder="e.g. 200000 or 2 lakh"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-orange-500 bg-white"
                      />
                      <div className="flex gap-1 justify-end">
                        <button onClick={() => setEditingField(null)} className="px-2 py-1 text-[10px] text-stone-500 font-bold">{t.cancel}</button>
                        <button onClick={handleSaveEdit} className="px-2 py-1 text-[10px] bg-[#EA580C] text-white rounded font-bold">{t.save}</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-base font-bold text-[#1C1917]">
                        {profile.available_capital !== null && profile.available_capital !== undefined ? (
                          formatCurrency(profile.available_capital, profile.capital_currency)
                        ) : (
                          <span className="text-amber-600 italic">Pending clarification</span>
                        )}
                      </p>
                      <div className="flex items-center gap-1.5 text-[11px] text-stone-500">
                        <span>Currency: {profile.capital_currency || 'INR'}</span>
                        {profile.available_capital !== null && (
                          <span className="text-[#7A563E] bg-[#FAF2E3] border border-[#7A563E]/25 px-2 py-0.5 rounded-md font-semibold text-[10px]">
                            {profile.confidence?.available_capital ? `${Math.round(profile.confidence.available_capital * 100)}% confidence` : 'Canonical'}
                          </span>
                        )}
                      </div>
                    </>
                  )}
                </div>

                {/* 4. Business Location */}
                <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/15 space-y-2 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-[#EA580C]" />
                      Business Location
                    </span>
                    <button
                      onClick={() => handleStartEdit('proposed_location', typeof profile.proposed_location === 'string' ? profile.proposed_location : (profile.proposed_location?.district || profile.proposed_location?.name))}
                      className="text-[11px] text-[#EA580C] hover:underline font-semibold flex items-center gap-0.5"
                    >
                      <Edit3 className="w-3 h-3" />
                      {t.edit}
                    </button>
                  </div>
                  {editingField === 'proposed_location' ? (
                    <div className="space-y-2 pt-1">
                      <input
                        type="text"
                        placeholder="e.g. Mandya, Karnataka"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-orange-500 bg-white"
                      />
                      <div className="flex gap-1 justify-end">
                        <button onClick={() => setEditingField(null)} className="px-2 py-1 text-[10px] text-stone-500 font-bold">{t.cancel}</button>
                        <button onClick={handleSaveEdit} className="px-2 py-1 text-[10px] bg-[#EA580C] text-white rounded font-bold">{t.save}</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm font-bold text-[#1C1917]">
                        {typeof profile.proposed_location === 'string'
                          ? profile.proposed_location
                          : profile.proposed_location?.district 
                            ? `${profile.proposed_location.district}${profile.proposed_location.state ? ', ' + profile.proposed_location.state : ''}`
                            : profile.proposed_location?.name || <span className="text-amber-600 italic">Pending clarification</span>}
                      </p>
                      <span className="text-[11px] text-stone-500 flex items-center gap-1">
                        Source: {profile.proposed_location?.source === 'gps' ? t.sourceGPS : t.sourceUser}
                      </span>
                    </>
                  )}
                </div>

                {/* 5. Detected Language */}
                <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/15 space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                    <Globe2 className="w-3.5 h-3.5 text-[#EA580C]" />
                    Language
                  </span>
                  <p className="text-sm font-bold text-[#1C1917]">
                    {profile.detected_language || 'English'}
                  </p>
                  <span className="text-[11px] text-stone-500 uppercase font-mono">
                    Code: {profile.language_code || 'en'}
                  </span>
                </div>

                {/* 6. Entrepreneur Skills */}
                <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/15 space-y-2 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-[#EA580C]" />
                      Entrepreneur Skills
                    </span>
                    <button
                      onClick={() => handleStartEdit('entrepreneur_skills', profile.entrepreneur_skills?.join(', '))}
                      className="text-[11px] text-[#EA580C] hover:underline font-semibold flex items-center gap-0.5"
                    >
                      <Edit3 className="w-3 h-3" />
                      {t.edit}
                    </button>
                  </div>
                  {editingField === 'entrepreneur_skills' ? (
                    <div className="space-y-2 pt-1">
                      <input
                        type="text"
                        placeholder="e.g. Farming, Cattle rearing or No experience"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-orange-500 bg-white"
                      />
                      <div className="flex gap-1 justify-end">
                        <button onClick={() => setEditingField(null)} className="px-2 py-1 text-[10px] text-stone-500 font-bold">{t.cancel}</button>
                        <button onClick={handleSaveEdit} className="px-2 py-1 text-[10px] bg-[#EA580C] text-white rounded font-bold">{t.save}</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-xs font-semibold text-[#1C1917]">
                        {profile.skills_status === 'no_experience'
                          ? 'No prior experience (Fresh entrepreneur)'
                          : profile.entrepreneur_skills?.length > 0
                          ? profile.entrepreneur_skills.join(', ')
                          : <span className="text-amber-600 italic">Pending clarification</span>}
                      </p>
                      <span className="text-[11px] text-stone-500">
                        Status: {profile.skills_status === 'no_experience' ? 'Fresh Entrepreneur' : profile.skills_status === 'collected' ? 'Skills Logged' : 'Clarification needed'}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Clarification Section: Only active when Stage 1 has missing fields */}
            {nextAction?.type === 'clarification' && (nextAction.question || nextAction.field === 'proposed_location') ? (
              <div className="rounded-3xl p-6 sm:p-8 border border-[#D97706]/40 bg-[#FAF0DC] space-y-5 shadow-sm animate-fadeIn">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="brown">{t.clarificationTitle}</Badge>
                  </div>

                  {/* Browser TTS Button */}
                  <button
                    type="button"
                    onClick={() =>
                      handleToggleTTS(
                        nextAction.field === 'proposed_location'
                          ? 'Where do you plan to run this business? You can enter your village, town, taluk, district, or city.'
                          : nextAction.question
                      )
                    }
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                      isSpeaking
                        ? 'bg-rose-100 text-rose-800 border-rose-300'
                        : 'bg-[#FAF2E3] text-[#7A563E] border-[#7A563E]/20 hover:bg-[#FAF2E3]/90 shadow-2xs'
                    }`}
                  >
                    {isSpeaking ? (
                      <>
                        <VolumeX className="w-4 h-4 text-rose-600" />
                        <span>{t.stopSpeaking}</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-4 h-4 text-[#EA580C]" />
                        <span>{t.listenQuestion}</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Question & Guidance */}
                <div className="space-y-1.5">
                  <h3 className="text-lg sm:text-xl font-bold text-[#1C1917] font-['Outfit'] leading-snug">
                    {nextAction.field === 'proposed_location'
                      ? 'Where do you plan to run this business?'
                      : nextAction.question}
                  </h3>
                  <p className="text-xs sm:text-sm font-medium text-[#57534E]">
                    {nextAction.field === 'proposed_location'
                      ? 'You can enter your village, town, taluk, district, or city.'
                      : nextAction.helper_text}
                  </p>
                </div>

                {/* Special Case: Intent Options */}
                {nextAction.field === 'intent' && nextAction.options && (
                  <div className="flex flex-wrap gap-3 pt-1">
                    {nextAction.options.map((opt, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => submitFollowUpPayload({ answers: { intent: opt.value } })}
                        disabled={isSubmittingFollowUp}
                        className="px-5 py-2.5 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/30 hover:border-[#EA580C] text-sm font-bold text-[#1C1917] hover:bg-[#FAF2E3]/90 transition-all shadow-2xs flex items-center gap-2"
                      >
                        <Sparkles className="w-4 h-4 text-[#EA580C]" />
                        <span>{opt.label}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Special Case: GPS Fallback Button for Location */}
                {nextAction.field === 'proposed_location' && (
                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={handleRequestGPS}
                      disabled={gpsLoading || isSubmittingFollowUp}
                      className="inline-flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/30 hover:border-[#EA580C] text-xs font-bold text-[#1C1917] hover:bg-[#FAF2E3]/90 shadow-2xs transition-all"
                    >
                      <Compass className={`w-4 h-4 text-[#EA580C] ${gpsLoading ? 'animate-spin' : ''}`} />
                      <span>{gpsLoading ? t.gpsLocating : t.useCurrentLocation}</span>
                    </button>
                  </div>
                )}

                {/* Special Case: "No Experience" Button for Skills */}
                {nextAction.field === 'entrepreneur_skills' && (
                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={() => submitFollowUpPayload({ answers: { skills_status: 'no_experience', skills: 'no experience' } })}
                      disabled={isSubmittingFollowUp}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-[#E8DCC7] hover:bg-[#D6CDBC] text-xs font-bold text-stone-700 transition-all"
                    >
                      <X className="w-3.5 h-3.5 text-stone-500" />
                      <span>{t.noExperienceBtn}</span>
                    </button>
                  </div>
                )}

                {/* Answer Mode Switcher: Type Answer OR Speak Answer */}
                <div className="space-y-3 pt-2">
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setFollowUpTab('text')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                        followUpTab === 'text'
                          ? 'bg-[#7A563E] text-[#FAF4E8]'
                          : 'bg-[#FAF2E3] text-[#7A563E] border border-[#7A563E]/20 hover:bg-[#FAF2E3]/80'
                      }`}
                    >
                      {t.typeAnswerTab}
                    </button>
                    <button
                      type="button"
                      onClick={() => setFollowUpTab('voice')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                        followUpTab === 'voice'
                          ? 'bg-[#EA580C] text-white'
                          : 'bg-[#FAF2E3] text-[#7A563E] border border-[#7A563E]/20 hover:bg-[#FAF2E3]/80'
                      }`}
                    >
                      <Mic className="w-3.5 h-3.5" />
                      <span>{t.speakAnswerTab}</span>
                    </button>
                  </div>

                  {/* Mode A: Type Follow-up Answer */}
                  {followUpTab === 'text' && (
                    <form onSubmit={handleFollowUpSubmit} className="flex flex-col sm:flex-row gap-3">
                      <input
                        type="text"
                        value={followUpAnswer}
                        onChange={(e) => setFollowUpAnswer(e.target.value)}
                        placeholder={nextAction.helper_text || 'Type your answer here...'}
                        className="flex-grow bg-[#FAF2E3] border border-[#7A563E]/25 rounded-xl px-4 py-3 text-sm text-[#1C1917] focus:outline-none focus:ring-2 focus:ring-[#7A563E]/30 focus:border-[#7A563E]"
                      />
                      <Button
                        type="submit"
                        size="md"
                        icon={Send}
                        disabled={isSubmittingFollowUp || !followUpAnswer.trim()}
                        className="px-6"
                      >
                        {isSubmittingFollowUp ? 'Updating...' : t.submitAnswer}
                      </Button>
                    </form>
                  )}

                  {/* Mode B: Speak Follow-up Answer */}
                  {followUpTab === 'voice' && (
                    <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#7A563E]/20 space-y-3">
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={isFollowUpRecording ? stopFollowUpRecording : startFollowUpRecording}
                          disabled={isSubmittingFollowUp}
                          className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                            isFollowUpRecording
                              ? 'bg-rose-600 text-white animate-pulse'
                              : 'bg-[#EA580C] text-white hover:scale-105'
                          }`}
                        >
                          {isFollowUpRecording ? <Square className="w-5 h-5 fill-current" /> : <Mic className="w-6 h-6" />}
                        </button>
                        <span className="text-xs font-semibold text-[#1C1917]">
                          {isFollowUpRecording
                            ? `Recording follow-up... (${followUpRecordingTime}s)`
                            : 'Tap microphone to speak your answer'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* All Stage 1 Conditions Satisfied Banner */
              <div className="rounded-3xl p-6 sm:p-8 bg-[#F1E4CC] border border-[#7A563E]/20 space-y-4 text-center animate-fadeIn shadow-sm">
                <div className="w-14 h-14 rounded-full bg-[#FAF2E3] text-[#006B59] border border-[#7A563E]/15 flex items-center justify-center mx-auto shadow-inner">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-2xl font-bold text-[#1C1917] font-['Outfit']">
                    {t.stage1CompleteTitle}
                  </h3>
                  <p className="text-xs sm:text-sm text-[#57534E] max-w-lg mx-auto leading-relaxed">
                    {t.stage1CompleteDesc}
                  </p>
                </div>

                <div className="pt-3 flex justify-center">
                  <button
                    type="button"
                    onClick={() => {
                      const sid = sessionResponse?.session_id || sessionResponse?.profile?.session_id || '';
                      console.log('[STAGE 1 → STAGE 2] Proceeding with session_id:', sid);
                      markStageComplete(1, 2);
                      navigate(`/classification${sid ? `?session_id=${encodeURIComponent(sid)}` : ''}`);
                    }}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#EA580C] hover:bg-[#C2410C] text-white text-sm font-bold shadow-lg shadow-orange-900/20 transition-all hover:scale-105 cursor-pointer"
                  >
                    <span>Proceed to Stage 2: Business Classification</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntakePage;
