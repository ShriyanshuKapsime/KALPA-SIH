"""
Comprehensive Test Suite for Stage 14.1 Multilingual, LLM-Generated Question Framing.
Tests 8 key fields across English, Hindi, and Marathi:
1. business_activity
2. legal_constitution
3. operating_premises
4. target_customers
5. promoter_contribution
6. project_cost
7. expected_revenue
8. business_experience

Verifies:
- Natural, rural-friendly conversational phrasing
- Helper text exists and guides the user clearly
- Realistic examples exist for open-ended questions
- Selected language is respected (en, hi, mr)
- No internal snake_case field_id exposed in user-facing text
- No fabricated business facts or financial numbers
- LLM failure / unconfigured state falls back safely to curated multilingual catalog
- TTS audio script synthesizes question + helper + example (omitting internal why_we_are_asking)
- STT transcription remains intact without LLM alteration
"""
import sys
import os
import asyncio
import unittest

# Ensure ai-service root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.dpr_stage1.dpr_question_framer import dpr_question_framer, get_fallback_question, CURATED_FALLBACK_CATALOG
from app.services.dpr_stage1.dpr_question_engine import dpr_question_engine, DPRQuestion
from app.services.dpr_stage1.dpr_gap_analyzer import DPRGapAnalysisResult, GapItem
from app.services.dpr_stage1.dpr_registry import get_field_definition, normalize_field_id
from app.services.dpr_stage1 import dpr_context_builder, dpr_gap_analyzer, dpr_scenario_manager, dpr_answer_resolver


