"""
Comprehensive Test Suite for Authoritative Indian Income Tax Resolver
Statutory Policy Version: INDIA_INCOME_TAX_AY_2026_27 (Assessment Year 2026-27 / Financial Year 2025-26)

Tests all required statutory test cases:
1. Sole proprietor, small retail (Section 44AD, 6% vs 8%)
2. Sole proprietor, manufacturing (Section 44AD vs 115BAC)
3. Sole proprietor, generic service (salons/repair: verified excluded from 44ADA)
4. Specified professional under Section 44AA(1) (Section 44ADA 50% deemed profit)
5. Partnership firm (44AD eligible vs flat 30%)
6. LLP (verified excluded from 44AD, flat 30% + cess)
7. Domestic company (standard 25% MSME vs 115BAA)
8. Commercial Dairy Farm (PGBP commercial business, not Section 10(1) exempt)
9. Saree Retail (retail trading)
10. Turnover below/above 44AD thresholds (INR 2 Cr / INR 3 Cr)
11. Digital vs non-digital receipts
12. Income around INR 12L (marginal relief verification)
13. Income above INR 12L (marginal relief vs normal tax)
14. Income above INR 24L (30% slab rate)
15. Company opting vs not opting for Section 115BAA
"""
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.financial_engine.projection.tax_policy import (
    tax_policy_resolver,
    compute_individual_new_regime_tax_ay2026_27,
    TAX_POLICY_VERSION,
    STATUTORY_ASSESSMENT_YEAR,
    STATUTORY_FINANCIAL_YEAR,
)

