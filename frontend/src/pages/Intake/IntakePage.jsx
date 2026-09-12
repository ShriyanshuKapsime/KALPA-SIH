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
import ContourBackground from '../../components/ui/ContourBackground';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';

// Language Options (Display Labels separated from Sarvam API values)
const SUPPORTED_LANGUAGES = [
  { code: 'auto', appCode: 'unknown', sarvamCode: 'unknown', label: 'Auto Detect', native: 'ಸ್ವಯಂಚಾಲಿತ / Auto' },
  { code: 'en', appCode: 'en', sarvamCode: 'en-IN', label: 'English', native: 'English' },
  { code: 'kn', appCode: 'kn', sarvamCode: 'kn-IN', label: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'hi', appCode: 'hi', sarvamCode: 'hi-IN', label: 'Hindi', native: 'हिन्दी' },
];

// Localized UI Texts
const UI_STRINGS = {
  auto: {
    badge: 'Step 1 of KALPA Journey',
    title: 'Tell Us About Your Business Idea',
    subtitle: 'Speak naturally in any Indian language or type in your preferred language.',
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
    listening: 'Listening... Speak in English, Hindi, or Kannada',
    processingSpeech: 'Processing speech with Sarvam STT...',
    transcriptReceived: 'Transcript received. You can review or edit below:',
    confirmAndAnalyze: 'Confirm & Understand Business Idea',
    reRecord: 'Re-record',
    clarificationTitle: 'Clarification Needed',
    typeAnswerTab: 'Type Answer',
    speakAnswerTab: 'Speak Answer',
    submitAnswer: 'Submit Answer',
    listenQuestion: 'Listen',
    stopSpeaking: 'Stop Speaking',
    useCurrentLocation: 'Use Current Location (GPS)',
    gpsLocating: 'Fetching GPS location...',
    gpsSuccess: 'Device GPS Location detected',
    noExperienceBtn: "I don't have experience",
    stage1CompleteTitle: 'Stage 1 Intake & Extraction Complete!',
    stage1CompleteDesc: 'Your business profile, capital, location, and skills have been structured and verified.',
    readyForPhase2: 'Ready for Stage 2: Business Classification & NIC Mapping',
    startOver: 'Start Over',
    edit: 'Edit',
    save: 'Save',
    cancel: 'Cancel',
    sourceUser: 'Provided by you',
    sourceGPS: 'Device GPS'
  },
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
    listening: 'Listening... Speak clearly',
    processingSpeech: 'Processing speech with Sarvam STT...',
    transcriptReceived: 'Transcript received. You can review or edit below:',
    confirmAndAnalyze: 'Confirm & Understand Business Idea',
    reRecord: 'Re-record',
    clarificationTitle: 'Clarification Needed',
    typeAnswerTab: 'Type Answer',
    speakAnswerTab: 'Speak Answer',
    submitAnswer: 'Submit Answer',
    listenQuestion: 'Listen',
    stopSpeaking: 'Stop Speaking',
    useCurrentLocation: 'Use Current Location (GPS)',
    gpsLocating: 'Fetching GPS location...',
    gpsSuccess: 'Device GPS Location detected',
    noExperienceBtn: "I don't have experience",
    stage1CompleteTitle: 'Stage 1 Intake & Extraction Complete!',
    stage1CompleteDesc: 'Your business profile, capital, location, and skills have been structured and verified.',
    readyForPhase2: 'Ready for Stage 2: Business Classification & NIC Mapping',
    startOver: 'Start Over',
    edit: 'Edit',
    save: 'Save',
    cancel: 'Cancel',
    sourceUser: 'Provided by you',
    sourceGPS: 'Device GPS'
  },
  kn: {
    badge: 'ಕಲ್ಪ ಪ್ರಯಾಣದ ಹಂತ 1',
    title: 'ನಿಮ್ಮ ವ್ಯವಹಾರದ ಕಲ್ಪನೆಯನ್ನು ನಮಗೆ ತಿಳಿಸಿ',
    subtitle: 'ನಿಮ್ಮ ಮಾತೃಭಾಷೆಯಲ್ಲಿ ಸ್ವಾಭಾವಿಕವಾಗಿ ಮಾತನಾಡಿ ಅಥವಾ ನಿಮ್ಮ ಆಯ್ಕೆಯ ಭಾಷೆಯಲ್ಲಿ ಬರೆಯಿರಿ.',
    guidanceHeading: 'ನಿಮ್ಮ ವ್ಯಾಪಾರದ ಬಗ್ಗೆ ಮುಕ್ತವಾಗಿ ತಿಳಿಸಿ:',
    guidancePoints: [
      'ನೀವು ಯಾವ ವ್ಯವಹಾರವನ್ನು ಪ್ರಾರಂಭಿಸಲು ಅಥವಾ ವಿಸ್ತರಿಸಲು ಬಯಸುತ್ತೀರಿ',
      'ನೀವು ಎಷ್ಟು ಬಂಡವಾಳ ಹೂಡಿಕೆ ಮಾಡಬಹುದು',
      'ವ್ಯವಹಾರವನ್ನು ಎಲ್ಲಿ ನಡೆಸಲು ಯೋಜಿಸುತ್ತಿದ್ದೀರಿ (ಗ್ರಾಮ, ತಾಲೂಕು, ಜಿಲ್ಲೆ)',
      'ನಿಮ್ಮಲ್ಲಿರುವ ಸಂಬಂಧಿತ ಅನುಭವ ಅಥವಾ ಕೌಶಲ್ಯಗಳು'
    ],
    quickExamples: 'ತ್ವರಿತ ಉದಾಹರಣೆಗಳು:',
    textTab: 'ಬರೆದು ತಿಳಿಸಿ',
    voiceTab: 'ಮಾತನಾಡಿ ತಿಳಿಸಿ',
    textPlaceholder: 'ಉದಾ: ನಾನು ಮಂಡ್ಯದಲ್ಲಿ ₹2 ಲಕ್ಷ ಬಂಡವಾಳದೊಂದಿಗೆ ಡೈರಿ ಫಾರ್ಮ್ ಪ್ರಾರಂಭಿಸಲು ಬಯಸುತ್ತೇನೆ. ನನಗೆ ಹೈನುಗಾರಿಕೆ ಅನುಭವವಿದೆ.',
    continueBtn: 'ಮುಂದುವರಿಯಿರಿ',
    processingText: 'ನಿಮ್ಮ ವ್ಯವಹಾರ ಕಲ್ಪನೆಯನ್ನು ಗ್ರಹಿಸಲಾಗುತ್ತಿದೆ...',
    readyToListen: 'ಮಾತನಾಡಲು ಸಿದ್ಧ. ಮೈಕ್ ಮೇಲೆ ಸ್ಪರ್ಶಿಸಿ',
    listening: 'ಕೇಳಿಸಿಕೊಳ್ಳುತ್ತಿದ್ದೇವೆ... ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ',
    processingSpeech: 'ಧ್ವನಿಯನ್ನು ಪಠ್ಯಕ್ಕೆ ಪರಿವರ್ತಿಸಲಾಗುತ್ತಿದೆ...',
    transcriptReceived: 'ಧ್ವನಿ ಸ್ವೀಕರಿಸಲಾಗಿದೆ. ಪರಿಶೀಲಿಸಿ ಅಥವಾ ತಿದ್ದಿ:',
    confirmAndAnalyze: 'ಖಚಿತಪಡಿಸಿ ಮತ್ತು ವಿಶ್ಲೇಷಿಸಿ',
    reRecord: 'ಮತ್ತೊಮ್ಮೆ ಧ್ವನಿಮುದ್ರಿಸಿ',
    clarificationTitle: 'ಹೆಚ್ಚುವರಿ ಮಾಹಿತಿ ಅಗತ್ಯವಿದೆ',
    typeAnswerTab: 'ಬರೆದು ಉತ್ತರಿಸಿ',
    speakAnswerTab: 'ಮಾತನಾಡಿ ಉತ್ತರಿಸಿ',
    submitAnswer: 'ಉತ್ತರ ಸಲ್ಲಿಸಿ',
    listenQuestion: 'ಪ್ರಶ್ನೆ ಆಲಿಸಿ',
    stopSpeaking: 'ನಿಲ್ಲಿಸಿ',
    useCurrentLocation: 'ಪ್ರಸ್ತುತ ಸ್ಥಳ ಬಳಸಿ (GPS)',
    gpsLocating: 'GPS ಸ್ಥಳ ಪಡೆಯಲಾಗುತ್ತಿದೆ...',
    gpsSuccess: 'ಸಾಧನದ GPS ಸ್ಥಳ ಗುರುತಿಸಲಾಗಿದೆ',
    noExperienceBtn: 'ನನಗೆ ಅನುಭವವಿಲ್ಲ',
    stage1CompleteTitle: 'ಹಂತ 1 - ಮಾಹಿತಿ ಸಂಗ್ರಹ ಪೂರ್ಣಗೊಂಡಿದೆ!',
    stage1CompleteDesc: 'ನಿಮ್ಮ ವ್ಯಾಪಾರ ಪರಿಕಲ್ಪನೆ, ಬಂಡವಾಳ, ಸ್ಥಳ ಮತ್ತು ಕೌಶಲ್ಯಗಳನ್ನು ಯಶಸ್ವಿಯಾಗಿ ರಚಿಸಲಾಗಿದೆ.',
    readyForPhase2: 'ಹಂತ 2: ವ್ಯಾಪಾರ ವರ್ಗೀಕರಣಕ್ಕೆ ಸಿದ್ಧವಾಗಿದೆ',
    startOver: 'ಮತ್ತೆ ಪ್ರಾರಂಭಿಸಿ',
    edit: 'ತಿದ್ದಿ',
    save: 'ಉಳಿಸಿ',
    cancel: 'ರದ್ದು',
    sourceUser: 'ನೀವು ನೀಡಿದ ಸ್ಥಳ',
    sourceGPS: 'ಸಾಧನದ GPS'
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
    useCurrentLocation: 'वर्तमान स्थान का उपयोग करें (GPS)',
    gpsLocating: 'GPS स्थान खोजा जा रहा है...',
    gpsSuccess: 'डिवाइस का GPS स्थान मिल गया',
    noExperienceBtn: 'मुझे पूर्व अनुभव नहीं है',
    stage1CompleteTitle: 'चरण 1 - जानकारी निष्कर्षण पूर्ण!',
    stage1CompleteDesc: 'आपकी व्यावसायिक अवधारणा, पूंजी, स्थान और कौशल का सत्यापन हो चुका है।',
    readyForPhase2: 'चरण 2: व्यवसाय वर्गीकरण और NIC मैपिंग के लिए तैयार',
    startOver: 'शुरू से शुरू करें',
    edit: 'बदलें',
    save: 'सहेजें',
    cancel: 'रद्द करें',
    sourceUser: 'आपके द्वारा दिया गया',
    sourceGPS: 'डिवाइस GPS'
  }
};

