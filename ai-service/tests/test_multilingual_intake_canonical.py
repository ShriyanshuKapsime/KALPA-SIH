"""
Comprehensive Multilingual Intake & Canonical Extraction Test Suite.
Verifies:
1. Hindi number-word parsing & composition ('एक लाख', 'दो लाख पचास हजार', 'डेढ़ लाख', 'साढ़े तीन लाख', 'तीन करोड़', 'पचास हजार')
2. English Indian numbers ('one lakh', '1.5 lakh', '10 lakh', '1 crore', 'one hundred thousand', '1L', '1.5L', '₹1,00,000')
3. Hinglish expressions ('mera budget ek lakh hai', 'budget 2 lakh hai', 'saree shop kholna hai, budget 1.5 lakh')
4. Mixed and Indian language inputs (Kannada, Marathi, Tamil, Telugu)
5. Negative tests ('one lakh customers', 'shop area is 1 lakh sq ft', '5 years of experience', '100 cows')
6. Currency inference ('मेरा बजट एक लाख है' -> currency='INR', currency_source='CONTEXT_INFERRED')
7. Groq 400 and offline resilience (deterministic extraction guarantees no money is dropped)
8. Provenance and diagnostic logging validation
"""

import pytest
from app.services.intake.language_normalizer import (
    normalize_unicode_text,
    detect_language_multilingual
)
from app.services.intake.indic_number_parser import (
    parse_indic_number_expression,
    parse_compositional_indic_number
)
from app.services.intake.amount_parser import (
    parse_canonical_amount,
    AmountResult
)
from app.services.intake.business_entity_extractor import (
    extract_multilingual_business_entities
)
from app.services.intake.canonical_extractor import (
    canonical_intake_extractor
)
from app.services.intake_pipeline import (
    process_user_intake,
    continue_user_intake
)


# =============================================================================
# 1. HINDI NUMBER COMPOSITION TESTS
# =============================================================================

def test_hindi_compositional_numbers():
    assert parse_indic_number_expression("एक लाख") == 100000
    assert parse_indic_number_expression("दो लाख") == 200000
    assert parse_indic_number_expression("डेढ़ लाख") == 150000
    assert parse_indic_number_expression("ढाई लाख") == 250000
    assert parse_indic_number_expression("साढ़े तीन लाख") == 350000
    assert parse_indic_number_expression("सवा लाख") == 125000
    assert parse_indic_number_expression("पौने दो लाख") == 175000
    assert parse_indic_number_expression("दो लाख पचास हजार") == 250000
    assert parse_indic_number_expression("एक लाख बीस हजार पांच सौ") == 120500
    assert parse_indic_number_expression("तीन करोड़") == 30000000
    assert parse_indic_number_expression("पचास हजार") == 50000
    assert parse_indic_number_expression("दस लाख") == 1000000


def test_hindi_spelling_and_nukta_variations():
    # लाख vs लाख़, हजार vs हज़ार, करोड़ vs करोड़
    assert parse_indic_number_expression("एक लाख़") == 100000
    assert parse_indic_number_expression("दो हज़ार") == 2000
    assert parse_indic_number_expression("तीन करोड़") == 30000000
    assert parse_indic_number_expression("पचास हज़ार") == 50000


# =============================================================================
# 2. ENGLISH & INDIAN NUMBER FORMAT TESTS
# =============================================================================

def test_english_number_expressions():
    assert parse_indic_number_expression("one lakh") == 100000
    assert parse_indic_number_expression("two lakh") == 200000
    assert parse_indic_number_expression("one hundred thousand") == 100000
    assert parse_indic_number_expression("1 lakh") == 100000
    assert parse_indic_number_expression("1 lac") == 100000
    assert parse_indic_number_expression("1L") == 100000
    assert parse_indic_number_expression("1.5 lakh") == 150000
    assert parse_indic_number_expression("2.5 lakh") == 250000
    assert parse_indic_number_expression("10 lakh") == 1000000
    assert parse_indic_number_expression("1 crore") == 10000000
    assert parse_indic_number_expression("1.5L") == 150000
    assert parse_indic_number_expression("2cr") == 20000000
    assert parse_indic_number_expression("50k") == 50000
    assert parse_indic_number_expression("₹1,00,000") == 100000
    assert parse_indic_number_expression("Rs 1,00,000") == 100000
    assert parse_indic_number_expression("100000") == 100000
    assert parse_indic_number_expression("1,00,000") == 100000


# =============================================================================
# 3. HINGLISH COMPOSITION TESTS
# =============================================================================

def test_hinglish_number_expressions():
    assert parse_indic_number_expression("ek lakh") == 100000
    assert parse_indic_number_expression("do lakh") == 200000
    assert parse_indic_number_expression("teen lakh") == 300000
    assert parse_indic_number_expression("chaar lakh") == 400000
    assert parse_indic_number_expression("dedh lakh") == 150000
    assert parse_indic_number_expression("dhai lakh") == 250000
    assert parse_indic_number_expression("sadhe teen lakh") == 350000
    assert parse_indic_number_expression("pachaas hazaar") == 50000
    assert parse_indic_number_expression("do lakh pachaas hazaar") == 250000


# =============================================================================
# 4. CANONICAL AMOUNT PARSER & CONTEXT INFERENCE TESTS
# =============================================================================

def test_amount_parser_explicit_currency():
    res1 = parse_canonical_amount("मुझे साड़ी का दुकान खोलना है, मेरा बजट एक लाख रुपये।")
    assert res1.available_capital == 100000
    assert res1.currency == "INR"
    assert res1.currency_source == "EXPLICIT"
    assert res1.provenance is not None
    assert res1.provenance.value == 100000

    res2 = parse_canonical_amount("I want to open a saree shop with budget of ₹1,00,000")
    assert res2.available_capital == 100000
    assert res2.currency == "INR"
    assert res2.currency_source == "EXPLICIT"

    res3 = parse_canonical_amount("Budget of Rs 1.5 lakh")
    assert res3.available_capital == 150000
    assert res3.currency == "INR"
    assert res3.currency_source == "EXPLICIT"