def run_tests():
    print(f"=== TESTING TAX POLICY: {TAX_POLICY_VERSION} (AY {STATUTORY_ASSESSMENT_YEAR}) ===")
    passed = 0
    total = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name} {details}")
        else:
            print(f"  [FAIL] {name} {details}")

    # -------------------------------------------------------------
    # 1. Section 115BAC Slabs & Section 87A Rebate & Marginal Relief
    # -------------------------------------------------------------
    print("\n--- Test Suite 1: Individual Section 115BAC Slabs & Rebate & Marginal Relief ---")
    
    # Case 1A: Income <= 4L -> 0%
    tax, slab, reb, mr, sur, cess = compute_individual_new_regime_tax_ay2026_27(400000.0)
    assert_test("1A: Income INR 4L (0% slab)", tax == 0.0 and slab == 0.0 and reb == 0.0, f"(Tax: INR {tax})")

    # Case 1B: Income INR 8L -> 4L @ 5% = 20,000. Under 87A rebate <= 12L -> Tax = 0
    tax, slab, reb, mr, sur, cess = compute_individual_new_regime_tax_ay2026_27(800000.0)
    assert_test("1B: Income INR 8L (Rebate under 87A)", tax == 0.0 and slab == 20000.0 and reb == 20000.0, f"(Tax: INR {tax}, Slab: INR {slab}, Rebate: INR {reb})")

    # Case 1C: Income INR 12L -> 4L@5% (20k) + 4L@10% (40k) = 60,000. Rebate up to 60k -> Tax = 0
    tax, slab, reb, mr, sur, cess = compute_individual_new_regime_tax_ay2026_27(1200000.0)
    assert_test("1C: Income INR 12L (Exact 87A INR 60k rebate boundary)", tax == 0.0 and slab == 60000.0 and reb == 60000.0, f"(Tax: INR {tax}, Slab: INR {slab}, Rebate: INR {reb})")

    # Case 1D: Income INR 12,10,000 -> Excess income = 10,000. Slab tax = 60,000 + 1500 = 61,500.
    # Marginal relief: Tax cannot exceed excess income (10,000). Tax before cess = 10,000. With 4% cess = 10,400.
    tax, slab, reb, mr, sur, cess = compute_individual_new_regime_tax_ay2026_27(1210000.0)
    assert_test("1D: Income INR 12.1L (Marginal Relief applied)", tax == 10400.0 and mr == 51500.0, f"(Tax: INR {tax}, Marginal Relief: INR {mr})")

    # Case 1E: Income INR 16L -> Slab tax: 20k + 40k + 60k = 1,20,000. Cess = 4,800. Total = 1,24,800.
    tax, slab, reb, mr, sur, cess = compute_individual_new_regime_tax_ay2026_27(1600000.0)
    assert_test("1E: Income INR 16L (Normal new regime)", tax == 124800.0 and slab == 120000.0, f"(Tax: INR {tax})")

    # Case 1F: Income INR 25L (> 24L slab 30%)
    # Slabs: 4L@0 + 4L@5%(20k) + 4L@10%(40k) + 4L@15%(60k) + 4L@20%(80k) + 4L@25%(100k) + 1L@30%(30k) = 3,30,000.
    # Cess 4% = 13,200. Total = 3,43,200.
    tax, slab, reb, mr, sur, cess = compute_individual_new_regime_tax_ay2026_27(2500000.0)
    assert_test("1F: Income INR 25L (Above 24L 30% slab)", tax == 343200.0 and slab == 330000.0, f"(Tax: INR {tax})")

    # -------------------------------------------------------------
    # 2. Section 44AD Presumptive (Small Retail & Manufacturing)
    # -------------------------------------------------------------
    print("\n--- Test Suite 2: Section 44AD Presumptive Taxation ---")

    # Case 2A: Small Retail (Turnover INR 50L, 100% digital receipts)
    # Presumptive income = 50L * 6% = 3,00,000.
    # Tax on 3L under 115BAC = 0.
    res_2a = tax_policy_resolver.resolve_tax(
        pbt=450000.0,
        annual_revenue=5000000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="retail",
        specific_business="grocery_store",
        user_inputs={"digital_receipts_pct": 100.0}
    )
    assert_test("2A: Small Retail (INR 50L turnover, 100% digital 6%)", res_2a.tax_regime == "SECTION_44AD_PRESUMPTIVE" and res_2a.annual_tax_expense == 0.0, f"(Tax: INR {res_2a.annual_tax_expense}, Regime: {res_2a.tax_regime})")

    # Case 2B: Small Retail (Turnover INR 50L, 100% cash receipts)
    # Presumptive income = 50L * 8% = 4,00,000.
    # Tax on 4L under 115BAC = 0.
    res_2b = tax_policy_resolver.resolve_tax(
        pbt=450000.0,
        annual_revenue=5000000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="retail",
        specific_business="saree_retail",
        user_inputs={"digital_receipts_pct": 0.0, "cash_receipts_pct": 100.0}
    )
    assert_test("2B: Saree Retail (INR 50L turnover, 100% cash 8%)", res_2b.tax_regime == "SECTION_44AD_PRESUMPTIVE" and res_2b.annual_tax_expense == 0.0, f"(Tax: INR {res_2b.annual_tax_expense})")

    # Case 2C: High Turnover Retail (Turnover INR 1.8 Cr, 50% digital, 50% non-digital)
    # Digital = 90L * 6% = 5.4L. Non-digital = 90L * 8% = 7.2L. Deemed profit = 12.6L.
    # Tax on 12.6L under 115BAC:
    # Slab tax: 60k + 60k * 0.15 = 69,000.
    # Marginal relief around 12L: Excess = 60,000. Slab tax (69,000) > excess (60,000) -> Tax before cess = 60,000.
    # Cess 4% = 2,400. Total tax = 62,400.
    res_2c = tax_policy_resolver.resolve_tax(
        pbt=1500000.0,
        annual_revenue=18000000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="retail",
        specific_business="saree_retail",
        user_inputs={"digital_receipts_pct": 50.0}
    )
    assert_test("2C: INR 1.8 Cr turnover, 50/50 digital split (6% & 8%)", res_2c.annual_tax_expense == 62400.0 and res_2c.provenance["presumptive_method"] == "SECTION_44AD_SPLIT_50_DIGITAL", f"(Tax: INR {res_2c.annual_tax_expense}, Method: {res_2c.provenance.get('presumptive_method')})")

    # Case 2D: Unknown receipt mode (conservative 8% policy)
    res_2d = tax_policy_resolver.resolve_tax(
        pbt=1000000.0,
        annual_revenue=15000000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="manufacturing",
        specific_business="rice_mill",
        user_inputs={}
    )
    assert_test("2D: Manufacturing rice mill with unevidenced receipt mode (conservative 8% default)", res_2d.provenance["presumptive_method"] == "SECTION_44AD_CONSERVATIVE_8_PCT", f"(Method: {res_2d.provenance.get('presumptive_method')})")

    # Case 2E: Turnover INR 2.5 Cr without 95% digital compliance -> Exceeds INR 2 Cr normal limit -> Section 115BAC regular slabs
    res_2e = tax_policy_resolver.resolve_tax(
        pbt=2500000.0,
        annual_revenue=25000000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="manufacturing",
        specific_business="spice_processing",
        user_inputs={"cash_receipts_pct": 20.0}
    )
    assert_test("2E: INR 2.5 Cr turnover with 20% cash (Exceeds INR 2 Cr limit, falls to regular 115BAC)", res_2e.tax_regime == "INDIVIDUAL_NEW_REGIME_115BAC", f"(Regime: {res_2e.tax_regime})")

    # Case 2F: Turnover INR 2.5 Cr WITH cash <= 5% -> Eligible for extended INR 3 Cr limit
    res_2f = tax_policy_resolver.resolve_tax(
        pbt=2500000.0,
        annual_revenue=25000000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="manufacturing",
        specific_business="spice_processing",
        user_inputs={"cash_receipts_pct": 3.0, "digital_receipts_pct": 97.0}
    )
    assert_test("2F: INR 2.5 Cr turnover with cash <= 5% (Eligible under extended INR 3 Cr limit)", res_2f.tax_regime == "SECTION_44AD_PRESUMPTIVE", f"(Regime: {res_2f.tax_regime})")

    # -------------------------------------------------------------
    # 3. Section 44ADA (Specified Professions ONLY)
    # -------------------------------------------------------------
    print("\n--- Test Suite 3: Section 44ADA vs Generic Services ---")

    # Case 3A: Specified Professional (Doctor / CA / Engineer / IT)
    res_3a = tax_policy_resolver.resolve_tax(
        pbt=1800000.0,
        annual_revenue=3000000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="services",
        specific_business="it_professional",
        user_inputs={}
    )
    # Deemed profit = 30L * 50% = 15L.
    # Tax on 15L under 115BAC: 4L@5%(20k) + 4L@10%(40k) + 3L@15%(45k) = 1,05,000. Cess 4% = 4,200. Total = 1,09,200.
    assert_test("3A: Specified Profession (IT Professional, 50% under 44ADA)", res_3a.tax_regime == "SECTION_44ADA_SPECIFIED_PROFESSION_PRESUMPTIVE" and res_3a.annual_tax_expense == 109200.0, f"(Regime: {res_3a.tax_regime}, Tax: INR {res_3a.annual_tax_expense})")

    # Case 3B: Generic Service (Beauty Salon: MUST NOT BE 44ADA)
    res_3b = tax_policy_resolver.resolve_tax(
        pbt=250000.0,
        annual_revenue=600000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="services",
        specific_business="beauty_salon",
        user_inputs={}
    )
    assert_test("3B: Beauty Salon (Generic service EXCLUDED from 44ADA)", res_3b.tax_regime == "SECTION_44AD_PRESUMPTIVE", f"(Regime: {res_3b.tax_regime})")

    # Case 3C: Repair Shop (Mobile Repair: MUST NOT BE 44ADA)
    res_3c = tax_policy_resolver.resolve_tax(
        pbt=200000.0,
        annual_revenue=500000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="services",
        specific_business="mobile_repair",
        user_inputs={}
    )
    assert_test("3C: Mobile Repair (Generic repair EXCLUDED from 44ADA)", res_3c.tax_regime == "SECTION_44AD_PRESUMPTIVE", f"(Regime: {res_3c.tax_regime})")

    # Case 3D: Agency / Commission Excluded from 44AD
    res_3d = tax_policy_resolver.resolve_tax(
        pbt=800000.0,
        annual_revenue=2000000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="services",
        specific_business="real_estate_agent",
        user_inputs={}
    )
    assert_test("3D: Real Estate Agent (Agency/brokerage statutorily excluded from 44AD)", res_3d.tax_regime == "INDIVIDUAL_NEW_REGIME_115BAC", f"(Regime: {res_3d.tax_regime})")

    # -------------------------------------------------------------
    # 4. Partnership Firms & LLPs
    # -------------------------------------------------------------
    print("\n--- Test Suite 4: Partnership Firm vs LLP ---")

    # Case 4A: Regular Partnership Firm within 44AD limit
    res_4a = tax_policy_resolver.resolve_tax(
        pbt=600000.0,
        annual_revenue=5000000.0,
        business_constitution="PARTNERSHIP_FIRM",
        category="retail",
        specific_business="grocery_store",
        user_inputs={"digital_receipts_pct": 100.0}
    )
    # Deemed profit = 50L * 6% = 3,00,000. Tax at 30% firm rate = 90,000. Cess 4% = 3,600. Total = 93,600.
    assert_test("4A: Partnership Firm eligible for 44AD (30% firm rate on deemed profit)", res_4a.tax_regime == "SECTION_44AD_PARTNERSHIP_PRESUMPTIVE" and res_4a.annual_tax_expense == 93600.0, f"(Regime: {res_4a.tax_regime}, Tax: INR {res_4a.annual_tax_expense})")

    # Case 4B: LLP statutorily EXCLUDED from 44AD (flat 30% + cess = 31.2%)
    res_4b = tax_policy_resolver.resolve_tax(
        pbt=600000.0,
        annual_revenue=5000000.0,
        business_constitution="LLP",
        category="retail",
        specific_business="grocery_store",
        user_inputs={}
    )
    # Tax: 6,00,000 * 31.2% = 1,87,200.
    assert_test("4B: LLP statutorily excluded from 44AD (flat 31.2% effective rate)", res_4b.tax_regime == "PARTNERSHIP_LLP_REGULAR_FLAT_30PCT" and res_4b.annual_tax_expense == 187200.0, f"(Regime: {res_4b.tax_regime}, Tax: INR {res_4b.annual_tax_expense})")

    # -------------------------------------------------------------
    # 5. Domestic Companies (Standard MSME vs Section 115BAA)
    # -------------------------------------------------------------
    print("\n--- Test Suite 5: Domestic Companies ---")

    # Case 5A: Standard Domestic Company MSME (25% + 4% cess = 26.0%)
    res_5a = tax_policy_resolver.resolve_tax(
        pbt=1000000.0,
        annual_revenue=10000000.0,
        business_constitution="COMPANY",
        category="manufacturing",
        specific_business="rice_mill",
        user_inputs={"opt_section_115baa": False}
    )
    # Tax: 10,00,000 * 25% = 2,50,000. Cess 4% = 10,000. Total = 2,60,000 (26.0%).
    assert_test("5A: Domestic Company Standard MSME (25% base + 4% cess = 26.0%)", res_5a.tax_regime == "STANDARD_DOMESTIC_COMPANY_MSME_25PCT" and res_5a.annual_tax_expense == 260000.0 and res_5a.effective_tax_rate == 26.0, f"(Regime: {res_5a.tax_regime}, Tax: INR {res_5a.annual_tax_expense}, Rate: {res_5a.effective_tax_rate}%)")

    # Case 5B: Domestic Company opting for Section 115BAA
    # 22% base + 10% statutory surcharge + 4% cess = 25.168% effective rate
    res_5b = tax_policy_resolver.resolve_tax(
        pbt=1000000.0,
        annual_revenue=10000000.0,
        business_constitution="COMPANY",
        category="manufacturing",
        specific_business="rice_mill",
        user_inputs={"opt_section_115baa": True}
    )
    # Tax: 10,00,000 * 25.168% = 2,51,680.
    assert_test("5B: Domestic Company Section 115BAA opted (22% base + 10% sur + 4% cess = 25.168%)", res_5b.tax_regime == "SECTION_115BAA_DOMESTIC_COMPANY" and res_5b.annual_tax_expense == 251680.0 and res_5b.effective_tax_rate == 25.168, f"(Regime: {res_5b.tax_regime}, Tax: INR {res_5b.annual_tax_expense}, Rate: {res_5b.effective_tax_rate}%)")

    # -------------------------------------------------------------
    # 6. Commercial Dairy Farm vs Primary Crop Cultivation
    # -------------------------------------------------------------
    print("\n--- Test Suite 6: Agriculture & Livestock Tax Treatment ---")

    # Case 6A: Commercial Dairy Farm is PGBP commercial business, NOT Section 10(1) exempt
    res_6a = tax_policy_resolver.resolve_tax(
        pbt=350000.0,
        annual_revenue=1120000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="livestock",
        specific_business="dairy_farm",
        user_inputs={}
    )
    assert_test("6A: Commercial Dairy Farm is PGBP commercial business (not Section 10(1) exempt)", res_6a.is_exempt == False and res_6a.tax_regime == "SECTION_44AD_PRESUMPTIVE", f"(Exempt: {res_6a.is_exempt}, Regime: {res_6a.tax_regime})")

    # Case 6B: Primary Crop Cultivation on land is exempt under Section 10(1)
    res_6b = tax_policy_resolver.resolve_tax(
        pbt=500000.0,
        annual_revenue=1500000.0,
        business_constitution="SOLE_PROPRIETORSHIP",
        category="agriculture",
        specific_business="crop_cultivation",
        user_inputs={}
    )
    assert_test("6B: Primary Crop Cultivation is exempt under Section 10(1)", res_6b.is_exempt == True and res_6b.tax_regime == "SECTION_10_1_AGRICULTURAL_INCOME", f"(Exempt: {res_6b.is_exempt}, Regime: {res_6b.tax_regime})")

    # -------------------------------------------------------------
    # 7. Entity Registration Clarification Handling
    # -------------------------------------------------------------
    print("\n--- Test Suite 7: Unsupported Sole-Proprietorship Default Removed ---")

    # Case 7A: Constitution missing from profile -> Provisional with clarification question
    res_7a = tax_policy_resolver.resolve_tax(
        pbt=500000.0,
        annual_revenue=2000000.0,
        business_constitution=None,
        category="retail",
        specific_business="grocery_store",
        user_inputs={}
    )
    has_q = "clarification_question" in res_7a.provenance
    assert_test("7A: Unspecified entity triggers registration question in provenance", has_q and res_7a.tax_status == "PROVISIONAL_PENDING_REGISTRATION", f"(Status: {res_7a.tax_status}, Question: {res_7a.provenance.get('clarification_question')})")

    print(f"\n=== SUMMARY: {passed} of {total} TESTS PASSED ===")
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