export const IntakePage = () => {
  const navigate = useNavigate();
  const { updateWorkflowState, markStageComplete } = useWorkflow();
  // Language State: Priority English -> Kannada -> Hindi
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  
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

  // Stage 1 API Response & Profile
  const [sessionResponse, setSessionResponse] = useState(null);
  const profile = sessionResponse?.profile;
  const nextAction = sessionResponse?.next_action;

  // Sync Stage 1 structured result to sessionStorage and central workflow context
  useEffect(() => {
    if (sessionResponse) {
      console.log('[STAGE 1 RESULT]', sessionResponse);
      const sid = sessionResponse.session_id || sessionResponse.profile?.session_id;
      const bName = sessionResponse.profile?.business_idea || sessionResponse.profile?.business_concept;
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

  // Text-To-Speech (TTS) State
  const [isSpeaking, setIsSpeaking] = useState(false);

  // GPS Fallback State
  const [gpsLoading, setGpsLoading] = useState(false);
  const [gpsData, setGpsData] = useState(null);

  // Inline Profile Edit State
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState('');

  const t = UI_STRINGS[selectedLanguage] || UI_STRINGS.en;

  // Sample Prompts for Instant Testing
  const samplePrompts = [
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
      label: 'Saree Shop (English)',
      lang: 'en',
      text: 'I want to open a saree shop in my village with 3 lakh rupees and retail experience.',
    },
    {
      label: 'Expand Grocery (English)',
      lang: 'en',
      text: 'I already run a small grocery shop and want to expand it with 1.5 lakh budget.',
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
    let matchedVoice = null;

    if (selectedLanguage === 'kn') {
      matchedVoice = voices.find((v) => v.lang.startsWith('kn') || v.lang.includes('Kannada'));
    } else if (selectedLanguage === 'hi') {
      matchedVoice = voices.find((v) => v.lang.startsWith('hi') || v.lang.includes('Hindi'));
    } else {
      matchedVoice = voices.find((v) => v.lang === 'en-IN') || voices.find((v) => v.lang.startsWith('en'));
    }

    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }
    utterance.lang = selectedLanguage === 'kn' ? 'kn-IN' : selectedLanguage === 'hi' ? 'hi-IN' : 'en-IN';
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
      setErrorMessage('Microphone access was denied or not available. Please type your business idea below.');
      setVoiceStatus('idle');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setVoiceStatus('transcribing');
    }
  };

  // Upload Voice to Sarvam STT
  const handleVoiceSTT = async (audioBlob) => {
    setIsProcessing(true);
    setVoiceStatus('transcribing');
    setErrorMessage(null);

    const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage) || SUPPORTED_LANGUAGES[0];
    const formData = new FormData();
    formData.append('file', audioBlob, 'intake_recording.webm');
    formData.append('language_code', langConfig.sarvamCode || 'unknown');
    formData.append('selected_language', langConfig.appCode === 'unknown' ? 'en' : langConfig.appCode);

    try {
      const response = await apiService.intake.submitVoice(formData);
      setVoiceTranscript(response.transcript || '');
      setVoiceStatus('received');
      setSessionResponse(response);
    } catch (err) {
      console.error('Voice submission error:', err);
      const errMsg = err.details?.message || err.details?.provider_error || err.message || 'Voice processing is temporarily unavailable. Please try typing your idea.';
      setErrorMessage(errMsg);
      setVoiceStatus('idle');
    } finally {
      setIsProcessing(false);
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
      console.error('Text intake error:', err);
      setErrorMessage(err.message || 'Failed to process business intake. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Follow-Up Voice Recording Handlers
  const startFollowUpRecording = async () => {
    setErrorMessage(null);
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
      setErrorMessage('Microphone access denied. You can type your answer instead.');
      setIsFollowUpRecording(false);
    }
  };

  const stopFollowUpRecording = () => {
    if (followUpMediaRecorderRef.current && isFollowUpRecording) {
      followUpMediaRecorderRef.current.stop();
      setIsFollowUpRecording(false);
    }
  };

  const handleFollowUpVoiceSTT = async (audioBlob) => {
    setIsSubmittingFollowUp(true);
    const langConfig = SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage) || SUPPORTED_LANGUAGES[0];
    const formData = new FormData();
    formData.append('file', audioBlob, 'followup_recording.webm');
    formData.append('language_code', langConfig.sarvamCode || 'unknown');
    formData.append('selected_language', langConfig.appCode === 'unknown' ? 'en' : langConfig.appCode);

    try {
      const response = await apiService.intake.submitVoice(formData);
      if (response.transcript) {
        setFollowUpAnswer(response.transcript);
        // Automatically submit transcribed text to follow up
        await submitFollowUpPayload({ text: response.transcript });
      }
    } catch (err) {
      console.error('Follow-up voice STT error:', err);
      setErrorMessage('Could not process voice answer. Please type your response.');
    } finally {
      setIsSubmittingFollowUp(false);
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
      console.error('Follow-up submit error:', err);
      setErrorMessage('Could not update profile. Please try again.');
    } finally {
      setIsSubmittingFollowUp(false);
    }
  };

  const handleFollowUpSubmit = (e) => {
    e?.preventDefault();
    if (!followUpAnswer || !followUpAnswer.trim()) return;
    submitFollowUpPayload({ text: followUpAnswer.trim() });
  };

  // GPS Fallback Request Handler
  const handleRequestGPS = () => {
    if (!navigator.geolocation) {
      setErrorMessage('Geolocation is not supported by your browser.');
      return;
    }

    setGpsLoading(true);
    setErrorMessage(null);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const coords = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        };
        setGpsData(coords);
        setGpsLoading(false);

        // Submit GPS coordinates to session
        await submitFollowUpPayload({
          gps_location: coords,
          answers: { location: 'Current Location (GPS)' },
        });
      },
      (error) => {
        console.warn('Geolocation error:', error);
        setGpsLoading(false);
        setErrorMessage('Location permission was denied. Please type your village, town or district instead.');
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
      setErrorMessage('Could not update field. Please try again.');
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

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'Not specified';
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
  };

  return (
    <div className="relative min-h-screen">
      {/* Subtle Animated Topographic Contour Background */}
      <ContourBackground />

      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-8">
        {/* Step Progress Tracker */}
        <div className="royal-panel rounded-2xl p-4 sm:p-5 shadow-sm">
          <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1 text-xs">
            <div className="flex items-center gap-2 font-bold text-[#EA580C] shrink-0">
              <span className="w-6 h-6 rounded-full bg-[#EA580C] text-white flex items-center justify-center text-[11px]">
                1
              </span>
              <span>01 Intake & Extraction</span>
            </div>
            <span className="text-stone-300">→</span>
            <div className="flex items-center gap-1 text-stone-400 shrink-0">
              <Lock className="w-3 h-3 text-stone-400" />
              <span>02 Classification (NIC)</span>
            </div>
            <span className="text-stone-300">→</span>
            <div className="flex items-center gap-1 text-stone-400 shrink-0">
              <Lock className="w-3 h-3 text-stone-400" />
              <span>03 Market Intel</span>
            </div>
            <span className="text-stone-300">→</span>
            <div className="flex items-center gap-1 text-stone-400 shrink-0">
              <Lock className="w-3 h-3 text-stone-400" />
              <span>04 Feasibility</span>
            </div>
            <span className="text-stone-300">→</span>
            <div className="flex items-center gap-1 text-stone-400 shrink-0">
              <Lock className="w-3 h-3 text-stone-400" />
              <span>05 DPR</span>
            </div>
          </div>
        </div>

        {/* Language Selector Toolbar */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <Globe2 className="w-4 h-4 text-[#EA580C]" />
            <span className="text-xs font-bold text-[#57534E]">Select Language / ಭಾಷೆ / भाषा:</span>
          </div>

          <div className="inline-flex p-1 rounded-2xl bg-[#EFE8DE] border border-[#D6CDBC]">
            {SUPPORTED_LANGUAGES.map((lang) => (
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
                className={`px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                  selectedLanguage === lang.code
                    ? 'bg-white text-[#EA580C] shadow-sm'
                    : 'text-[#78716C] hover:text-[#1C1917]'
                }`}
              >
                {lang.native} ({lang.label})
              </button>
            ))}
          </div>
        </div>

        {/* Header Banner */}
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <Badge variant="saffron">{t.badge}</Badge>
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
            <div className="flex-grow font-medium">{errorMessage}</div>
            <button onClick={() => setErrorMessage(null)} className="text-rose-600 font-bold text-sm">×</button>
          </div>
        )}

        {/* Initial Intake Section */}
        {!profile ? (
          <div className="royal-card rounded-3xl p-6 sm:p-8 space-y-6 shadow-md bg-white/95 backdrop-blur-sm border border-[#EAE3D5]">
            {/* User Guidance Card */}
            <div className="p-4 sm:p-5 rounded-2xl bg-[#FAF7F2] border border-[#E2D9CB] space-y-2">
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
              <div className="inline-flex p-1 rounded-2xl bg-[#EFE8DE] border border-[#D6CDBC]">
                <button
                  type="button"
                  onClick={() => { setActiveTab('text'); setErrorMessage(null); }}
                  className={`flex items-center gap-2 px-6 py-2 rounded-xl text-xs font-bold transition-all ${
                    activeTab === 'text'
                      ? 'bg-white text-[#1C1917] shadow-sm'
                      : 'text-[#78716C] hover:text-[#1C1917]'
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
                      ? 'bg-white text-[#1C1917] shadow-sm'
                      : 'text-[#78716C] hover:text-[#1C1917]'
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
                    className="w-full bg-[#FAF7F2] border border-[#D6CDBC] rounded-2xl p-4 text-sm text-[#1C1917] placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-[#EA580C] resize-none transition-all leading-relaxed"
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
                        className="text-left px-3 py-1.5 rounded-xl bg-[#FAF7F2] hover:bg-orange-50 border border-[#D6CDBC] hover:border-orange-300 text-xs text-[#44403C] hover:text-[#C2410C] transition-all"
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
                    <div className="text-left p-4 rounded-2xl bg-[#FAF7F2] border border-[#D6CDBC] space-y-3 animate-fadeIn">
                      <div className="flex items-center justify-between text-xs text-[#78716C] font-semibold">
                        <span>{t.transcriptReceived}</span>
                        <Badge variant="saffron">Sarvam STT</Badge>
                      </div>
                      <textarea
                        rows={3}
                        value={voiceTranscript}
                        onChange={(e) => setVoiceTranscript(e.target.value)}
                        className="w-full bg-white border border-[#D6CDBC] rounded-xl p-3 text-sm text-[#1C1917] focus:outline-none focus:ring-2 focus:ring-orange-500/50"
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
            <div className="royal-panel rounded-3xl p-6 sm:p-8 space-y-6 shadow-md border border-[#EAE3D5]">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#EAE3D5] pb-4">
                <div>
                  <Badge variant="saffron" className="mb-1">Stage 1 Profile</Badge>
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
                <div className="p-4 rounded-2xl bg-white border border-[#EAE3D5] space-y-2 relative group">
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
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-orange-500"
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
                <div className="p-4 rounded-2xl bg-white border border-[#EAE3D5] space-y-2 relative">
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
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none"
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
                      <span className="inline-block text-[11px] px-2 py-0.5 rounded bg-orange-50 text-[#C2410C] font-semibold capitalize">
                        Stage: {profile.business_stage || 'Planning'}
                      </span>
                    </>
                  )}
                </div>

                {/* 3. Available Capital */}
                <div className="p-4 rounded-2xl bg-white border border-[#EAE3D5] space-y-2 relative">
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
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-orange-500"
                      />
                      <div className="flex gap-1 justify-end">
                        <button onClick={() => setEditingField(null)} className="px-2 py-1 text-[10px] text-stone-500 font-bold">{t.cancel}</button>
                        <button onClick={handleSaveEdit} className="px-2 py-1 text-[10px] bg-[#EA580C] text-white rounded font-bold">{t.save}</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-base font-bold text-[#1C1917]">
                        {profile.available_capital !== null ? formatCurrency(profile.available_capital) : <span className="text-amber-600 italic">Pending clarification</span>}
                      </p>
                      <span className="text-[11px] text-stone-500">
                        {profile.available_capital !== null ? 'Verified' : 'Required for Stage 1'}
                      </span>
                    </>
                  )}
                </div>

                {/* 4. Business Location */}
                <div className="p-4 rounded-2xl bg-white border border-[#EAE3D5] space-y-2 relative">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C] flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-[#EA580C]" />
                      Business Location
                    </span>
                    <button
                      onClick={() => handleStartEdit('proposed_location', profile.proposed_location?.district || profile.proposed_location?.name)}
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
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-orange-500"
                      />
                      <div className="flex gap-1 justify-end">
                        <button onClick={() => setEditingField(null)} className="px-2 py-1 text-[10px] text-stone-500 font-bold">{t.cancel}</button>
                        <button onClick={handleSaveEdit} className="px-2 py-1 text-[10px] bg-[#EA580C] text-white rounded font-bold">{t.save}</button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm font-bold text-[#1C1917]">
                        {profile.proposed_location?.district 
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
                <div className="p-4 rounded-2xl bg-white border border-[#EAE3D5] space-y-2">
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
                <div className="p-4 rounded-2xl bg-white border border-[#EAE3D5] space-y-2 relative">
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
                        className="w-full text-xs p-2 border border-orange-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-orange-500"
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
            {nextAction?.type === 'clarification' && nextAction.question ? (
              <div className="royal-card rounded-3xl p-6 sm:p-8 border-2 border-amber-300 bg-amber-50/40 space-y-5 shadow-md animate-fadeIn">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="gold">{t.clarificationTitle}</Badge>
                    <span className="text-xs text-[#78716C] font-semibold">
                      Field: <span className="font-mono text-[#C2410C]">{nextAction.field}</span>
                    </span>
                  </div>

                  {/* Browser TTS Button */}
                  <button
                    type="button"
                    onClick={() => handleToggleTTS(nextAction.question)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all border ${
                      isSpeaking
                        ? 'bg-rose-100 text-rose-800 border-rose-300'
                        : 'bg-white text-[#EA580C] border-orange-200 hover:bg-orange-50 shadow-sm'
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
                    {nextAction.question}
                  </h3>
                  {nextAction.helper_text && (
                    <p className="text-xs sm:text-sm font-medium text-[#57534E]">
                      {nextAction.helper_text}
                    </p>
                  )}
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
                        className="px-5 py-2.5 rounded-2xl bg-white border-2 border-orange-300 hover:border-orange-500 text-sm font-bold text-[#1C1917] hover:bg-orange-50 transition-all shadow-sm flex items-center gap-2"
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
                      className="inline-flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-white border border-[#D6CDBC] hover:border-orange-400 text-xs font-bold text-[#1C1917] hover:bg-orange-50 shadow-sm transition-all"
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
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-stone-100 hover:bg-stone-200 text-xs font-bold text-stone-700 transition-all"
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
                          ? 'bg-[#1C1917] text-white'
                          : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-100'
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
                          : 'bg-white text-stone-600 border border-stone-200 hover:bg-stone-100'
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
                        className="flex-grow bg-white border border-[#D6CDBC] rounded-xl px-4 py-3 text-sm text-[#1C1917] focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-[#EA580C]"
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
                    <div className="p-4 rounded-2xl bg-white border border-[#D6CDBC] space-y-3">
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
              <div className="royal-card rounded-3xl p-6 sm:p-8 bg-emerald-50/70 border-2 border-emerald-300 space-y-4 text-center animate-fadeIn shadow-md">
                <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto shadow-inner">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-2xl font-bold text-emerald-950 font-['Outfit']">
                    {t.stage1CompleteTitle}
                  </h3>
                  <p className="text-xs sm:text-sm text-emerald-800 max-w-lg mx-auto leading-relaxed">
                    {t.stage1CompleteDesc}
                  </p>
                </div>

                <div className="pt-3 flex justify-center">
                  <button
                    type="button"
                    onClick={() => {
                      const sid = sessionResponse?.session_id || sessionResponse?.profile?.session_id || '';
                      console.log('[STAGE 1 → STAGE 2] Proceeding with session_id:', sid);
                      navigate(`/classification${sid ? `?session_id=${encodeURIComponent(sid)}` : ''}`);
                    }}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#EA580C] hover:bg-[#C2410C] text-white text-sm font-bold shadow-lg shadow-orange-900/20 transition-all hover:scale-105"
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