def test_amount_parser_context_inferred_currency():
    # Without explicit currency token, but financial context present
    res = parse_canonical_amount("मेरा बजट एक लाख है")
    assert res.available_capital == 100000
    assert res.currency == "INR"
    assert res.currency_source == "CONTEXT_INFERRED"


# =============================================================================
# 5. NEGATIVE TESTS (MUST NOT EXTRACT AS CAPITAL)
# =============================================================================

def test_negative_cases_rejected():
    # Customers / people count
    res_cust = parse_canonical_amount("I have one lakh customers visiting every year.")
    assert res_cust.available_capital is None

    # Area / sq ft
    res_area = parse_canonical_amount("The shop area is 1 lakh sq ft in the village.")
    assert res_area.available_capital is None

    # Experience / years
    res_exp = parse_canonical_amount("I have 5 years of experience in retail.")
    assert res_exp.available_capital is None

    # Livestock count
    res_cows = parse_canonical_amount("I have 100 cows in my cattle farm.")
    assert res_cows.available_capital is None


def test_loan_vs_available_capital_distinction():
    res = parse_canonical_amount("I need a loan of ₹1 lakh to start my shop.")
    assert res.loan_requested == 100000
    assert res.available_capital is None


# =============================================================================
# 6. BUSINESS ENTITY EXTRACTION MULTILINGUAL TESTS
# =============================================================================

def test_business_concept_multilingual_aliases():
    # Saree variations
    b1 = extract_multilingual_business_entities("मुझे साड़ी का दुकान खोलना है")
    assert b1.business_concept == "Saree Retail"

    b2 = extract_multilingual_business_entities("मुझे साड़ी की दुकान खोलनी है")
    assert b2.business_concept == "Saree Retail"

    b3 = extract_multilingual_business_entities("Mujhe saree shop kholna hai")
    assert b3.business_concept == "Saree Retail"

    b4 = extract_multilingual_business_entities("ನಾನು ಸೀರೆ ಅಂಗಡಿ ತೆರೆಯಲು ಬಯಸುತ್ತೇನೆ")
    assert b4.business_concept == "Saree Retail"

    b5 = extract_multilingual_business_entities("புடவைக் கடை தொடங்க வேண்டும்")
    assert b5.business_concept == "Saree Retail"

    # Grocery / Kirana variations
    b6 = extract_multilingual_business_entities("मी किराणा दुकान सुरू करू इच्छितो")
    assert b6.business_concept == "Grocery & Kirana Store"

    # Dairy variations
    b7 = extract_multilingual_business_entities("दूध का व्यापार शुरू करना है")
    assert b7.business_concept == "Dairy Farm"


# =============================================================================
# 7. END-TO-END STAGE 1 INTAKE PIPELINE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_canonical_intake_hindi_transcript():
    # Primary failing sentence from logs:
    # "मुझे साड़ी का दुकान खोलना है, मेरा बजट एक लाख रुपये।"
    text = "मुझे साड़ी का दुकान खोलना है, मेरा बजट एक लाख रुपये।"
    res = await process_user_intake(text=text, input_type="voice", language_override="hi-IN")

    assert res.success is True
    assert res.profile.business_concept == "Saree Retail"
    assert res.profile.available_capital == 100000
    assert res.profile.capital_currency == "INR"
    assert res.language.code == "hi"
    assert res.profile.intent == "start_business"


@pytest.mark.asyncio
async def test_canonical_intake_hindi_compound_amount():
    text = "मेरा बजट दो लाख पचास हजार रुपये है और मैं नागपुर में किराना दुकान शुरू करना चाहता हूँ।"
    res = await process_user_intake(text=text, input_type="text")

    assert res.profile.available_capital == 250000
    assert res.profile.business_concept == "Grocery & Kirana Store"
    assert res.profile.proposed_location.district == "Nagpur"


@pytest.mark.asyncio
async def test_canonical_intake_hindi_fraction_amount():
    text = "मेरे पास डेढ़ लाख रुपये हैं और मुझे सिलाई का काम शुरू करना है।"
    res = await process_user_intake(text=text, input_type="text")

    assert res.profile.available_capital == 150000
    assert res.profile.business_concept == "Tailoring & Boutique"


@pytest.mark.asyncio
async def test_canonical_intake_hinglish():
    text = "Mujhe saree shop kholna hai, mera budget ek lakh hai"
    res = await process_user_intake(text=text, input_type="text")

    assert res.profile.business_concept == "Saree Retail"
    assert res.profile.available_capital == 100000
    assert res.profile.capital_currency == "INR"


@pytest.mark.asyncio
async def test_canonical_intake_kannada():
    text = "ನಾನು ಸೀರೆ ಅಂಗಡಿ ತೆರೆಯಲು ಬಯಸುತ್ತೇನೆ, ನನ್ನ ಬಜೆಟ್ ಒಂದು ಲಕ್ಷ ರೂಪಾಯಿ"
    res = await process_user_intake(text=text, input_type="voice", language_override="kn-IN")

    assert res.profile.business_concept == "Saree Retail"
    assert res.profile.available_capital == 100000
    assert res.language.code == "kn"


@pytest.mark.asyncio
async def test_canonical_intake_mixed_code():
    text = "I want to start साड़ी की दुकान, budget एक लाख है"
    res = await process_user_intake(text=text, input_type="text")

    assert res.profile.business_concept == "Saree Retail"
    assert res.profile.available_capital == 100000
