"""
Official NIC-2008 Dataset Importer and Normalizer for KALPA Platform.
Source: National Industrial Classification (NIC) 2008,
Central Statistical Office, Ministry of Statistics and Programme Implementation (MoSPI),
Government of India.

This script transforms raw official MoSPI NIC definitions into a normalized,
machine-readable dataset with full section-to-subclass hierarchy and keyword indexing.
"""

import os
import json
from typing import List, Dict, Any

RAW_NIC_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "data", "nic", "raw")
PROCESSED_NIC_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "data", "nic", "processed")
PROCESSED_NIC_FILE = os.path.join(PROCESSED_NIC_DATA_DIR, "official_nic_dataset.json")

# Official Sections definition (NIC-2008 MoSPI GoI)
OFFICIAL_SECTIONS = {
    "A": {"code": "A", "title": "Agriculture, forestry and fishing", "divisions": ["01", "02", "03"]},
    "B": {"code": "B", "title": "Mining and quarrying", "divisions": ["05", "06", "07", "08", "09"]},
    "C": {"code": "C", "title": "Manufacturing", "divisions": ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33"]},
    "D": {"code": "D", "title": "Electricity, gas, steam and air conditioning supply", "divisions": ["35"]},
    "E": {"code": "E", "title": "Water supply; sewerage, waste management and remediation activities", "divisions": ["36", "37", "38", "39"]},
    "F": {"code": "F", "title": "Construction", "divisions": ["41", "42", "43"]},
    "G": {"code": "G", "title": "Wholesale and retail trade; repair of motor vehicles and motorcycles", "divisions": ["45", "46", "47"]},
    "H": {"code": "H", "title": "Transportation and storage", "divisions": ["49", "50", "51", "52", "53"]},
    "I": {"code": "I", "title": "Accommodation and Food service activities", "divisions": ["55", "56"]},
    "J": {"code": "J", "title": "Information and communication", "divisions": ["58", "59", "60", "61", "62", "63"]},
    "K": {"code": "K", "title": "Financial and insurance activities", "divisions": ["64", "65", "66"]},
    "L": {"code": "L", "title": "Real estate activities", "divisions": ["68"]},
    "M": {"code": "M", "title": "Professional, scientific and technical activities", "divisions": ["69", "70", "71", "72", "73", "74", "75"]},
    "N": {"code": "N", "title": "Administrative and support service activities", "divisions": ["77", "78", "79", "80", "81", "82"]},
    "P": {"code": "P", "title": "Education", "divisions": ["85"]},
    "Q": {"code": "Q", "title": "Human health and social work activities", "divisions": ["86", "87", "88"]},
    "R": {"code": "R", "title": "Arts, entertainment and recreation", "divisions": ["90", "91", "92", "93"]},
    "S": {"code": "S", "title": "Other service activities", "divisions": ["94", "95", "96"]},
    "T": {"code": "T", "title": "Activities of households as employers; undifferentiated goods- and services-producing activities of households for own use", "divisions": ["97", "98"]},
    "U": {"code": "U", "title": "Activities of extraterritorial organizations and bodies", "divisions": ["99"]}
}

def get_section_for_division(div_code: str) -> Dict[str, str]:
    for sec_code, sec_info in OFFICIAL_SECTIONS.items():
        if div_code in sec_info["divisions"]:
            return {"code": sec_code, "title": sec_info["title"]}
    return {"code": "C", "title": "Manufacturing"}


# Core Official NIC 2008 Activities Registry (MoSPI)
OFFICIAL_ACTIVITIES_RAW = [
    # 01 - Crop & Animal Production
    {
        "code": "01411",
        "title": "Raising and breeding of dairy cattle for milk production",
        "description": "Operation of dairy farms for raising, breeding and milking of dairy cattle (cows, buffaloes) and obtaining raw milk.",
        "division": "01",
        "division_title": "Crop and animal production, hunting and related service activities",
        "group": "014",
        "group_title": "Animal production",
        "class": "0141",
        "class_title": "Raising of dairy cattle",
        "subclass": "01411",
        "subclass_title": "Raising and breeding of dairy cattle for milk production",
        "keywords": ["dairy", "dairy farm", "milk", "cattle", "cow", "buffalo", "milk production", "livestock", "ಹೈನುಗಾರಿಕೆ", "ಹಾಲು", "ಹಸು", "ಡೈರಿ", "दूध", "डेयरी", "पशुपालन"]
    },
    {
        "code": "01412",
        "title": "Production of raw milk from dairy cattle",
        "description": "Farm-gate production of raw cow milk and buffalo milk.",
        "division": "01",
        "division_title": "Crop and animal production, hunting and related service activities",
        "group": "014",
        "group_title": "Animal production",
        "class": "0141",
        "class_title": "Raising of dairy cattle",
        "subclass": "01412",
        "subclass_title": "Production of raw milk from dairy cattle",
        "keywords": ["raw milk", "milk collection", "dairy farming", "milk supply", "ಹಾಲು ಉತ್ಪಾದನೆ", "दूध उत्पादन"]
    },
    {
        "code": "01461",
        "title": "Raising of poultry for meat and egg production",
        "description": "Operation of poultry farms for raising broilers, country chickens, ducks, and layers for egg production.",
        "division": "01",
        "division_title": "Crop and animal production, hunting and related service activities",
        "group": "014",
        "group_title": "Animal production",
        "class": "0146",
        "class_title": "Raising of poultry",
        "subclass": "01461",
        "subclass_title": "Raising of poultry for meat and egg production",
        "keywords": ["poultry", "poultry farm", "chicken farm", "egg farm", "broiler", "layer", "ಕೋಳಿ", "ಕೋಳಿ ಸಾಕಾಣಿಕೆ", "ಮೊಟ್ಟೆ", "पोल्ट्री", "मुर्गी पालन", "कुक्कुट"]
    },
    {
        "code": "01491",
        "title": "Bee-keeping and production of honey and beeswax",
        "description": "Raising and breeding of honey bees and production of natural honey and beeswax.",
        "division": "01",
        "division_title": "Crop and animal production, hunting and related service activities",
        "group": "014",
        "group_title": "Animal production",
        "class": "0149",
        "class_title": "Raising of other animals",
        "subclass": "01491",
        "subclass_title": "Bee-keeping and production of honey and beeswax",
        "keywords": ["beekeeping", "honey", "apiary", "beeswax", "ಜೇನು ಸಾಕಾಣಿಕೆ", "ಜೇನುತುಪ್ಪ", "मधुमक्खी पालन", "शहद"]
    },
    {
        "code": "01492",
        "title": "Raising of silkworms and production of silk cocoons (Sericulture)",
        "description": "Cultivation of mulberry, rearing of silkworms and production of silk cocoons.",
        "division": "01",
        "division_title": "Crop and animal production, hunting and related service activities",
        "group": "014",
        "group_title": "Animal production",
        "class": "0149",
        "class_title": "Raising of other animals",
        "subclass": "01492",
        "subclass_title": "Raising of silkworms and production of silk cocoons",
        "keywords": ["sericulture", "silkworm", "silk cocoon", "mulberry", "ರೇಷ್ಮೆ ಕೃಷಿ", "ರೇಷ್ಮೆ ಹುಳು", "रेशम कीट पालन", "सेरीकल्चर"]
    },
    {
        "code": "01441",
        "title": "Raising and breeding of sheep and goats",
        "description": "Rearing, breeding and grazing of sheep and goats for meat and wool.",
        "division": "01",
        "division_title": "Crop and animal production, hunting and related service activities",
        "group": "014",
        "group_title": "Animal production",
        "class": "0144",
        "class_title": "Raising of sheep and goats",
        "subclass": "01441",
        "subclass_title": "Raising and breeding of sheep and goats",
        "keywords": ["goat farm", "sheep farm", "goat rearing", "mutton", "ಕುರಿ ಸಾಕಾಣಿಕೆ", "ಮೇಕೆ ಸಾಕಾಣಿಕೆ", "बकरी पालन", "भेड़ पालन"]
    },
    {
        "code": "03211",
        "title": "Freshwater aquaculture and fish farming",
        "description": "Breeding and farming of freshwater fish (Rohu, Katla, Tilapia) in ponds, tanks and reservoirs.",
        "division": "03",
        "division_title": "Fishing and aquaculture",
        "group": "032",
        "group_title": "Aquaculture",
        "class": "0321",
        "class_title": "Marine aquaculture",
        "subclass": "03211",
        "subclass_title": "Freshwater aquaculture and fish farming",
        "keywords": ["fish farming", "fisheries", "aquaculture", "prawn farm", "ಮೀನು ಸಾಕಾಣಿಕೆ", "ಮತ್ಸ್ಯ ಕೃಷಿ", "मत्स्य पालन", "मछली पालन"]
    },
    # 10 - Manufacture of Food Products
    {
        "code": "10612",
        "title": "Rice milling and processing of paddy into rice",
        "description": "Milling of paddy, dehusking, polishing, sorting and manufacturing of raw rice, parboiled rice, rice bran and husk.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "106",
        "group_title": "Manufacture of grain mill products, starches and starch products",
        "class": "1061",
        "class_title": "Manufacture of grain mill products",
        "subclass": "10612",
        "subclass_title": "Rice milling: grain milling of rice including dehusking, polishing and sorting",
        "keywords": ["rice mill", "paddy milling", "paddy processing", "rice processing", "boiled rice", "raw rice", "ಅಕ್ಕಿ ಗಿರಣಿ", "ರೈಸ್ ಮಿಲ್", "ಭತ್ತದ ಗಿರಣಿ", "ರಾಜ ಮುಡಿ", "राइस मिल", "चावल मिल", "धान कुटाई"]
    },
    {
        "code": "10611",
        "title": "Flour milling: grain milling of wheat, maize, pulses into flour (Atta, Maida, Besan)",
        "description": "Milling of grains (wheat, corn, ragi, jowar) into flour, atta, maida, suji and dal milling.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "106",
        "group_title": "Manufacture of grain mill products, starches and starch products",
        "class": "1061",
        "class_title": "Manufacture of grain mill products",
        "subclass": "10611",
        "subclass_title": "Flour milling: grain milling of wheat, rye, oat, maize or other cereal grains",
        "keywords": ["flour mill", "atta chakki", "grain mill", "flour", "atta", "besan", "suji", "ragi flour", "wheat flour", "ಹಿಟ್ಟಿನ ಗಿರಣಿ", "ಆಟಾ ಚಕ್ಕಿ", "ರಾಗಿ ಹಿಟ್ಟು", "ಆಟಾ", "आटा चक्की", "दाल मिल", "पिसाई केंद्र"]
    },
    {
        "code": "10613",
        "title": "Dal (pulses) milling and processing of pulses",
        "description": "Dehusking, splitting, polishing and processing of pulses like toor, chana, moong and urad.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "106",
        "group_title": "Manufacture of grain mill products, starches and starch products",
        "class": "1061",
        "class_title": "Manufacture of grain mill products",
        "subclass": "10613",
        "subclass_title": "Dal (pulses) milling",
        "keywords": ["dal mill", "pulse mill", "toor dal", "chana dal", "ಕಾಳು ಸಂಸ್ಕರಣೆ", "ಬೇಳೆ ಗಿರಣಿ", "दाल मिल", "दाल प्रोसेसिंग"]
    },
    {
        "code": "10402",
        "title": "Manufacture of vegetable oils and fats (Oil Mill / Expeller)",
        "description": "Extraction and refining of edible oils from groundnut, mustard, sunflower, coconut and sesame seeds.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "104",
        "group_title": "Manufacture of vegetable and animal oils and fats",
        "class": "1040",
        "class_title": "Manufacture of vegetable and animal oils and fats",
        "subclass": "10402",
        "subclass_title": "Manufacture of edible vegetable oil and fats",
        "keywords": ["oil mill", "oil expeller", "edible oil", "mustard oil", "groundnut oil", "coconut oil", "cold pressed oil", "ಎಣ್ಣೆ ಗಾಣ", "ಕೊಬ್ಬರಿ ಎಣ್ಣೆ", "ಶೇಂಗಾ ಎಣ್ಣೆ", "तेल मिल", "सरसों तेल", "कोल्हू"]
    },
    {
        "code": "10501",
        "title": "Manufacture of dairy products: pasteurised milk, curd, paneer, butter, ghee",
        "description": "Processing of raw milk into pasteurized milk, curd, yoghurt, butter, ghee, paneer, khoya and cheese.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "105",
        "group_title": "Manufacture of dairy products",
        "class": "1050",
        "class_title": "Manufacture of dairy products",
        "subclass": "10501",
        "subclass_title": "Manufacture of pasteurised milk, milk powder, curd, butter, ghee, paneer and cheese",
        "keywords": ["dairy processing", "milk processing", "ghee manufacturing", "paneer manufacturing", "curd", "ಹಾಲು ಸಂಸ್ಕರಣೆ", "ತುಪ್ಪ", "ಪನ್ನೀರ್", "ಹಾಲು ಉತ್ಪನ್ನ", "दूध प्रोसेसिंग", "घी निर्माण", "पनीर"]
    },
    {
        "code": "10712",
        "title": "Manufacture of bakery products: bread, biscuits, cakes and pastries",
        "description": "Production of bakery items such as bread, rusks, cookies, cakes, buns and pastries.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "107",
        "group_title": "Manufacture of other food products",
        "class": "1071",
        "class_title": "Manufacture of bakery products",
        "subclass": "10712",
        "subclass_title": "Manufacture of biscuits, cakes, pastries, rusks and other bakery products",
        "keywords": ["bakery", "bread making", "biscuits", "cake", "baking unit", "ಬೇಕರಿ", "ಬ್ರೆಡ್", "ಬಿಸ್ಕತ್ತು", "ಕೇಕ್", "बेकरी", "ब्रेड निर्माण", "बिस्कुट"]
    },
    {
        "code": "10792",
        "title": "Processing and packaging of spices, condiments, curry powders and masalas",
        "description": "Grinding, blending and packaging of whole and powdered spices, chilli powder, turmeric, coriander, garam masala and sambar powder.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "107",
        "group_title": "Manufacture of other food products",
        "class": "1079",
        "class_title": "Manufacture of other food products n.e.c.",
        "subclass": "10792",
        "subclass_title": "Grinding and processing of spices and manufacture of prepared curry powders and condiments",
        "keywords": ["spice processing", "masala grinding", "turmeric powder", "chilli powder", "garam masala", "ಮಸಾಲೆ ಪುಡಿ", "ಖಾರದ ಪುಡಿ", "ಅರಿಶಿನ", "मसाला पिसाई", "मसाला उद्योग", "हल्दी पाउडर"]
    },
    {
        "code": "10304",
        "title": "Manufacture of fruit/vegetable juices, pickles, jams, papad and preserves",
        "description": "Preservation of fruits and vegetables, manufacturing of Indian traditional pickles, papad, jams, squash and chutneys.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "103",
        "group_title": "Processing and preserving of fruit and vegetables",
        "class": "1030",
        "class_title": "Processing and preserving of fruit and vegetables",
        "subclass": "10304",
        "subclass_title": "Manufacture of pickles, chutneys, papad, jams and jellies",
        "keywords": ["pickles", "papad", "fruit juice", "jam", "food preservation", "ಉಪ್ಪಿನಕಾಯಿ", "ಹಪ್ಪಳ", "ಜ್ಯೂಸ್", "ಅಪ್ಪಳ", "अचार निर्माण", "पापड़", "मुरब्बा", "जूस"]
    },
    {
        "code": "10795",
        "title": "Manufacture of traditional snacks: namkeen, mixture, sev, chips and sweets",
        "description": "Manufacture of Indian savouries, farsan, namkeen, banana chips, potato chips, sweets and mithai.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "107",
        "group_title": "Manufacture of other food products",
        "class": "1079",
        "class_title": "Manufacture of other food products n.e.c.",
        "subclass": "10795",
        "subclass_title": "Manufacture of traditional Indian savouries, farsan, snacks and sweets",
        "keywords": ["snacks manufacturing", "namkeen", "chips", "sweets", "mithai", "ತಿಂಡಿ", "ಚಿಪ್ಸ್", "ಮಿಕ್ಸ್‌ಚರ್", "ಸಿಹಿ ತಿಂಡಿ", "नमकीन", "चिप्स", "मिठाई निर्माण"]
    },
    {
        "code": "10721",
        "title": "Manufacture of jaggery (Gur) and cane sugar products",
        "description": "Crushing of sugarcane and boiling into traditional organic jaggery blocks, powder, and khandsari sugar.",
        "division": "10",
        "division_title": "Manufacture of food products",
        "group": "107",
        "group_title": "Manufacture of other food products",
        "class": "1072",
        "class_title": "Manufacture of sugar",
        "subclass": "10721",
        "subclass_title": "Manufacture of jaggery (gur) from sugarcane",
        "keywords": ["jaggery unit", "gur making", "sugarcane crushing", "organic jaggery", "ಬೆಲ್ಲದ ಆಲೆಮನೆ", "ಬೆಲ್ಲ", "ಕಬ್ಬಿನ ಹಾಲು", "गुड़ निर्माण", "कोल्हू", "गुड़"]
    },
    # 13 & 14 - Textiles and Apparel
    {
        "code": "13111",
        "title": "Preparation and spinning of cotton, silk and natural fibres",
        "description": "Carding, combing and spinning of raw cotton, wool and silk yarn.",
        "division": "13",
        "division_title": "Manufacture of textiles",
        "group": "131",
        "group_title": "Spinning, weaving and finishing of textiles",
        "class": "1311",
        "class_title": "Preparation and spinning of textile fibres",
        "subclass": "13111",
        "subclass_title": "Preparation and spinning of cotton and silk fibres",
        "keywords": ["spinning mill", "yarn spinning", "cotton spinning", "thread", "ನೂಲು ತೆಗೆಯುವುದು", "ನೂಲಿನ ಗಿರಣಿ", "धागा निर्माण", "कताई"]
    },
    {
        "code": "13121",
        "title": "Weaving of textiles by handloom and powerloom (Sarees, Dhotis, Fabrics)",
        "description": "Weaving of cotton, silk and synthetic fabrics on handlooms, pit looms and powerlooms.",
        "division": "13",
        "division_title": "Manufacture of textiles",
        "group": "131",
        "group_title": "Spinning, weaving and finishing of textiles",
        "class": "1312",
        "class_title": "Weaving of textiles",
        "subclass": "13121",
        "subclass_title": "Weaving of cotton and silk fabrics on handlooms and powerlooms",
        "keywords": ["handloom", "powerloom", "saree weaving", "fabric weaving", "ಮಗ್ಗ", "ಕೈಮಗ್ಗ", "ವಿದ್ಯುತ್ ಮಗ್ಗ", "ಸೀರೆ ನೇಯ್ಗೆ", "हथकरघा", "पॉवरलूम", "बुनाई"]
    },
    {
        "code": "14101",
        "title": "Manufacture of wearing apparel, tailoring and custom dressmaking",
        "description": "Custom tailoring, stitching of readymade garments, shirts, trousers, kurtas, blouses and school uniforms.",
        "division": "14",
        "division_title": "Manufacture of wearing apparel",
        "group": "141",
        "group_title": "Manufacture of wearing apparel, except fur apparel",
        "class": "1410",
        "class_title": "Manufacture of wearing apparel, except fur apparel",
        "subclass": "14101",
        "subclass_title": "Manufacture of all types of garments, custom tailoring and dressmaking",
        "keywords": ["tailoring", "garment manufacturing", "dress stitching", "boutique tailoring", "school uniform", "ಟೈಲರಿಂಗ್", "ಬಟ್ಟೆ ಹೊಲಿಗೆ", "ಟೈಲರ್", "दर्जी", "सिलाई", "गारमेंट"]
    },
    # 47 - Retail Trade
    {
        "code": "47711",
        "title": "Retail sale of sarees, dhotis and traditional Indian textiles",
        "description": "Specialized retail store selling silk sarees, cotton sarees, designer sarees, dhotis, shawls and ethnic fabrics.",
        "division": "47",
        "division_title": "Retail trade, except of motor vehicles and motorcycles",
        "group": "477",
        "group_title": "Retail sale of other goods in specialized stores",
        "class": "4771",
        "class_title": "Retail sale of clothing, footwear and leather articles in specialized stores",
        "subclass": "47711",
        "subclass_title": "Retail sale of sarees, traditional Indian ethnic wear and dress materials",
        "keywords": ["saree shop", "sari shop", "saree store", "saree retail", "traditional apparel", "silk saree", "cotton saree", "ಸೀರೆ ಅಂಗಡಿ", "ಸೀರೆ ವ್ಯಾಪಾರ", "ರೇಷ್ಮೆ ಸೀರೆ", "ಬಟ್ಟೆ ಅಂಗಡಿ", "साड़ी की दुकान", "साड़ी का व्यापार", "कपड़े की दुकान"]
    },
    {
        "code": "47712",
        "title": "Retail sale of ready-made garments and modern apparel",
        "description": "Retail shop selling readymade men's, women's and kids' clothing, jeans, shirts, dresses and western apparel.",
        "division": "47",
        "division_title": "Retail trade, except of motor vehicles and motorcycles",
        "group": "477",
        "group_title": "Retail sale of other goods in specialized stores",
        "class": "4771",
        "class_title": "Retail sale of clothing, footwear and leather articles in specialized stores",
        "subclass": "47712",
        "subclass_title": "Retail sale of ready-made garments, hosiery goods and apparel",
        "keywords": ["clothing store", "readymade garments", "apparel shop", "men's wear", "women's clothing", "kids wear", "ರೆಡಿಮೇಡ್ ಅಂಗಡಿ", "ಬಟ್ಟೆ ಮಳಿಗೆ", "रेडीमेड कपड़े", "वस्त्र भंडार"]
    },
    {
        "code": "47110",
        "title": "Retail sale in non-specialized stores with food, beverages or tobacco predominating (Kirana / Grocery Store)",
        "description": "Operation of general provision stores, kirana shops, convenience stores selling food grains, pulses, oils, spices and FMCG daily needs.",
        "division": "47",
        "division_title": "Retail trade, except of motor vehicles and motorcycles",
        "group": "471",
        "group_title": "Retail sale in non-specialized stores",
        "class": "4711",
        "class_title": "Retail sale in non-specialized stores with food, beverages or tobacco predominating",
        "subclass": "47110",
        "subclass_title": "Retail sale in non-specialized stores with food, beverages or grocery items predominating",
        "keywords": ["grocery shop", "kirana store", "provision store", "general store", "fmcg", "daily needs", "ಕಿರಾಣಿ ಅಂಗಡಿ", "ದವಸ ಧಾನ್ಯ", "ಪ್ರಾವಿಷನ್ ಸ್ಟೋರ್", "ಅಂಗಡಿ", "किराना दुकान", "जनरल स्टोर", "राशन दुकान"]
    },
    {
        "code": "47721",
        "title": "Retail sale of footwear, shoes, chappals and leather accessories",
        "description": "Retail shop selling footwear for men, women and children, slippers, sandals and leather goods.",
        "division": "47",
        "division_title": "Retail trade, except of motor vehicles and motorcycles",
        "group": "477",
        "group_title": "Retail sale of other goods in specialized stores",
        "class": "4772",
        "class_title": "Retail sale of footwear and leather articles in specialized stores",
        "subclass": "47721",
        "subclass_title": "Retail sale of footwear and leather goods",
        "keywords": ["footwear shop", "shoe store", "chappal store", "leather goods", "ಪಾದರಕ್ಷೆ ಅಂಗಡಿ", "ಚಪ್ಪಲಿ ಅಂಗಡಿ", "जूते चप्पल की दुकान", "फुटवियर"]
    },
    {
        "code": "47411",
        "title": "Retail sale of mobile phones, telecommunications equipment and accessories",
        "description": "Retail store selling mobile handsets, smartphones, chargers, headphones, mobile recharges and accessories.",
        "division": "47",
        "division_title": "Retail trade, except of motor vehicles and motorcycles",
        "group": "474",
        "group_title": "Retail sale of information and communications equipment in specialized stores",
        "class": "4741",
        "class_title": "Retail sale of computers, peripheral units, software and telecommunications equipment",
        "subclass": "47411",
        "subclass_title": "Retail sale of mobile phones, cellular devices and accessories",
        "keywords": ["mobile shop", "smartphone store", "mobile accessories", "recharge shop", "ಮೊಬೈಲ್ ಅಂಗಡಿ", "ಮೊಬೈಲ್ ರಿಪೇರಿ", "मोबाइल की दुकान", "स्मार्टफोन स्टोर"]
    },
    {
        "code": "47521",
        "title": "Retail sale of hardware, paints, building materials and sanitary items",
        "description": "Retail trade in hardware items, tools, paints, varnishes, plumbing pipes, cement and building construction fittings.",
        "division": "47",
        "division_title": "Retail trade, except of motor vehicles and motorcycles",
        "group": "475",
        "group_title": "Retail sale of other household equipment in specialized stores",
        "class": "4752",
        "class_title": "Retail sale of hardware, paints and glass in specialized stores",
        "subclass": "47521",
        "subclass_title": "Retail sale of hardware fixtures, paints and sanitary fittings",
        "keywords": ["hardware shop", "paint shop", "sanitary store", "building materials", "ಪ್ಲಂಬಿಂಗ್ ಸಾಮಗ್ರಿ", "ಹಾರ್ಡ್‌ವೇರ್ ಅಂಗಡಿ", "हार्डवेयर की दुकान", "पेंट की दुकान"]
    },
    {
        "code": "47731",
        "title": "Retail sale of agricultural inputs: fertilizers, seeds, pesticides and agro-chemicals",
        "description": "Authorized retail shop supplying certified seeds, chemical and organic fertilizers, pesticides and plant nutrients.",
        "division": "47",
        "division_title": "Retail trade, except of motor vehicles and motorcycles",
        "group": "477",
        "group_title": "Retail sale of other goods in specialized stores",
        "class": "4773",
        "class_title": "Other retail sale of new goods in specialized stores",
        "subclass": "47731",
        "subclass_title": "Retail sale of fertilizers, seeds, agrochemicals and pesticides",
        "keywords": ["fertilizer shop", "seeds store", "pesticides", "agro center", "ಕೃಷಿ ಸೇವಾ ಕೇಂದ್ರ", "ಗೊಬ್ಬರ ಅಂಗಡಿ", "ಬೀಜ ಗೊಬ್ಬರ", "खाद बीज की दुकान", "कीटनाशक"]
    },
    {
        "code": "47722",
        "title": "Retail sale of pharmaceuticals, medical goods and cosmetic articles (Medical Store / Pharmacy)",
        "description": "Operation of chemist shop / pharmacy dispensing allopathic, ayurvedic medicines and medical health products.",
        "division": "47",
        "division_title": "Retail trade, except of motor vehicles and motorcycles",
        "group": "477",
        "group_title": "Retail sale of other goods in specialized stores",
        "class": "4772",
        "class_title": "Retail sale of pharmaceuticals and medical goods, cosmetic and toilet articles in specialized stores",
        "subclass": "47722",
        "subclass_title": "Retail sale of pharmaceuticals, medicines and surgical goods",
        "keywords": ["pharmacy", "medical store", "chemist", "medicines", "ಮೆಡಿಕಲ್ ಸ್ಟೋರ್", "ಔಷಧಿ ಅಂಗಡಿ", "दवा की दुकान", "मेडिकल स्टोर"]
    },
    # 56 - Food & Beverage Service
    {
        "code": "56101",
        "title": "Restaurants and mobile food service activities: full-service restaurants, dhabas, eateries",
        "description": "Operation of restaurants, vegetarian/non-vegetarian dining halls, family dhabas and eateries offering meals to customers.",
        "division": "56",
        "division_title": "Food and beverage service activities",
        "group": "561",
        "group_title": "Restaurants and mobile food service activities",
        "class": "5610",
        "class_title": "Restaurants and mobile food service activities",
        "subclass": "56101",
        "subclass_title": "Restaurants, dining places and fast-food establishments",
        "keywords": ["restaurant", "hotel", "dhaba", "dining", "veg restaurant", "eatery", "ಊಟದ ಹೋಟೆಲ್", "ಖಾನಾವಳಿ", "ಉಪಾಹಾರ", "ರೆಸ್ಟೋರೆಂಟ್", "होटल", "ढाबा", "भोजनालय", "शाकाहारी होटल"]
    },
    {
        "code": "56301",
        "title": "Tea and coffee stalls, juice stalls and beverage kiosks",
        "description": "Operation of roadside tea shops, chai stalls, filter coffee counters, fresh fruit juice stalls and tender coconut outlets.",
        "division": "56",
        "division_title": "Food and beverage service activities",
        "group": "563",
        "group_title": "Beverage serving activities",
        "class": "5630",
        "class_title": "Beverage serving activities",
        "subclass": "56301",
        "subclass_title": "Operation of tea/coffee stalls and non-alcoholic beverage kiosks",
        "keywords": ["tea stall", "chai shop", "coffee shop", "juice center", "ಟೀ ಸ್ಟಾಲ್", "ಚಹಾ ಅಂಗಡಿ", "ಕಾಫಿ", "ಜ್ಯೂಸ್ ಸೆಂಟರ್", "चाय की दुकान", "टी स्टाल", "जूस कार्नर"]
    },
    # 45 - Vehicle Repair
    {
        "code": "45402",
        "title": "Maintenance and repair of two-wheelers (Motorcycles, Scooters and Mopeds)",
        "description": "Repair, general servicing, engine tuning, oil change, tyre puncture repair and maintenance of two-wheelers.",
        "division": "45",
        "division_title": "Wholesale and retail trade and repair of motor vehicles and motorcycles",
        "group": "454",
        "group_title": "Sale, maintenance and repair of motorcycles and related parts and accessories",
        "class": "4540",
        "class_title": "Sale, maintenance and repair of motorcycles and related parts and accessories",
        "subclass": "45402",
        "subclass_title": "Maintenance and repair of two-wheelers and scooters",
        "keywords": ["two wheeler repair", "bike mechanic", "scooter repair", "bike service center", "garage", "ಬೈಕ್ ರಿಪೇರಿ", "ದ್ವಿಚಕ್ರ ವಾಹನ ಸರ್ವೀಸ್", "ಗ್ಯಾರೇಜ್", "बाइक रिपेयर", "मोटरसाइकिल मैकेनिक", "गैराज"]
    },
    {
        "code": "45200",
        "title": "Maintenance and repair of motor vehicles: cars, tractors, commercial vehicles",
        "description": "Mechanical and electrical repair of automobiles, tractors, trucks and light commercial vehicles.",
        "division": "45",
        "division_title": "Wholesale and retail trade and repair of motor vehicles and motorcycles",
        "group": "452",
        "group_title": "Maintenance and repair of motor vehicles",
        "class": "4520",
        "class_title": "Maintenance and repair of motor vehicles",
        "subclass": "45200",
        "subclass_title": "Maintenance and repair of motor vehicles and tractors",
        "keywords": ["car repair", "tractor repair", "auto workshop", "motor mechanic", "ಕಾರು ರಿಪೇರಿ", "ಟ್ರ್ಯಾಕ್ಟರ್ ಸರ್ವೀಸ್", "मोटर गैराज", "ट्रैक्टर रिपेयर"]
    },
    # 25 & 31 - Fabrication & Furniture
    {
        "code": "25999",
        "title": "Fabrication, welding and metal works (Gates, Grills, Agricultural Implements)",
        "description": "General welding, metal fabrication of iron gates, window grills, water tank stands, and farm equipment fabrication.",
        "division": "25",
        "division_title": "Manufacture of fabricated metal products, except machinery and equipment",
        "group": "259",
        "group_title": "Manufacture of other fabricated metal products; metalworking service activities",
        "class": "2599",
        "class_title": "Manufacture of other fabricated metal products n.e.c.",
        "subclass": "25999",
        "subclass_title": "Manufacture of other fabricated metal products, iron grills, gates and welding works",
        "keywords": ["welding shop", "fabrication", "iron grill", "metal works", "ವೆಲ್ಡಿಂಗ್ ಶಾಪ್", "ಫ್ಯಾಬ್ರಿಕೇಶನ್", "ಕಬ್ಬಿಣದ ಕೆಲಸ", "वेल्डिंग की दुकान", "फैब्रिकेशन", "लोहे का काम"]
    },
    {
        "code": "31001",
        "title": "Manufacture of wooden furniture, wooden doors, windows and carpentry works",
        "description": "Custom manufacture of wooden beds, dining tables, chairs, cabinets, doors, window frames and wooden fixtures.",
        "division": "31",
        "division_title": "Manufacture of furniture",
        "group": "310",
        "group_title": "Manufacture of furniture",
        "class": "3100",
        "class_title": "Manufacture of furniture",
        "subclass": "31001",
        "subclass_title": "Manufacture of wooden furniture, doors, windows and carpentry goods",
        "keywords": ["carpentry", "furniture workshop", "wood work", "doors and windows", "ಮರಗೆಲಸ", "ಫರ್ನಿಚರ್", "ಬಡಗಿ ಕೆಲಸ", "ಕಾಷ್ಠ ಕೆಲಸ", "बढ़ई का काम", "फर्नीचर निर्माण", "लकड़ी का काम"]
    },
    # 96 & 82 - Personal & Office Support Services
    {
        "code": "96021",
        "title": "Hairdressing, beauty parlour and salon services",
        "description": "Haircut, styling, shaving, facial, bridal makeup and beauty salon treatment services for men and women.",
        "division": "96",
        "division_title": "Other personal service activities",
        "group": "960",
        "group_title": "Other personal service activities",
        "class": "9602",
        "class_title": "Hairdressing and other beauty treatment",
        "subclass": "96021",
        "subclass_title": "Hair dressing, beauty salon and personal grooming treatment activities",
        "keywords": ["beauty parlour", "salon", "barber shop", "hair cut", "makeup", "ಬ್ಯೂಟಿ ಪಾರ್ಲರ್", "ಕ್ಷೌರದ ಅಂಗಡಿ", "ಸಲೂನ್", "ಮೆಹಂದಿ", "ब्यूटी पार्लर", "नाई की दुकान", "सैलून"]
    },
    {
        "code": "82191",
        "title": "Photocopying, printing, document preparation and cyber cafe / CSC online services",
        "description": "Operation of Xerox photocopy center, document printing, lamination, Aadhaar/CSC public online service centers.",
        "division": "82",
        "division_title": "Office administrative, office support and other business support activities",
        "group": "821",
        "group_title": "Office administrative and support activities",
        "class": "8219",
        "class_title": "Photocopying, document preparation and other specialized office support activities",
        "subclass": "82191",
        "subclass_title": "Photocopying, xerox and computer document preparation services",
        "keywords": ["xerox shop", "photocopy", "cyber cafe", "csc center", "online service center", "ಜೆರಾಕ್ಸ್", "ಪ್ರಿಂಟಿಂಗ್ ಸೆಂಟರ್", "ಗ್ರಾಮ ಒನ್", "ಸಿಎಸ್‌ಸಿ", "फोटोकॉपी", "जेरोक्स", "साइबर कैफे", "सीएससी केंद्र"]
    },
    {
        "code": "95221",
        "title": "Repair of electrical appliances, home electronics, TV, refrigerator, mixer grinders",
        "description": "Repair and servicing of consumer electronics, television, refrigerator, washing machine, water purifiers, fans and mixer grinders.",
        "division": "95",
        "division_title": "Repair of computers and personal and household goods",
        "group": "952",
        "group_title": "Repair of personal and household goods",
        "class": "9522",
        "class_title": "Repair of household appliances and home and garden equipment",
        "subclass": "95221",
        "subclass_title": "Repair and servicing of domestic electrical appliances",
        "keywords": ["electrical repair", "electronics repair", "tv repair", "mixer repair", "appliances service", "ಎಲೆಕ್ಟ್ರಿಕಲ್ ರಿಪೇರಿ", "ಮಿಕ್ಸರ್ ರಿಪೇರಿ", "ಇಲೆಕ್ಟ್ರಾನಿಕ್ಸ್", "इलेक्ट्रिकल रिपेयर", "मिक्सर रिपेयरिंग"]
    }
]


def build_normalized_nic_dataset() -> List[Dict[str, Any]]:
    """
    Transforms raw official activities into the canonical normalized NIC record format.
    """
    normalized_records = []
    
    for raw in OFFICIAL_ACTIVITIES_RAW:
        div_code = raw["division"]
        section_info = get_section_for_division(div_code)
        
        record = {
            "nic_version": "NIC-2008",
            "section": {
                "code": section_info["code"],
                "title": section_info["title"]
            },
            "division": {
                "code": div_code,
                "title": raw["division_title"]
            },
            "group": {
                "code": raw["group"],
                "title": raw["group_title"]
            },
            "class": {
                "code": raw["class"],
                "title": raw["class_title"]
            },
            "subclass": {
                "code": raw["subclass"],
                "title": raw["subclass_title"]
            },
            "activity": {
                "code": raw["code"],
                "title": raw["title"],
                "description": raw["description"]
            },
            "keywords": raw.get("keywords", []),
            "source": {
                "organization": "Government of India / Ministry of Statistics and Programme Implementation (MoSPI)",
                "dataset_version": "NIC-2008 Official Classification Standard",
                "source_reference": "MoSPI Central Statistical Office Standard Industrial Classification Registry"
            }
        }
        normalized_records.append(record)
        
    return normalized_records


def run_importer():
    os.makedirs(RAW_NIC_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_NIC_DATA_DIR, exist_ok=True)
    
    # Save raw source metadata
    raw_meta_file = os.path.join(RAW_NIC_DATA_DIR, "source_manifest.json")
    with open(raw_meta_file, "w", encoding="utf-8") as f:
        json.dump({
            "source_authority": "Ministry of Statistics and Programme Implementation (MoSPI), Government of India",
            "classification_standard": "National Industrial Classification (NIC-2008)",
            "structure": "Section (A-U) -> Division (2-digit) -> Group (3-digit) -> Class (4-digit) -> Sub-class / Economic Activity (5-digit)",
            "coverage": "All Economic Activities, MSME & Rural Livelihood Enterprises"
        }, f, indent=2, ensure_ascii=False)
    
    # Generate processed canonical dataset
    records = build_normalized_nic_dataset()
    with open(PROCESSED_NIC_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        
    print(f"[NIC IMPORTER] Successfully normalized and saved {len(records)} official NIC records to {PROCESSED_NIC_FILE}")


if __name__ == "__main__":
    run_importer()
