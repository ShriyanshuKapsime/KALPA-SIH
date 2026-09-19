"""
Comprehensive Scenario Verification Suite for KALPA Stage 10 & 11 Refactor.
Covers Scenarios A through G as specified in the authenticity specification:

SCENARIO A: Saree Retail (₹1,00,000 margin, 3 yrs retail exp, strong skills, adequate resources)
SCENARIO B: Saree Retail (₹1,00,000 margin, 0 yrs exp, no relevant skills)
SCENARIO C: Dairy Farm (Different skills, livestock resources, cold chain requirements)
SCENARIO D: Missing Entrepreneur Information (Data gap explicitly identified with questions)
SCENARIO E: Strong Entrepreneur but Weak Market (Stage 6/8 low demand -> High Market Risk)
SCENARIO F: Strong Market but Weak Financial DSCR (Stage 9 DSCR < 1.15 -> Critical Financial Risk)
SCENARIO G: Strong Market + Finance but Entrepreneur Capability Gap (Stage 10 gaps -> High Operational Risk)
"""
import pytest
from app.services.entrepreneur_profile_engine import entrepreneur_profile_engine
from app.services.risk_engine import risk_engine


class TestStage10Stage11Scenarios:
    """
    Validation of end-to-end deterministic behavior across Scenarios A through G.
    """

    # -------------------------------------------------------------------------
    # SCENARIO A: Saree Retail — Experienced, Skilled, Adequate Resources
    # -------------------------------------------------------------------------
    def test_scenario_a_saree_retail_experienced(self):
        stage10_payload = {
            "business_profile": {
                "business_id": "saree_retail",
                "specific_business": "Saree & Ethnic Wear Retail"
            },
            "user_profile": {
                "skills": {
                    "skills": ["Textile fabric identification", "Retail sales", "Customer negotiation", "Display merchandising"],
                    "skill_level": "EXPERT"
                },
                "experience": {
                    "years_of_experience": 3.0,
                    "domain": "Saree & Textile Retail",
                    "prior_business_ownership": True
                },
                "training": {
                    "has_formal_training": True,
                    "certifications": ["Textile Retail Merchandising"]
                },
                "resources": {
                    "available_area_sqft": 250.0,
                    "power_connection_type": "SINGLE_PHASE",
                    "land_or_premises_available": True
                },
                "operations": {
                    "commitment_type": "FULL_TIME",
                    "available_family_helpers": 1,
                    "hired_workers_planned": 1
                }
            }
        }
        res10 = entrepreneur_profile_engine.analyze(stage10_payload)

        # Stage 10 Assertions
        assert res10.success is True
        assert res10.status == "READY"
        assert res10.readiness_level == "HIGH"
        assert res10.readiness_score >= 80.0
        assert res10.component_scores["skills"].score >= 75.0
        assert res10.component_scores["experience"].score >= 90.0
        assert res10.component_scores["resources"].score >= 80.0
        assert res10.component_scores["operational"].score >= 85.0
        assert len(res10.calculation_provenance) >= 5

        # Feed into Stage 11 with healthy financial & market data
        stage11_payload = {
            "business_profile": {"business_id": "saree_retail"},
            "financial_analysis": {
                "financial_viability": {
                    "debt_service_coverage_ratio": 1.75,
                    "viability_status": "HIGHLY_VIABLE"
                },
                "break_even_analysis": {
                    "break_even_point_percentage": 45.0
                }
            },
            "market_intelligence": {
                "market_indicators": {
                    "demand_evidence": {"demand_level": "HIGH"},
                    "competition_evidence": {"competitor_count": 2}
                }
            },
            "entrepreneur_readiness": res10.model_dump()
        }
        res11 = risk_engine.analyze(stage11_payload)

        # Stage 11 Assertions
        assert res11.success is True
        assert res11.overall_risk_severity in ["LOW", "MEDIUM"]
        assert res11.overall_risk_score <= 0.40
        assert res11.category_risks["FINANCIAL"].level == "LOW"
        assert res11.category_risks["OPERATIONAL"].level == "LOW"
        assert res11.category_risks["INFRASTRUCTURE"].level == "LOW"

    # -------------------------------------------------------------------------
    # SCENARIO B: Saree Retail — 0 Years Experience, No Skills
    # -------------------------------------------------------------------------
    def test_scenario_b_saree_retail_novice_zero_experience(self):
        stage10_payload = {
            "business_profile": {
                "business_id": "saree_retail",
                "specific_business": "Saree & Ethnic Wear Retail"
            },
            "user_profile": {
                "skills": {
                    "skills": ["General helper"],
                    "skill_level": "NOVICE"
                },
                "experience": {
                    "years_of_experience": 0.0,
                    "domain": "",
                    "prior_business_ownership": False
                },
                "training": {
                    "has_formal_training": False
                },
                "resources": {
                    "available_area_sqft": 80.0,
                    "power_connection_type": "SINGLE_PHASE"
                },
                "operations": {
                    "commitment_type": "PART_TIME",
                    "available_family_helpers": 0
                }
            }
        }
        res10 = entrepreneur_profile_engine.analyze(stage10_payload)

        # Stage 10 Assertions: Must NOT award arbitrary positive experience score
        assert res10.success is True
        assert res10.status == "READY"
        assert res10.readiness_level in ["DEVELOPING", "LOW"]
        assert res10.readiness_score <= 50.0
        assert res10.component_scores["experience"].score <= 25.0
        assert res10.component_scores["experience"].status == "GAP"
        assert res10.component_scores["skills"].score <= 35.0
        assert len(res10.gaps) >= 2
        assert len(res10.required_support) >= 1
        # Contextual support for saree retail must include merchandising or inventory management
        assert any("inventory" in s.gap.lower() or "retail" in s.gap.lower() or "merchandising" in s.gap.lower() for s in res10.required_support)

        # Feed into Stage 11 -> Operational Risk should reflect the capability gap
        stage11_payload = {
            "business_profile": {"business_id": "saree_retail"},
            "entrepreneur_readiness": res10.model_dump()
        }
        res11 = risk_engine.analyze(stage11_payload)
        assert res11.category_risks["OPERATIONAL"].level in ["HIGH", "CRITICAL"]
        assert any("readiness" in d.lower() or "experience" in d.lower() or "skills" in d.lower() for d in res11.category_risks["OPERATIONAL"].drivers)

    # -------------------------------------------------------------------------
    # SCENARIO C: Dairy Farm — Sector-Specific Requirements & Cold Chain
    # -------------------------------------------------------------------------
    def test_scenario_c_dairy_farm_sector_specific(self):
        stage10_payload = {
            "business_profile": {
                "business_id": "dairy_farm",
                "specific_business": "Commercial Dairy Farming Unit"
            },
            "user_profile": {
                "skills": {
                    "skills": ["Milking techniques", "Cattle feeding and nutrition", "Livestock breed management"],
                    "skill_level": "INTERMEDIATE"
                },
                "experience": {
                    "years_of_experience": 2.5,
                    "domain": "Dairy & Animal Husbandry"
                },
                "training": {
                    "has_formal_training": True,
                    "certifications": ["NDDB Dairy Management Course"]
                },
                "resources": {
                    "available_area_sqft": 1500.0,
                    "power_connection_type": "THREE_PHASE_COMMERCIAL",
                    "water_source_available": True
                },
                "operations": {
                    "commitment_type": "FULL_TIME",
                    "available_family_helpers": 2
                }
            }
        }
        res10 = entrepreneur_profile_engine.analyze(stage10_payload)

        assert res10.success is True
        assert res10.readiness_level in ["HIGH", "MODERATE"]
        assert res10.readiness_score >= 70.0
        assert res10.component_scores["skills"].score >= 70.0
        assert res10.component_scores["training"].score >= 80.0

        # Dairy in Stage 11 must trigger perishable supply chain & animal health operational drivers
        stage11_payload = {
            "business_profile": {"business_id": "dairy_farm"},
            "entrepreneur_readiness": res10.model_dump()
        }
        res11 = risk_engine.analyze(stage11_payload)
        assert res11.category_risks["SUPPLY_CHAIN"].level in ["MEDIUM", "HIGH"]
        assert any("perishable" in d.lower() or "cold chain" in d.lower() or "milk" in d.lower() for d in res11.category_risks["SUPPLY_CHAIN"].drivers)

    # -------------------------------------------------------------------------
    # SCENARIO D: Missing Entrepreneur Information (Data Gap & Questions)
    # -------------------------------------------------------------------------
    def test_scenario_d_missing_entrepreneur_information(self):
        stage10_payload = {
            "business_profile": {
                "business_id": "tailoring_shop",
                "specific_business": "Boutique & Tailoring Unit"
            },
            "user_profile": {
                # Completely missing skills, experience, resources
            }
        }
        res10 = entrepreneur_profile_engine.analyze(stage10_payload)

        # Stage 10 must NOT fabricate scores; must return PROFILE_INCOMPLETE
        assert res10.status == "PROFILE_INCOMPLETE"
        assert res10.readiness_level == "INCOMPLETE"
        assert len(res10.questions) >= 2
        assert len(res10.missing_fields) >= 2
        assert res10.confidence <= 0.60

        # Feed missing Stage 10 into Stage 11 -> Stage 11 operational risk must flag data gap with reduced confidence
        stage11_payload = {
            "business_profile": {"business_id": "tailoring_shop"},
            "entrepreneur_readiness": res10.model_dump()
        }
        res11 = risk_engine.analyze(stage11_payload)
        assert res11.category_risks["OPERATIONAL"].level in ["MEDIUM", "HIGH", "UNKNOWN"]
        assert res11.confidence <= 0.70

    # -------------------------------------------------------------------------
    # SCENARIO E: Strong Entrepreneur but Weak Market
    # -------------------------------------------------------------------------
    def test_scenario_e_strong_entrepreneur_weak_market(self):
        stage10_payload = {
            "business_profile": {"business_id": "grocery_store"},
            "user_profile": {
                "skills": {"skills": ["Inventory management", "Retail sales", "Vendor management"], "skill_level": "EXPERT"},
                "experience": {"years_of_experience": 6.0, "prior_business_ownership": True},
                "training": {"has_formal_training": True},
                "resources": {"available_area_sqft": 400.0, "power_connection_type": "SINGLE_PHASE"},
                "operations": {"commitment_type": "FULL_TIME", "available_family_helpers": 1}
            }
        }
        res10 = entrepreneur_profile_engine.analyze(stage10_payload)
        assert res10.readiness_score >= 85.0

        # Upstream Stage 6 has depressed demand & saturated competition
        stage11_payload = {
            "business_profile": {"business_id": "grocery_store"},
            "market_intelligence": {
                "market_indicators": {
                    "demand_evidence": {"demand_level": "LOW"},
                    "competition_evidence": {"competitor_count": 9}
                }
            },
            "entrepreneur_readiness": res10.model_dump()
        }
        res11 = risk_engine.analyze(stage11_payload)

        # Market & Competition risks must be HIGH while Operational risk is LOW
        assert res11.category_risks["MARKET"].level in ["HIGH", "CRITICAL"]
        assert res11.category_risks["COMPETITION"].level in ["HIGH", "CRITICAL"]
        assert res11.category_risks["OPERATIONAL"].level == "LOW"
        assert res11.overall_risk_score >= 0.40
        assert res11.overall_risk_severity in ["HIGH", "CRITICAL"]

    # -------------------------------------------------------------------------
    # SCENARIO F: Strong Market but Weak Financial DSCR
    # -------------------------------------------------------------------------
    def test_scenario_f_strong_market_weak_financial_dscr(self):
        stage11_payload = {
            "business_profile": {"business_id": "rice_mill"},
            "financial_analysis": {
                "financial_viability": {
                    "debt_service_coverage_ratio": 1.05,  # Fragile / Overleveraged
                    "viability_status": "CRITICAL_RISK"
                },
                "break_even_analysis": {
                    "break_even_point_percentage": 78.0  # High break-even
                }
            },
            "market_intelligence": {
                "market_indicators": {
                    "demand_evidence": {"demand_level": "VERY_HIGH"},
                    "competition_evidence": {"competitor_count": 1}
                }
            },
            "entrepreneur_readiness": {
                "readiness_score": 85.0
            }
        }
        res11 = risk_engine.analyze(stage11_payload)

        # Financial risk must be CRITICAL and trigger the Critical Risk Ceiling
        assert res11.category_risks["FINANCIAL"].level == "CRITICAL"
        assert res11.category_risks["FINANCIAL"].score >= 0.85
        assert res11.critical_risks_count >= 1
        assert res11.provenance.critical_ceiling_applied is True
        assert res11.overall_risk_severity in ["HIGH", "CRITICAL"]

    # -------------------------------------------------------------------------
    # SCENARIO G: Strong Market + Finance but Entrepreneur Capability Gap
    # -------------------------------------------------------------------------
    def test_scenario_g_strong_market_finance_weak_entrepreneur(self):
        # Entrepreneur with severe skills and experience gap for specialized business (Solar pump repair)
        stage10_payload = {
            "business_profile": {
                "business_id": "solar_pump_repair_service",
                "specific_business": "Solar Pump & Inverter Repair Unit"
            },
            "user_profile": {
                "skills": {
                    "skills": ["General shopkeeping"],
                    "skill_level": "NOVICE"
                },
                "experience": {
                    "years_of_experience": 0.5,
                    "domain": "General Retail"
                },
                "training": {
                    "has_formal_training": False
                },
                "resources": {
                    "available_area_sqft": 100.0,
                    "power_connection_type": "SINGLE_PHASE"
                },
                "operations": {
                    "commitment_type": "PART_TIME"
                }
            }
        }
        res10 = entrepreneur_profile_engine.analyze(stage10_payload)
        assert res10.readiness_score <= 50.0
        assert res10.readiness_level in ["DEVELOPING", "LOW"]
        assert len(res10.gaps) >= 2

        # Strong market and financial data
        stage11_payload = {
            "business_profile": {"business_id": "solar_pump_repair_service"},
            "financial_analysis": {
                "financial_viability": {
                    "debt_service_coverage_ratio": 2.20
                },
                "break_even_analysis": {
                    "break_even_point_percentage": 35.0
                }
            },
            "market_intelligence": {
                "market_indicators": {
                    "demand_evidence": {"demand_level": "VERY_HIGH"},
                    "competition_evidence": {"competitor_count": 0}
                }
            },
            "entrepreneur_readiness": res10.model_dump()
        }
        res11 = risk_engine.analyze(stage11_payload)

        # Financial & Market are LOW, but Operational is elevated due to technical skill deficit
        assert res11.category_risks["FINANCIAL"].level == "LOW"
        assert res11.category_risks["MARKET"].level == "LOW"
        assert res11.category_risks["OPERATIONAL"].level in ["HIGH", "CRITICAL"]
        assert any("gap" in d.lower() or "readiness" in d.lower() or "skill" in d.lower() for d in res11.category_risks["OPERATIONAL"].drivers)
        # Verify mitigation includes technical training
        assert any("training" in m.lower() or "technical" in m.lower() or "hire" in m.lower() for m in res11.category_risks["OPERATIONAL"].mitigations)