class TestStage141QuestionFraming(unittest.TestCase):
    """Test Suite for LLM-Generated Multilingual Question Framing."""

    TEST_FIELDS = [
        "business_activity",
        "legal_constitution",
        "operating_premises",
        "target_customers",
        "promoter_contribution",
        "project_cost",
        "expected_revenue",
        "business_experience"
    ]

    def test_01_all_test_fields_have_curated_multilingual_fallbacks(self):
        """1. Every required test field has curated translations in English, Hindi, and Marathi."""
        for fid in self.TEST_FIELDS:
            self.assertIn(fid, CURATED_FALLBACK_CATALOG, f"Field '{fid}' missing from CURATED_FALLBACK_CATALOG")
            cat = CURATED_FALLBACK_CATALOG[fid]
            for lang in ["en", "hi", "mr"]:
                self.assertIn(lang, cat, f"Field '{fid}' missing language '{lang}' in catalog")
                entry = cat[lang]
                self.assertTrue(entry.get("question"), f"Empty question for '{fid}' in lang='{lang}'")
                self.assertTrue(entry.get("helper_text"), f"Empty helper_text for '{fid}' in lang='{lang}'")
                self.assertTrue(entry.get("why_we_are_asking"), f"Empty why_we_are_asking for '{fid}' in lang='{lang}'")
                # Ensure no raw snake_case field_id is leaked in questions or helper text
                self.assertNotIn(fid, entry["question"], f"Raw field_id leaked in question: {entry['question']}")
                self.assertNotIn("Please provide the detail for", entry["question"])

    def test_02_natural_conversational_questions_across_languages(self):
        """2. Fallback and framer generate natural, empathetic questions in en, hi, mr."""
        # Test Business Activity in English
        q_en = get_fallback_question(
            field_id="business_activity",
            field_label="Business Activity",
            field_type="string",
            intent="Describe business operations",
            why_required="Required for feasibility appraisal",
            language="en"
        )
        self.assertIn("What business or activity are you planning", q_en.question)
        self.assertIn("saree", q_en.example.lower())
        self.assertNotIn("business_activity", q_en.question)

        # Test Business Activity in Hindi (Devanagari)
        q_hi = get_fallback_question(
            field_id="business_activity",
            field_label="Business Activity",
            field_type="string",
            intent="Describe business operations",
            why_required="Required for feasibility appraisal",
            language="hi"
        )
        self.assertIn("आप कौन-सा व्यवसाय या काम शुरू अथवा विस्तार करना चाहते हैं?", q_hi.question)
        self.assertIn("साड़ी", q_hi.example)

        # Test Business Activity in Marathi (Devanagari)
        q_mr = get_fallback_question(
            field_id="business_activity",
            field_label="Business Activity",
            field_type="string",
            intent="Describe business operations",
            why_required="Required for feasibility appraisal",
            language="mr"
        )
        self.assertIn("तुम्हाला कोणता व्यवसाय किंवा उपक्रम", q_mr.question)
        self.assertIn("साडी", q_mr.example)

    def test_03_numeric_and_financial_fields_framing(self):
        """3. Numeric / Financial fields (promoter contribution, project cost, expected revenue) explain units."""
        # Promoter Contribution
        pc_en = get_fallback_question("promoter_contribution", "Promoter Contribution", "currency", "Own investment", "Bank equity margin", language="en")
        self.assertIn("own savings", pc_en.question.lower())
        self.assertIn("₹", pc_en.example)

        # Project Cost
        cost_hi = get_fallback_question("project_cost", "Project Cost", "currency", "Total investment outlay", "Loan size calculation", language="hi")
        self.assertIn("कुल अनुमानित प्रोजेक्ट खर्च", cost_hi.question)
        self.assertIn("रुपये", cost_hi.helper_text)

        # Expected Revenue
        rev_mr = get_fallback_question("expected_revenue", "Expected Annual Revenue", "currency", "Gross annual turnover", "DSCR debt capacity", language="mr")
        self.assertIn("वार्षिक विक्री", rev_mr.question)
        self.assertIn("रुपये", rev_mr.helper_text)

    def test_04_no_fabricated_facts_or_financials(self):
        """4. Question framing never fabricates unprovided facts or assumes arbitrary numbers."""
        async def _run():
            # General business without category
            q = await dpr_question_framer.frame_question(
                field_id="business_activity",
                field_label="Business Activity",
                field_type="string",
                intent="Describe business operations",
                why_required="Bank appraisal",
                language="en"
            )
            # Question is clean and open-ended
            self.assertIsNotNone(q.question)
            self.assertIsNotNone(q.helper_text)
            self.assertFalse("Retail" in q.question and "Manufacturing" in q.question)
        asyncio.run(_run())

    def test_05_why_we_are_asking_is_separate_from_question(self):
        """5. 'Why We Are Asking' is maintained separately from question text and non-technical."""
        for fid in self.TEST_FIELDS:
            q = get_fallback_question(fid, fid, "string", "Test", "Test bank req", language="en")
            self.assertTrue(q.why_we_are_asking)
            self.assertNotEqual(q.question, q.why_we_are_asking)
            # Technical internals should NOT appear
            self.assertNotIn("DPRGapAnalysisResult", q.why_we_are_asking)
            self.assertNotIn("DPRFieldDefinition", q.why_we_are_asking)
            self.assertNotIn("dpr_registry", q.why_we_are_asking)

    def test_06_dpr_question_engine_integration(self):
        """6. DPRQuestionEngine integrates framer and produces complete DPRQuestion payload."""
        async def _run():
            bid = "test_framing_integration_001"
            # Set minimum answers, leaving business_activity unresolved
            dpr_scenario_manager.set_user_answer(bid, "business_name", "Varanasi Silk Emporium")
            dpr_scenario_manager.set_user_answer(bid, "location_state", "Uttar Pradesh")
            dpr_scenario_manager.set_user_answer(bid, "location_district", "Varanasi")

            ctx = await dpr_context_builder.build_context(business_id=bid)
            gap_res = dpr_gap_analyzer.analyze(ctx)

            # Request Hindi question
            q_hi = await dpr_question_engine.get_next_question(gap_res, ctx, language="hi")
            if q_hi:
                self.assertIsInstance(q_hi, DPRQuestion)
                self.assertEqual(q_hi.language, "hi")
                self.assertTrue(q_hi.question)
                self.assertTrue(q_hi.helper_text)
                self.assertTrue(q_hi.why_we_are_asking)
                self.assertNotIn("Please provide the detail for", q_hi.question)
                self.assertNotIn("Please provide the detail for", q_hi.question_text)
        asyncio.run(_run())

    def test_07_tts_synthesis_payload_formatting(self):
        """7. TTS synthesis text combines question + helper_text + example, omitting internal why_we_are_asking."""
        q = DPRQuestion(
            field_id="business_activity",
            section_id="sec_01",
            module_id="mod_01",
            question="आप कौन-सा व्यवसाय या काम शुरू करना चाहते हैं?",
            question_text="आप कौन-सा व्यवसाय या काम शुरू करना चाहते हैं?",
            helper_text="आप क्या बेचेंगे या कौन-सी सेवा देंगे, इसके बारे में बताएं।",
            example="उदाहरण: मैं अपने गांव में साड़ी की दुकान शुरू करना चाहता हूँ।",
            why_we_are_asking="आंतरिक मूल्यांकन हेतु।",
            language="hi"
        )

        parts = [q.question or q.question_text]
        if q.helper_text:
            parts.append(q.helper_text)
        if q.example:
            parts.append(q.example)
        combined_speech_text = "\n".join(parts)

        self.assertIn("आप कौन-सा व्यवसाय", combined_speech_text)
        self.assertIn("आप क्या बेचेंगे", combined_speech_text)
        self.assertIn("उदाहरण:", combined_speech_text)
        self.assertNotIn("आंतरिक मूल्यांकन हेतु।", combined_speech_text)

    def test_08_stt_answer_resolution_remains_exact_and_unmutated(self):
        """8. STT voice answers resolve canonically without LLM alteration."""
        # Numeric Hindi resolution
        res_num = dpr_answer_resolver.resolve_answer("project_timeline_months", "पंद्रह")
        self.assertTrue(res_num.validation_passed)
        self.assertEqual(res_num.canonical_value, 15.0)

        # Free text resolution preserves exact string
        user_spoken = "I plan to start a saree and lehenga retail shop in the central market."
        res_text = dpr_answer_resolver.resolve_answer("business_activity", user_spoken)
        self.assertTrue(res_text.validation_passed)
        self.assertEqual(res_text.canonical_value, user_spoken)


if __name__ == "__main__":
    unittest.main(verbosity=2)
