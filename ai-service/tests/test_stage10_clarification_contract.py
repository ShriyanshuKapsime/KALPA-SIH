"""
Comprehensive Data Contract Test Suite for Stage 10 Clarification System.
Tests:
1. Business-contextual question generation (Saree Retail, Rice Mill, Dairy)
2. Question canonical contract (field, question, reason, benchmark, priority, suggested_options)
3. Independent question persistence (answering Q1 keeps Q2 and Q3 pending)
4. Full clarification lifecycle (Q1 -> Q2 -> Q3 -> COMPLETE)
5. Voice / Text identical contract
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.entrepreneur_profile_engine import (
    entrepreneur_profile_engine,
    clarification_extractor,
)
from app.schemas.entrepreneur_profile import (
    EntrepreneurProfileRequest,
    EntrepreneurReadinessResponse,
    ClarificationQuestion,
)


@pytest.fixture
def client():
    return TestClient(app)


class TestStage10ClarificationContract:

    def test_01_canonical_question_schema_contract(self, client):
        """Verify POST /analyze returns canonical question contract with non-empty question and reason."""
        payload = {
            "business_profile": {
                "business_id": "traditional_saree_retail",
                "specific_business": "Traditional Saree / Silk / Women's Ethnic Wear Retail",
                "category": "Apparel & Textiles"
            },
            "user_profile": {
                "skills": {},
                "experience": {},
                "resources": {}
            }
        }
        res = client.post("/api/v1/entrepreneur-profile/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert "questions" in data
        assert len(data["questions"]) >= 3
        assert data["pending_count"] == len(data["questions"])

        # Check each question object structure
        for q in data["questions"]:
            assert "field" in q and q["field"]
            assert "question" in q and len(q["question"]) > 10, f"Missing question text in {q}"
            assert "question_en" in q and len(q["question_en"]) > 10
            assert "priority" in q and q["priority"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            assert "importance" in q
            assert "reason" in q and len(q["reason"]) > 5, f"Missing reason in {q}"
            assert "benchmark" in q and len(q["benchmark"]) > 5, f"Missing benchmark in {q}"
            assert "suggested_options" in q and isinstance(q["suggested_options"], list)

    def test_02_business_contextual_questions(self, client):
        """Verify questions generated for Saree Retail vs Rice Mill vs Dairy are contextual."""
        # 1. Saree Retail
        saree_res = client.post("/api/v1/entrepreneur-profile/analyze", json={
            "business_profile": {
                "business_id": "saree_retail",
                "specific_business": "Traditional Saree Retail",
                "category": "Retail"
            },
            "user_profile": {}
        }).json()
        saree_skills_q = next(q for q in saree_res["questions"] if q["field"] == "skills")
        assert any(k in saree_skills_q["question"].lower() for k in ["retail", "sales", "merchandis", "customer", "saree"])

        # 2. Rice Mill
        rice_res = client.post("/api/v1/entrepreneur-profile/analyze", json={
            "business_profile": {
                "business_id": "rice_mill",
                "specific_business": "Mini Rice Mill",
                "category": "Agro Processing"
            },
            "user_profile": {}
        }).json()
        rice_skills_q = next(q for q in rice_res["questions"] if q["field"] == "skills")
        assert any(k in rice_skills_q["question"].lower() for k in ["machinery", "grain", "process", "mill"])

        # 3. Dairy Farm
        dairy_res = client.post("/api/v1/entrepreneur-profile/analyze", json={
            "business_profile": {
                "business_id": "dairy_farm",
                "specific_business": "Dairy Farm Unit",
                "category": "Livestock"
            },
            "user_profile": {}
        }).json()
        dairy_skills_q = next(q for q in dairy_res["questions"] if q["field"] == "skills")
        assert any(k in dairy_skills_q["question"].lower() for k in ["livestock", "milk", "animal", "dairy", "cattle"])

    def test_03_independent_question_lifecycle_and_hard_gate(self, client):
        """
        Step-by-step lifecycle:
        Initial: 3 Pending (skills, experience, resources)
        Answer skills -> 2 Pending (experience, resources)
        Answer experience -> 1 Pending (resources)
        Answer resources -> 0 Pending -> COMPLETE / READY
        """
        biz = {
            "business_id": "saree_retail",
            "specific_business": "Traditional Saree Retail",
            "category": "Retail"
        }

        # Step 0: Initial state
        initial = client.post("/api/v1/entrepreneur-profile/analyze", json={
            "business_profile": biz,
            "user_profile": {}
        }).json()

        assert initial["pending_count"] == 3
        fields_initial = {q["field"] for q in initial["questions"]}
        assert "skills" in fields_initial
        assert "experience.years_of_experience" in fields_initial
        assert "resources.available_area_sqft" in fields_initial

        # Step 1: Answer Skills (only skills, no years mentioned)
        clarify_1 = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "field": "skills",
            "text": "साड़ी की बिक्री, ग्राहक सेवा और दुकान का प्रबंधन करना आता है",
            "business_profile": biz,
            "entrepreneur_profile": initial.get("entrepreneur_profile") or {}
        }).json()

        assert clarify_1["success"] is True
        assert clarify_1["pending_count"] == 2
        remaining_1 = {q["field"] for q in clarify_1["questions"]}
        assert "skills" not in remaining_1
        assert "experience.years_of_experience" in remaining_1
        assert "resources.available_area_sqft" in remaining_1
        assert "skills" in clarify_1["answered_fields"]

        # Step 2: Answer Experience
        clarify_2 = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "field": "experience.years_of_experience",
            "text": "3 years of experience in retail clothing sales",
            "business_profile": biz,
            "entrepreneur_profile": clarify_1["entrepreneur_profile"]
        }).json()

        assert clarify_2["success"] is True
        assert clarify_2["pending_count"] == 1
        remaining_2 = {q["field"] for q in clarify_2["questions"]}
        assert "skills" not in remaining_2
        assert "experience.years_of_experience" not in remaining_2
        assert "resources.available_area_sqft" in remaining_2

        # Step 3: Answer Resources (Area)
        clarify_3 = client.post("/api/v1/entrepreneur-profile/clarify", json={
            "field": "resources.available_area_sqft",
            "text": "250 sq ft commercial shop ready",
            "business_profile": biz,
            "entrepreneur_profile": clarify_2["entrepreneur_profile"]
        }).json()

        assert clarify_3["success"] is True
        assert clarify_3["pending_count"] == 0
        assert len(clarify_3["questions"]) == 0
        assert clarify_3["status"] == "READY"
        assert clarify_3["readiness_score"] >= 60.0
        assert len(clarify_3["calculation_provenance"]) == 5
