"""
Multilingual Business Concept, Intent, Location, and Skills Extractor.
Extracts business ideas across English, Hindi, Marathi, Kannada, Tamil, Telugu, and Hinglish.
Provides authoritative input for Stage 2 Business Ontology and Classification.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from app.services.intake.language_normalizer import normalize_unicode_text

# Comprehensive Multilingual Business Ontologies
MULTILINGUAL_BUSINESS_PATTERNS = [
    {
        "patterns": [
            r"saree\s*(?:shop|store|retail|business|market)?", r"sari\s*(?:shop|store|retail)?", r"cloth\s*(?:shop|store)",
            r"garment\s*store", r"textile\s*shop", r"silk\s*saree",
            r"ಸೀರೆ\s*(?:ಅಂಗಡಿ|ವ್ಯಾಪಾರ|ಉದ್ಯಮ)?", r"ಬಟ್ಟೆ\s*ಅಂಗಡಿ", r"ಟೆಕ್ಸ್‌ಟೈಲ್\s*ಅಂಗಡಿ",
            r"साड़ी\s*(?:का|की|के)?\s*(?:दुकान|शॉप|स्टोर|व्यापार|व्यवसाय)", r"साड़ी\s*सेंटर", r"कापड\s*दुकान", r"कपड़े\s*की\s*दुकान",
            r"புடவைக்\s*கடை", r"சீலை\s*கடை", r"चीरेचे\s*दुकान", r"साड़ी"
        ],
        "business_concept": "Saree Retail",
        "category_hint": "Textiles & Ethnic Apparel Retail",
        "product_service": "Sarees, Traditional Wear and Fabrics",
        "products": ["Silk Sarees", "Cotton Sarees", "Ethnic Wear", "Textiles"]
    },
    {
        "patterns": [
            r"rice\s*mill", r"paddy\s*mill", r"paddy\s*processing",
            r"ರೈಸ್\s*ಮಿಲ್", r"ರೈಸ್\s*ಮಿಲ್ಲು", r"ಅಕ್ಕಿ\s*ಗಿರಣಿ", r"ಭತ್ತದ\s*ಗಿರಣಿ",
            r"राइस\s*मिल", r"चावल\s*मिल", r"भात\s*गिरणी", r"धान\s*मिल", r"ಅಕ್ಕಿ\s*ಮಿಲ್",
            r"அரிசி\s*ஆலை"
        ],
        "business_concept": "Rice Mill",
        "category_hint": "Agro Processing & Grain Milling",
        "product_service": "Paddy Milling & Rice Processing",
        "products": ["Raw Rice", "Boiled Rice", "Rice Bran", "Husk"]
    },
    {
        "patterns": [
            r"dairy\s*farm", r"dairy\s*farming", r"dairy\s*business", r"milk\s*business", r"cattle\s*farming", r"dairy",
            r"ಡೈರಿ\s*ಫಾರ್ಮ್", r"ಡೈರಿ\s*ವ್ಯವಹಾರ", r"ಹೈನುಗಾರಿಕೆ", r"ಹಸು\s*ಸಾಕಾಣಿಕೆ", r"ಹಾಲು\s*ವ್ಯಾಪಾರ", r"ಡೈರಿ",
            r"दूध\s*का\s*(?:व्यापार|व्यवसाय|काम)", r"दूध\s*की\s*डेयरी", r"डेयरी\s*फार्म", r"डेयरी\s*व्यवसाय", r"डेयरी", r"पशुपालन",
            r"गाई\s*म्हशींचा\s*व्यवसाय", r"பால்\s*பண்ணை", r"పాల\s*డైరీ"
        ],
        "business_concept": "Dairy Farm",
        "category_hint": "Livestock & Dairy Farming",
        "product_service": "Fresh Milk & Dairy Derivatives",
        "products": ["Fresh Cow Milk", "Buffalo Milk", "Curd", "Ghee", "Paneer"]
    },
    {
        "patterns": [
            r"grocery\s*shop", r"grocery\s*store", r"kirana\s*shop", r"kirana\s*store", r"provision\s*store", r"general\s*store", r"grocery", r"kirana",
            r"ಕಿರಾಣಿ\s*ಅಂಗಡಿ", r"ದವಸ\s*ಧಾನ್ಯದ\s*ಅಂಗಡಿ", r"ಪ್ರಾವಿಷನ್\s*ಸ್ಟೋರ್", r"ಕಿರಾಣಿ\s*ವ್ಯಾಪಾರ",
            r"किराना\s*दुकान", r"किराणा\s*दुकान", r"राशन\s*दुकान", r"जनरल\s*स्टोर", r"மளிகைக்\s*கடை"
        ],
        "business_concept": "Grocery & Kirana Store",
        "category_hint": "Retail & Essential FMCG",
        "product_service": "Groceries and Household Essentials",
        "products": ["Grains", "Pulses", "Packaged Goods", "Spices", "Oils", "Toiletries"]
    },
    {
        "patterns": [
            r"poultry\s*farm", r"poultry\s*farming", r"chicken\s*farm", r"egg\s*farm", r"poultry",
            r"ಕೋಳಿ\s*ಸಾಕಾಣಿಕೆ", r"ಕೋಳಿ\s*ಫಾರ್ಮ್", r"ಮೊಟ್ಟೆ\s*ಉತ್ಪಾದನೆ",
            r"पोल्ट्री\s*फार्म", r"कुक्कुटपालन", r"मुर्गी\s*पालन", r"कोழிப்\s*பண்ணை"
        ],
        "business_concept": "Poultry Farming",
        "category_hint": "Animal Husbandry & Poultry",
        "product_service": "Broiler Poultry & Egg Production",
        "products": ["Broiler Chicken", "Country Eggs", "Poultry Feed"]
    },
    {
        "patterns": [
            r"flour\s*mill", r"atta\s*chakki", r"grain\s*mill",
            r"ಹಿಟ್ಟಿನ\s*ಗಿರಣಿ", r"ಗಿರಣಿ", r"ಆಟಾ\s*ಚಕ್ಕಿ", r"ಹಿಟ್ಟು\s*ಬೀಸುವ\s*ಗಿರಣಿ",
            r"आटा\s*चक्की", r"दाल\s*मिल", r"गिरणी", r"पिसाई\s*केंद्र", r"माவு\s*மில்"
        ],
        "business_concept": "Flour Mill (Atta Chakki)",
        "category_hint": "Agro Processing & Custom Milling",
        "product_service": "Grain Milling & Flour Supply",
        "products": ["Wheat Flour", "Ragi Flour", "Gram Flour (Besan)", "Milled Cereals"]
    },
    {
        "patterns": [
            r"tailoring\s*shop", r"boutique", r"tailoring", r"garment\s*stitching", r"custom\s*tailoring",
            r"ಟೈಲರಿಂಗ್\s*ಅಂಗಡಿ", r"ಬಟ್ಟೆ\s*ಹೊಲಿಯುವುದು", r"ಟೈಲರಿಂಗ್", r"ಲೇಡೀಸ್\s*ಬೊಟಿಕ್",
            r"सिलाई\s*का\s*काम", r"सिलाई\s*केंद्र", r"टेलरिंग", r"बुटीक", r"दर्जी\s*दुकान", r"सिलाई", r"தையல்\s*கடை"
        ],
        "business_concept": "Tailoring & Boutique",
        "category_hint": "Apparel & Custom Tailoring",
        "product_service": "Custom Tailoring & Alteration",
        "products": ["Blouse Stitching", "Dresses", "Custom Garments", "Alterations"]
    },
    {
        "patterns": [
            r"tea\s*stall", r"chai\s*stall", r"tea\s*shop", r"tea\s*and\s*snacks", r"cafeteria", r"chai\s*shop",
            r"ಟೀ\s*ಅಂಗಡಿ", r"ಚಹಾ\s*ಅಂಗಡಿ", r"ಕಾಫಿ\s*ಮತ್ತು\s*ತಿಂಡಿ\s*ಹೋಟೆಲ್",
            r"चाय\s*की\s*दुकान", r"चाय\s*स्टॉल", r"हॉटेल", r"चहाचे\s*दुकान", r"தேநீர்\s*கடை"
        ],
        "business_concept": "Tea Stall & Refreshments",
        "category_hint": "Food & Beverage Kiosk",
        "product_service": "Hot Beverages & Local Snacks",
        "products": ["Tea", "Filter Coffee", "Snacks", "Bakery Items"]
    },
    {
        "patterns": [
            r"beauty\s*parlour", r"salon", r"bridal\s*makeup",
            r"ಬ್ಯೂಟಿ\s*ಪಾರ್ಲರ್", r"ಸಲೂನ್", r"ಮೇಕಪ್\s*ಸ್ಟುಡಿಯೋ",
            r"ब्यूटी\s*पार्लर", r"सलून", r"मेकअप\s*सेंटर", r"अழகு\s*நிலையம்"
        ],
        "business_concept": "Beauty Parlour & Salon",
        "category_hint": "Personal Care & Wellness",
        "product_service": "Grooming, Haircare & Bridal Makeup",
        "products": ["Skincare", "Haircare", "Bridal Services", "Facials"]
    },
    {
        "patterns": [
            r"mobile\s*repair", r"mobile\s*shop", r"smartphone\s*service",
            r"ಮೊಬೈಲ್\s*ಅಂಗಡಿ", r"ಮೊಬೈಲ್\s*ರಿಪೇರಿ", r"ಮೊಬೈಲ್\s*ಸರ್ವಿಸ್",
            r"मोबाइल\s*रिपेयरिंग", r"मोबाइल\s*दुकान", r"मोबाइल\s*सर्विसिंग", r"மொபைல்\s*கடை"
        ],
        "business_concept": "Mobile Sales & Repair",
        "category_hint": "Electronics & Telecommunication",
        "product_service": "Smartphone Servicing & Accessories",
        "products": ["Phone Repair", "Accessories", "Screen Replacement", "Recharge Services"]
    },
    {
        "patterns": [
            r"carpentry", r"furniture\s*making", r"woodwork",
            r"ಮರಗೆಲಸ", r"ಬಡಗಿ\s*ಕೆಲಸ", r"ಫರ್ನಿಚರ್\s*ಅಂಗಡಿ",
            r"बढ़ई\s*का\s*काम", r"फर्नीचर\s*दुकान", r"लकड़ी\s*का\s*काम", r"மரவேலை"
        ],
        "business_concept": "Carpentry & Furniture Workshop",
        "category_hint": "Woodworking & Furniture Fabrication",
        "product_service": "Custom Wood Furniture & Woodwork",
        "products": ["Doors", "Tables", "Chairs", "Custom Wooden Cabinets"]
    },
    {
        "patterns": [
            r"organic\s*farming", r"agriculture", r"farming\s*business", r"horticulture", r"farming",
            r"ಸಾವಯವ\s*ಕೃಷಿ", r"ಕೃಷಿ", r"ತೋಟಗಾರಿಕೆ", r"ತರಕಾರಿ\s*ಬೆಳೆಯುವುದು",
            r"जैविक\s*खेती", r"खेती\s*बाड़ी", r"बागवानी", r"सब्जी\s*उत्पादन", r"இயற்கை\s*விவசாயம்"
        ],
        "business_concept": "Organic Farming & Horticulture",
        "category_hint": "Sustainable Agriculture",
        "product_service": "Organic Crop & Vegetable Cultivation",
        "products": ["Organic Vegetables", "Pulses", "Fruits", "Organic Seeds"]
    },
    {
        "patterns": [
            r"food\s*processing", r"spice\s*manufacturing", r"pickle\s*making",
            r"ಆಹಾರ\s*ಸಂಸ್ಕರಣೆ", r"ಮಸಾಲೆ\s*ತಯಾರಿಕೆ", r"ಉಪ್ಪಿನಕಾಯಿ\s*ಉದ್ಯಮ",
            r"खाद्य\s*प्रसंस्करण", r"मसाला\s*उद्योग", r"अचार\s*उद्योग", r"पापड़\s*उद्योग"
        ],
        "business_concept": "Food Processing & Spices",
        "category_hint": "Food Manufacturing & Value Addition",
        "product_service": "Processed Foods, Pickles & Blended Spices",
        "products": ["Ground Spices", "Pickles", "Papads", "Food Condiments"]
    },
    {
        "patterns": [
            r"goat\s*farming", r"sheep\s*farming", r"goat\s*rearing",
            r"ಕುರಿ\s*ಸಾಕಾಣಿಕೆ", r"ಮೇಕೆ\s*ಸಾಕಾಣಿಕೆ",
            r"बकरी\s*पालन", r"भेड़\s*पालन", r"ஆடு\s*வளர்ப்பு"
        ],
        "business_concept": "Goat & Sheep Farming",
        "category_hint": "Livestock Husbandry",
        "product_service": "Goat & Sheep Rearing",
        "products": ["Goat Meat", "Sheep Wool", "Live Stock"]
    },
    {
        "patterns": [
            r"bakery", r"cake\s*shop",
            r"ಬೇಕರಿ", r"ಬೇಕರಿ\s*ಅಂಗಡಿ",
            r"बेकरी", r"केक\s*शॉप", r"ரொட்டி\s*தயாரிப்பு"
        ],
        "business_concept": "Bakery & Confectionery",
        "category_hint": "Food Processing & Baked Goods",
        "product_service": "Fresh Breads, Buns & Cakes",
        "products": ["Bread", "Biscuits", "Buns", "Cakes"]
    }
]

# Multilingual Location Catalog
KNOWN_LOCATIONS: Dict[str, Dict[str, str]] = {
    # Karnataka Districts & Cities
    "mandya": {"district": "Mandya", "state": "Karnataka"},
    "ಮಂಡ್ಯ": {"district": "Mandya", "state": "Karnataka"},
    "मांड्या": {"district": "Mandya", "state": "Karnataka"},
    "mysuru": {"district": "Mysuru", "state": "Karnataka"},
    "mysore": {"district": "Mysuru", "state": "Karnataka"},
    "ಮೈಸೂರು": {"district": "Mysuru", "state": "Karnataka"},
    "मैसूर": {"district": "Mysuru", "state": "Karnataka"},
    "मैसुरु": {"district": "Mysuru", "state": "Karnataka"},
    "bengaluru": {"district": "Bengaluru", "state": "Karnataka"},
    "bangalore": {"district": "Bengaluru", "state": "Karnataka"},
    "ಬೆಂಗಳೂರು": {"district": "Bengaluru", "state": "Karnataka"},
    "बेंगलुरु": {"district": "Bengaluru", "state": "Karnataka"},
    "बैंगलोर": {"district": "Bengaluru", "state": "Karnataka"},
    "hassan": {"district": "Hassan", "state": "Karnataka"},
    "ಹಾಸನ": {"district": "Hassan", "state": "Karnataka"},
    "हासन": {"district": "Hassan", "state": "Karnataka"},
    "tumakuru": {"district": "Tumakuru", "state": "Karnataka"},
    "tumkur": {"district": "Tumakuru", "state": "Karnataka"},
    "ತುಮಕೂರು": {"district": "Tumakuru", "state": "Karnataka"},
    "तुमकुर": {"district": "Tumakuru", "state": "Karnataka"},
    "belagavi": {"district": "Belagavi", "state": "Karnataka"},
    "belgaum": {"district": "Belagavi", "state": "Karnataka"},
    "ಬೆಳಗಾವಿ": {"district": "Belagavi", "state": "Karnataka"},
    "बेलगावी": {"district": "Belagavi", "state": "Karnataka"},
    "dharwad": {"district": "Dharwad", "state": "Karnataka"},
    "hubli": {"district": "Dharwad", "state": "Karnataka"},
    "hubballi": {"district": "Dharwad", "state": "Karnataka"},
    "ಧಾರವಾಡ": {"district": "Dharwad", "state": "Karnataka"},
    "ಹುಬ್ಬಳ್ಳಿ": {"district": "Dharwad", "state": "Karnataka"},
    "धारवाड़": {"district": "Dharwad", "state": "Karnataka"},
    "हुबली": {"district": "Dharwad", "state": "Karnataka"},
    "shivamogga": {"district": "Shivamogga", "state": "Karnataka"},
    "shimoga": {"district": "Shivamogga", "state": "Karnataka"},
    "ಶಿವಮೊಗ್ಗ": {"district": "Shivamogga", "state": "Karnataka"},
    "शिमोगा": {"district": "Shivamogga", "state": "Karnataka"},
    "mangaluru": {"district": "Dakshina Kannada", "state": "Karnataka"},
    "mangalore": {"district": "Dakshina Kannada", "state": "Karnataka"},
    "ಮಂಗಳೂರು": {"district": "Dakshina Kannada", "state": "Karnataka"},
    "मंगलौर": {"district": "Dakshina Kannada", "state": "Karnataka"},
    "udupi": {"district": "Udupi", "state": "Karnataka"},
    "ಉಡುಪಿ": {"district": "Udupi", "state": "Karnataka"},
    "उडुपी": {"district": "Udupi", "state": "Karnataka"},
    "ballari": {"district": "Ballari", "state": "Karnataka"},
    "bellary": {"district": "Ballari", "state": "Karnataka"},
    "ಬಳ್ಳಾರಿ": {"district": "Ballari", "state": "Karnataka"},
    "बेल्लारी": {"district": "Ballari", "state": "Karnataka"},
    "raichur": {"district": "Raichur", "state": "Karnataka"},
    "ರಾಯಚೂರು": {"district": "Raichur", "state": "Karnataka"},
    "रायचूर": {"district": "Raichur", "state": "Karnataka"},
    "kalaburagi": {"district": "Kalaburagi", "state": "Karnataka"},
    "gulbarga": {"district": "Kalaburagi", "state": "Karnataka"},
    "ಕಲಬುರಗಿ": {"district": "Kalaburagi", "state": "Karnataka"},
    "कलबुर्गी": {"district": "Kalaburagi", "state": "Karnataka"},
    "davanagere": {"district": "Davanagere", "state": "Karnataka"},
    "ದಾವಣಗೆರೆ": {"district": "Davanagere", "state": "Karnataka"},
    "दावणगेरे": {"district": "Davanagere", "state": "Karnataka"},
    "kolar": {"district": "Kolar", "state": "Karnataka"},
    "ಕೋಲಾರ": {"district": "Kolar", "state": "Karnataka"},
    "कोलार": {"district": "Kolar", "state": "Karnataka"},
    "chikkamagaluru": {"district": "Chikkamagaluru", "state": "Karnataka"},
    "chikmagalur": {"district": "Chikkamagaluru", "state": "Karnataka"},
    "ಚಿಕ್ಕಮಗಳೂರು": {"district": "Chikkamagaluru", "state": "Karnataka"},
    "karnataka": {"state": "Karnataka"},
    "ಕರ್ನಾಟಕ": {"state": "Karnataka"},
    "कर्नाटक": {"state": "Karnataka"},

    # Maharashtra
    "nagpur": {"district": "Nagpur", "state": "Maharashtra"},
    "नागपुर": {"district": "Nagpur", "state": "Maharashtra"},
    "नागपूर": {"district": "Nagpur", "state": "Maharashtra"},
    "pune": {"district": "Pune", "state": "Maharashtra"},
    "पुणे": {"district": "Pune", "state": "Maharashtra"},
    "mumbai": {"district": "Mumbai", "state": "Maharashtra"},
    "मुंबई": {"district": "Mumbai", "state": "Maharashtra"},
    "nashik": {"district": "Nashik", "state": "Maharashtra"},
    "नाशिक": {"district": "Nashik", "state": "Maharashtra"},
    "amravati": {"district": "Amravati", "state": "Maharashtra"},
    "अमरावती": {"district": "Amravati", "state": "Maharashtra"},
    "aurangabad": {"district": "Chhatrapati Sambhajinagar", "state": "Maharashtra"},
    "संभाजीनगर": {"district": "Chhatrapati Sambhajinagar", "state": "Maharashtra"},
    "solapur": {"district": "Solapur", "state": "Maharashtra"},
    "सोलापूर": {"district": "Solapur", "state": "Maharashtra"},
    "सोलापुर": {"district": "Solapur", "state": "Maharashtra"},
    "maharashtra": {"state": "Maharashtra"},
    "महाराष्ट्र": {"state": "Maharashtra"},

    # Jharkhand & Eastern Hubs
    "chatra": {"district": "Chatra", "state": "Jharkhand"},
    "चतरा": {"district": "Chatra", "state": "Jharkhand"},
    "ranchi": {"district": "Ranchi", "state": "Jharkhand"},
    "रांची": {"district": "Ranchi", "state": "Jharkhand"},
    "dhanbad": {"district": "Dhanbad", "state": "Jharkhand"},
    "धनबाद": {"district": "Dhanbad", "state": "Jharkhand"},
    "hazaribagh": {"district": "Hazaribagh", "state": "Jharkhand"},
    "हजारीबाग": {"district": "Hazaribagh", "state": "Jharkhand"},
    "jharkhand": {"state": "Jharkhand"},
    "झारखंड": {"state": "Jharkhand"},

    # Other States & Key Hubs
    "indore": {"district": "Indore", "state": "Madhya Pradesh"},
    "इंदौर": {"district": "Indore", "state": "Madhya Pradesh"},
    "bhopal": {"district": "Bhopal", "state": "Madhya Pradesh"},
    "भोपाल": {"district": "Bhopal", "state": "Madhya Pradesh"},
    "varanasi": {"district": "Varanasi", "state": "Uttar Pradesh"},
    "वाराणसी": {"district": "Varanasi", "state": "Uttar Pradesh"},
    "lucknow": {"district": "Lucknow", "state": "Uttar Pradesh"},
    "लखनऊ": {"district": "Lucknow", "state": "Uttar Pradesh"},
    "patna": {"district": "Patna", "state": "Bihar"},
    "पटना": {"district": "Patna", "state": "Bihar"},
    "jaipur": {"district": "Jaipur", "state": "Rajasthan"},
    "जयपुर": {"district": "Jaipur", "state": "Rajasthan"},
    "chennai": {"district": "Chennai", "state": "Tamil Nadu"},
    "சென்னை": {"district": "Chennai", "state": "Tamil Nadu"},
    "hyderabad": {"district": "Hyderabad", "state": "Telangana"},
    "ಹೈದರಾಬಾದ್": {"district": "Hyderabad", "state": "Telangana"},
    "हैदराबाद": {"district": "Hyderabad", "state": "Telangana"},
    "madhya pradesh": {"state": "Madhya Pradesh"},
    "मध्य प्रदेश": {"state": "Madhya Pradesh"},
    "uttar pradesh": {"state": "Uttar Pradesh"},
    "उत्तर प्रदेश": {"state": "Uttar Pradesh"},
    "tamil nadu": {"state": "Tamil Nadu"},
    "தமிழ்நாடு": {"state": "Tamil Nadu"},
    "telangana": {"state": "Telangana"},
    "तेलंगाना": {"state": "Telangana"},
    "andhra pradesh": {"state": "Andhra Pradesh"},
    "आंध्र प्रदेश": {"state": "Andhra Pradesh"},
    "bihar": {"state": "Bihar"},
    "बिहार": {"state": "Bihar"},
    "rajasthan": {"state": "Rajasthan"},
    "राजस्थान": {"state": "Rajasthan"},
    "gujarat": {"state": "Gujarat"},
    "गुजरात": {"state": "Gujarat"},
}


@dataclass
class LocationExtracted:
    name: str = ""
    district: str = ""
    state: str = ""
    country: str = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = "unresolved"


@dataclass
class BusinessEntityResult:
    business_concept: Optional[str]
    business_category_hint: Optional[str]
    intent: str
    business_stage: str
    location: LocationExtracted
    skills: List[str] = field(default_factory=list)
    skills_status: str = "unspecified"
    experience_years: Optional[float] = None
    product_service: Optional[str] = None
    products: List[str] = field(default_factory=list)


def extract_multilingual_business_entities(
    text: str,
    language_code: str = "en"
) -> BusinessEntityResult:
    """
    Deterministically extracts Business Concept, Intent, Location, and Skills.
    """
    if not text:
        text = ""

    clean = normalize_unicode_text(text)
    lower = clean.lower()

    # 1. Intent Detection
    expand_markers = [
        "already run", "already have", "already running", "expand", "scale", "grow", "expansion",
        "ಈಗಾಗಲೇ", "ನಡೆಸುತ್ತಿದ್ದೇನೆ", "ವಿಸ್ತರಿಸಲು", "ಬೆಳೆಸಲು", "ಹೆಚ್ಚಿಸಲು", "ಹಾಲಿ ಅಂಗಡಿ",
        "पहले से", "पहले से ही", "बढ़ाना", "विस्तार", "दुकान है", "पूर्वीपासून", "वाढवायचा", "விரிவுபடுத்த"
    ]
    start_markers = [
        "want to open", "want to start", "planning to start", "open a", "start a", "looking to start",
        "new business", "start business", "setup a", "establish", "kholna hai", "kholna", "shuru karna",
        "ಆರಂಭಿಸಲು", "ಪ್ರಾರಂಭಿಸಲು", "ತೆರೆಯಲು", "ಮಾಡಬೇಕು", "ಮಾಡಲು ಬಯಸುತ್ತೇನೆ", "ಹೊಸದಾಗಿ", "ಹೊಸ ಉದ್ಯಮ",
        "शुरू करना", "शुरू करनी", "खोलना", "खोलनी", "नया व्यवसाय", "सुरू करू", "खोलायची", "தொழில் தொடங்க"
    ]
    existing_markers = [
        "existing business", "current shop", "ನನ್ನ ಅಂಗಡಿ", "ನನ್ನ ವ್ಯಾಪಾರ", "मौजूदा व्यापार", "माझा व्यवसाय"
    ]

    primary_intent = "start_business"
    business_stage = "planning"

    if any(m in lower or m in clean for m in expand_markers):
        primary_intent = "expand_business"
        business_stage = "existing"
    elif any(m in lower or m in clean for m in start_markers):
        primary_intent = "start_business"
        business_stage = "planning"
    elif any(m in lower or m in clean for m in existing_markers):
        primary_intent = "existing_business"
        business_stage = "existing"

    # 2. Business Concept Extraction
    business_concept = None
    business_category_hint = None
    product_service = None
    products = []

    for item in MULTILINGUAL_BUSINESS_PATTERNS:
        for pat in item["patterns"]:
            if re.search(pat, clean, re.IGNORECASE):
                business_concept = item["business_concept"]
                business_category_hint = item["category_hint"]
                product_service = item["product_service"]
                products = item["products"]
                break
        if business_concept:
            break

    # Dynamic fallback pattern for unlisted business ideas
    if not business_concept:
        fallback_patterns = [
            r"(?:start|open|run|build|setup)\s+(?:a|an)?\s*([a-zA-Z\s]{3,35}?)(?:\s+in|\s+with|\s+having|\.|$)",
            r"([a-zA-Z\s]{3,30}?)\s+(?:business|shop|store|enterprise|mill|farm|unit)",
            r"([^\s]+(?:\s+[^\s]+){0,3}?)\s*(?:ಪ್ರಾರಂಭಿಸಲು|ಆರಂಭಿಸಲು|ತೆರೆಯಲು|ಮಾಡಬೇಕು)",
            r"([^\s]+(?:\s+[^\s]+){0,3}?)\s*(?:शुरू\s*करना|खोलना|का\s*काम|का\s*व्यापार)"
        ]
        for fpat in fallback_patterns:
            m = re.search(fpat, clean, re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if candidate and candidate.lower() not in ["my", "the", "this", "new", "a", "an", "ಹೊಸ", "नया", "मुझे", "ನಾನು"]:
                    business_concept = candidate.title() if candidate.isascii() else candidate
                    business_category_hint = "General Micro Enterprise"
                    product_service = business_concept
                    products = [business_concept]
                    break

    # 3. Location Extraction
    location_name = ""
    district = ""
    state = ""
    location_source = "unresolved"

    village_phrases = [
        "my village", "in village", "in my village", "in the village",
        "ನನ್ನ ಹಳ್ಳಿಯಲ್ಲಿ", "ಹಳ್ಳಿಯಲ್ಲಿ", "ಗ್ರಾಮದಲ್ಲಿ", "ನನ್ನ ಗ್ರಾಮ",
        "गांव में", "गाँव में", "गावात", "माझ्या गावात", "கிராமத்தில்"
    ]
    if any(vp in lower or vp in clean for vp in village_phrases):
        location_name = "User Village"
        location_source = "user"

    town_phrases = [
        "my town", "in town", "in city", "ನನ್ನ ಊರಿನಲ್ಲಿ", "ನಗರದಲ್ಲಿ", "ಪಟ್ಟಣದಲ್ಲಿ",
        "शहर में", "शहरात", "माझ्या शहरात", "நகரத்தில்"
    ]
    if any(tp in lower or tp in clean for tp in town_phrases):
        location_name = "User Town"
        location_source = "user"

    for loc_key, loc_meta in KNOWN_LOCATIONS.items():
        if loc_key.isascii():
            matched = bool(re.search(rf"\b{re.escape(loc_key)}\b", lower))
        else:
            matched = (loc_key in clean)

        if matched:
            if "district" in loc_meta and not district:
                district = loc_meta["district"]
            if "state" in loc_meta and not state:
                state = loc_meta["state"]
            if not location_name or location_name in ["User Village", "User Town"]:
                location_name = loc_meta.get("district", loc_key.title())
            location_source = "user"

    near_match = re.search(r"near\s+([a-zA-Z\s]{3,20})", lower)
    if near_match:
        near_loc = near_match.group(1).strip()
        location_name = f"Near {near_loc.title()}"
        location_source = "user"
        if not district:
            district = near_loc.title()

    loc_obj = LocationExtracted(
        name=location_name,
        district=district,
        state=state,
        country="India",
        source=location_source
    )

    # 4. Entrepreneur Skills Extraction
    skills: List[str] = []
    skills_status = "unspecified"
    experience_years: Optional[float] = None

    no_exp_markers = [
        "no experience", "no prior experience", "don't have experience", "do not have experience",
        "no skills", "none", "fresher", "fresh",
        "ಯಾವುದೇ ಅನುಭವವಿಲ್ಲ", "ಅನುಭವವಿಲ್ಲ", "ಅನುಭವ ಇಲ್ಲ", "ಅನುಭವವೇನೂ ಇಲ್ಲ", "ಹೊಸಬ", "ಮೊದಲ ಬಾರಿ",
        "कोई अनुभव नहीं", "अनुभव नहीं है", "अनुभव नहीं", "नया हूँ", "नाही", "अनुभव नाही", "पहिला व्यवसाय"
    ]

    if any(nm in lower or nm in clean for nm in no_exp_markers):
        skills_status = "no_experience"
        skills = []
    else:
        exp_year_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?|ವರ್ಷ|ವರ್ಷಗಳ|साल|वर्ष)\s*(?:of\s*)?(?:experience|exp|ಅನುಭವ|अनुभव)",
            clean,
            re.IGNORECASE
        )
        if exp_year_match:
            try:
                experience_years = float(exp_year_match.group(1))
            except ValueError:
                pass

        # Skill domains
        if any(k in lower or k in clean for k in ["farming", "agriculture", "cattle farming", "ಕೃಷಿ", "ಹೈನುಗಾರಿಕೆ", "ಹಸು ಸಾಕಾಣಿಕೆ", "ತೋಟಗಾರಿಕೆ", "खेती", "कृषि", "पशुपालन", "शेती"]):
            skills.append("Farming & Agricultural Operations")
        if any(k in lower or k in clean for k in ["dairy experience", "dairy work", "milking", "ಹಾಲು ಕರೆಯುವುದು", "ಡೈರಿ ಅನುಭವ", "ಹೈನುಗಾರಿಕೆ", "डेयरी अनुभव", "दूध का काम"]):
            if "Dairy Management & Cattle Care" not in skills:
                skills.append("Dairy Management & Cattle Care")
        if any(k in lower or k in clean for k in ["tailoring", "stitching", "sewing", "cutting", "selling clothes", "textile", "ಟೈಲರಿಂಗ್", "ಬಟ್ಟೆ ಹೊಲಿಯುವುದು", "ಸೀರೆ ವ್ಯಾಪಾರ", "सिलाई", "दर्जी", "कपड़े बेचना", "कापड विक्री"]):
            skills.append("Garment Tailoring & Textile Sales")
        if any(k in lower or k in clean for k in ["retail experience", "sales", "shop management", "selling", "ಮಾರಾಟ", "ಅಂಗಡಿ ನಡೆಸಿದ ಅನುಭವ", "दुकानदारी", "बिक्री", "सेल्स", "दुकान"]):
            if "Retail Sales & Customer Negotiation" not in skills:
                skills.append("Retail Sales & Customer Negotiation")
        if any(k in lower or k in clean for k in ["carpentry", "woodwork", "furniture", "ಮರಗೆಲಸ", "ಬಡಗಿ ಕೆಲಸ", "बढ़ई", "फर्नीचर"]):
            skills.append("Carpentry & Furniture Fabrication")
        if any(k in lower or k in clean for k in ["cooking", "catering", "baking", "food prep", "ಅಡುಗೆ", "ಕ್ಯಾಟರಿಂಗ್", "ತಿಂಡಿ ತಯಾರಿಕೆ", "खाना बनाना", "हलवाई"]):
            skills.append("Food Preparation & Catering")
        if any(k in lower or k in clean for k in ["mechanical work", "mobile repair", "electrical", "machine repair", "ರಿಪೇರಿ", "ಮೆಕ್ಯಾನಿಕಲ್", "ಮೆಕ್ಯಾನಿಕ್", "रिपेयरिंग", "मैकेनिक"]):
            skills.append("Equipment Servicing & Repair")
        if any(k in lower or k in clean for k in ["computer skills", "typing", "digital", "ಕಂಪ್ಯೂಟರ್", "कंप्यूटर", "संगणक"]):
            skills.append("Computer & Digital Literacy")

        if skills:
            skills_status = "collected"

    return BusinessEntityResult(
        business_concept=business_concept,
        business_category_hint=business_category_hint,
        intent=primary_intent,
        business_stage=business_stage,
        location=loc_obj,
        skills=skills,
        skills_status=skills_status,
        experience_years=experience_years,
        product_service=product_service,
        products=products
    )
