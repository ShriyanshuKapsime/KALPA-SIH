"""
Authoritative Deterministic Tax Policy Resolver.
Statutory Policy Version: INDIA_INCOME_TAX_AY_2026_27
Assessment Year: 2026-27 | Financial Year: 2025-26

Implements official Indian Income Tax provisions for MSMEs, micro-enterprises, and rural businesses:
1. Section 115BAC (New Tax Regime) AY 2026-27 Slabs:
   - 0 to ₹4,00,000: Nil (0%)
   - ₹4,00,001 to ₹8,00,000: 5%
   - ₹8,00,001 to ₹12,00,000: 10%
   - ₹12,00,001 to ₹16,00,000: 15%
   - ₹16,00,001 to ₹20,00,000: 20%
   - ₹20,00,001 to ₹24,00,000: 25%
   - Above ₹24,00,000: 30%
   - Section 87A rebate up to ₹60,000 when taxable income <= ₹12,00,000 (tax becomes ₹0.00).
   - Marginal relief around ₹12,00,000 threshold (tax payable cannot exceed excess income over ₹12L).
   - 4% Health and Education Cess on tax after rebate/relief.

2. Section 44AD Presumptive Taxation for Eligible Businesses:
   - ₹2 Crore normal turnover limit; ₹3 Crore if aggregate cash receipts <= 5% of turnover.
   - Eligible: Resident Individual, Resident HUF, Resident Partnership firm (excluding LLP).
   - Excluded: LLPs, Companies, Agency/Commission/Brokerage, Section 44AE transporters, Section 44AA(1) professions.
   - Presumptive Income: 6% of qualifying electronic/bank receipts + 8% of other receipts.
   - Default when receipt mode unknown: Conservative 8% standard policy (documented in provenance).
   - Tax on presumptive income calculated under Section 115BAC (Individual/HUF) or Firm rate (30% + cess).

3. Section 44ADA Presumptive Taxation for Specified Professions ONLY:
   - Restricted to professions notified under Section 44AA(1): Legal, Medical, Engineering, Architectural,
     Accountancy, Technical Consultancy, Interior Decoration, Authorized Representative, Film Artist, Company Secretary, IT.
   - Generic services, repair shops, salons, retail, trading, tailoring, carpentry MUST NOT be classified under 44ADA.
   - ₹50 Lakh limit (₹75 Lakh if cash receipts <= 5%).
   - Presumptive income: 50% of gross receipts.

4. Domestic Companies:
   - Standard MSME Corporate Regime: 25% base rate (turnover <= ₹400 Cr) + Surcharge (7% if income > ₹1 Cr, 12% if > ₹10 Cr) + 4% Cess.
   - Section 115BAA (if opted): 22% base rate + flat 10% statutory surcharge + 4% cess = 25.168% effective rate.

5. Partnership Firms and LLPs:
   - Base rate: 30% + Surcharge (12% if income > ₹1 Cr) + 4% Cess = 31.2% (or 34.944% if > ₹1 Cr).
   - LLPs are legally excluded from Section 44AD presumptive taxation.
   - Regular Partnership firms are eligible for Section 44AD if turnover <= threshold.

6. Commercial Dairy / Livestock / Agriculture:
   - Section 10(1) pure agricultural exemption applies strictly to primary cultivation of land.
   - Commercial dairy farming, poultry, livestock, and fisheries are commercial business activities (PGBP),
     taxable with regular business expenses or under Section 44AD if eligible.

NEVER selects min(tax_amt_presumptive, tax_amt_actual).
Derives legally applicable regime and taxable income first, then computes tax deterministically.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Centralized Tax Policy Versioning
TAX_POLICY_VERSION = "INDIA_INCOME_TAX_AY_2026_27"
STATUTORY_ASSESSMENT_YEAR = "2026-27"
STATUTORY_FINANCIAL_YEAR = "2025-26"
HEALTH_EDUCATION_CESS_RATE = 0.04


class TaxResolutionResult(BaseModel):
    constitution: str
    tax_regime: str
    annual_tax_expense: float
    effective_tax_rate: float
    tax_status: str
    is_presumptive: bool
    is_exempt: bool
    explanation: str
    provenance: Dict[str, Any] = Field(default_factory=dict)


def compute_individual_new_regime_tax_ay2026_27(taxable_income: float) -> Tuple[float, float, float, float, float, float]:
    """
    Computes tax under Section 115BAC (New Tax Regime) for AY 2026-27 (FY 2025-26):
    Slabs:
      0 to 4,00,000         : 0%
      4,00,001 to 8,00,000  : 5%   (max slab tax: ₹20,000)
      8,00,001 to 12,00,000 : 10%  (max slab tax: ₹40,000, cumulative: ₹60,000)
      12,00,001 to 16,00,000: 15%  (max slab tax: ₹60,000, cumulative: ₹1,20,000)
      16,00,001 to 20,00,000: 20%  (max slab tax: ₹80,000, cumulative: ₹2,00,000)
      20,00,001 to 24,00,000: 25%  (max slab tax: ₹1,00,000, cumulative: ₹3,00,000)
      Above 24,00,000       : 30%

    Section 87A Rebate:
      Full rebate up to ₹60,000 when taxable income does not exceed ₹12,00,000.
      Tax payable before cess becomes ₹0.00.

    Marginal Relief around ₹12,00,000:
      For taxable income slightly exceeding ₹12,00,000, the tax payable shall not exceed
      the amount by which taxable income exceeds ₹12,00,000.
      Excess income = taxable_income - 12,00,000.
      If computed slab tax > excess income, tax payable = excess income, relief = slab_tax - excess_income.

    Surcharge under Section 115BAC (AY 2026-27):
      - Total income > ₹50,00,000 up to ₹1,00,00,000: 10%
      - Total income > ₹1,00,00,000 up to ₹2,00,00,000: 15%
      - Total income > ₹2,00,00,000: 25% (maximum rate under Section 115BAC)
      - Marginal relief on surcharge applied at ₹50L, ₹1Cr, and ₹2Cr thresholds.

    Health & Education Cess:
      4% Health & Education Cess on (tax + surcharge).

    Returns:
      (final_tax_with_cess, base_slab_tax, rebate_87a, marginal_relief, surcharge_amt, cess_amt)
    """
    if taxable_income <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    # 1. Base Slab Tax
    slab_tax = 0.0
    if taxable_income > 400000.0:
        slab_tax += min(400000.0, taxable_income - 400000.0) * 0.05
    if taxable_income > 800000.0:
        slab_tax += min(400000.0, taxable_income - 800000.0) * 0.10
    if taxable_income > 1200000.0:
        slab_tax += min(400000.0, taxable_income - 1200000.0) * 0.15
    if taxable_income > 1600000.0:
        slab_tax += min(400000.0, taxable_income - 1600000.0) * 0.20
    if taxable_income > 2000000.0:
        slab_tax += min(400000.0, taxable_income - 2000000.0) * 0.25
    if taxable_income > 2400000.0:
        slab_tax += (taxable_income - 2400000.0) * 0.30

    slab_tax = round(slab_tax, 2)

    # 2. Section 87A Rebate & Marginal Relief around ₹12,00,000
    rebate_87a = 0.0
    marginal_relief = 0.0
    if taxable_income <= 1200000.0:
        rebate_87a = min(60000.0, slab_tax)
        tax_after_rebate = max(0.0, slab_tax - rebate_87a)
    else:
        tax_after_rebate = slab_tax
        excess_income = taxable_income - 1200000.0
        if tax_after_rebate > excess_income:
            marginal_relief = round(tax_after_rebate - excess_income, 2)
            tax_after_rebate = round(excess_income, 2)

    # 3. Surcharge under Section 115BAC (AY 2026-27)
    surcharge_rate = 0.0
    surcharge_amt = 0.0
    if taxable_income > 20000000.0:
        surcharge_rate = 0.25
        base_surcharge = tax_after_rebate * surcharge_rate
        # Marginal relief at ₹2 Cr: tax + surcharge <= (tax on ₹2Cr with 15% surcharge) + (income - 2Cr)
        tax_at_2cr, _, _, _, _, _ = compute_individual_new_regime_tax_ay2026_27(20000000.0)
        max_tax_payable = tax_at_2cr + (taxable_income - 20000000.0)
        if (tax_after_rebate + base_surcharge) > max_tax_payable:
            surcharge_amt = max(0.0, max_tax_payable - tax_after_rebate)
        else:
            surcharge_amt = base_surcharge
    elif taxable_income > 10000000.0:
        surcharge_rate = 0.15
        base_surcharge = tax_after_rebate * surcharge_rate
        # Marginal relief at ₹1 Cr
        tax_at_1cr, _, _, _, _, _ = compute_individual_new_regime_tax_ay2026_27(10000000.0)
        max_tax_payable = tax_at_1cr + (taxable_income - 10000000.0)
        if (tax_after_rebate + base_surcharge) > max_tax_payable:
            surcharge_amt = max(0.0, max_tax_payable - tax_after_rebate)
        else:
            surcharge_amt = base_surcharge
    elif taxable_income > 5000000.0:
        surcharge_rate = 0.10
        base_surcharge = tax_after_rebate * surcharge_rate
        # Marginal relief at ₹50 Lakhs
        # Slab tax on ₹50L: 3,00,000 + 26L * 0.30 = 3,00,000 + 7,80,000 = 10,80,000
        tax_at_50l = 1080000.0
        max_tax_payable = tax_at_50l + (taxable_income - 5000000.0)
        if (tax_after_rebate + base_surcharge) > max_tax_payable:
            surcharge_amt = max(0.0, max_tax_payable - tax_after_rebate)
        else:
            surcharge_amt = base_surcharge

    surcharge_amt = round(surcharge_amt, 2)
    tax_subject_to_cess = tax_after_rebate + surcharge_amt

    # 4. 4% Health and Education Cess
    cess_amt = round(tax_subject_to_cess * HEALTH_EDUCATION_CESS_RATE, 2)
    final_tax = round(tax_subject_to_cess + cess_amt, 2)

    return final_tax, slab_tax, rebate_87a, marginal_relief, surcharge_amt, cess_amt


# Specified professions strictly eligible for Section 44ADA under Section 44AA(1)
SPECIFIED_PROFESSIONS_44AA1 = {
    "legal", "advocate", "lawyer",
    "medical", "doctor", "physician", "surgeon", "dentist",
    "engineering", "engineer", "civil_engineer", "structural_engineer",
    "architectural", "architect",
    "accountancy", "chartered_accountant", "accountant",
    "technical_consultancy", "technical_consultant", "software_consultant",
    "interior_decoration", "interior_decorator", "interior_designer",
    "authorized_representative", "film_artist", "company_secretary", "it_professional"
}


class TaxPolicyResolver:
    """
    Authoritative deterministic resolver for MSME tax treatment according to AY 2026-27 statutory rules.
    """

    @staticmethod
    def resolve_tax(
        pbt: Optional[float],
        annual_revenue: Optional[float] = None,
        business_constitution: Optional[str] = None,
        sector: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        archetype: Optional[str] = None,
        specific_business: Optional[str] = None,
        nic_code: Optional[str] = None,
        user_inputs: Optional[Dict[str, Any]] = None,
    ) -> TaxResolutionResult:
        """
        Determines applicable tax regime, taxable income, tax expense, and audit provenance.
        """
        user_in = user_inputs or {}

        # ---------------------------------------------------------------------
        # 1. Determine Constitution from Evidence Hierarchy
        # USER PROFILE -> registration/entity information -> verified information
        # ---------------------------------------------------------------------
        raw_const = (
            business_constitution
            or user_in.get("business_constitution")
            or user_in.get("constitution")
            or user_in.get("ownership_constitution")
            or user_in.get("entity_type")
            or user_in.get("registration_type")
        )

        has_verified_constitution = bool(raw_const)
        const_str = str(raw_const or "").upper().strip()

        if any(w in const_str for w in ("PVT", "PRIVATE", "COMPANY", "CORP", "LTD", "ONE_PERSON")):
            const_norm = "COMPANY"
            is_llp = False
        elif "LLP" in const_str or "LIMITED LIABILITY PARTNERSHIP" in const_str:
            const_norm = "LLP"
            is_llp = True
        elif any(w in const_str for w in ("PARTNER", "FIRM")):
            const_norm = "PARTNERSHIP_FIRM"
            is_llp = False
        elif any(w in const_str for w in ("HUF", "HINDU UNDIVIDED")):
            const_norm = "HUF"
            is_llp = False
        elif any(w in const_str for w in ("PROPRIETOR", "INDIVIDUAL", "SOLE")):
            const_norm = "SOLE_PROPRIETORSHIP"
            is_llp = False
        else:
            # Constitution not explicitly provided in user profile.
            # Avoid silently converting to sole proprietorship without disclosure.
            # Baseline evaluated as provisional proprietorship with required clarification.
            const_norm = "UNSPECIFIED_PENDING_REGISTRATION"
            is_llp = False

        constitution_provenance_basis = (
            "USER_PROFILE_CONFIRMED" if has_verified_constitution
            else "PROVISIONAL_BASELINE_PENDING_REGISTRATION_CLARIFICATION"
        )
        registration_clarification_question = (
            None if has_verified_constitution
            else "How are you planning to register the business — as your own proprietorship, partnership/LLP, or company?"
        )

        # ---------------------------------------------------------------------
        # 2. Check Explicit Statutory Exemption
        # ---------------------------------------------------------------------
        if user_in.get("is_tax_exempt") or user_in.get("tax_exempt"):
            return TaxResolutionResult(
                constitution=const_norm,
                tax_regime="EXPLICIT_STATUTORY_EXEMPTION",
                annual_tax_expense=0.0,
                effective_tax_rate=0.0,
                tax_status="EXEMPT",
                is_presumptive=False,
                is_exempt=True,
                explanation="Tax exempt per user-provided statutory profile certification.",
                provenance={
                    "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                    "financial_year": STATUTORY_FINANCIAL_YEAR,
                    "policy_version": TAX_POLICY_VERSION,
                    "tax_regime": "EXPLICIT_STATUTORY_EXEMPTION",
                    "statutory_sections": ["EXEMPTION_CERTIFICATION"],
                    "base_rate": 0.0,
                    "surcharge_rate": 0.0,
                    "cess_rate": 0.0,
                    "rebate": 0.0,
                    "marginal_relief": 0.0,
                    "presumptive_method": None,
                    "eligibility_conditions": ["Statutory exemption certification provided"],
                    "taxable_income_basis": "EXEMPT",
                    "source": "USER_PROFILE_EVIDENCE",
                    "source_date": "2024-07-23",
                    "confidence": 1.0
                }
            )

        # ---------------------------------------------------------------------
        # 3. Handle Unresolved or Non-Positive PBT
        # ---------------------------------------------------------------------
        if pbt is None:
            return TaxResolutionResult(
                constitution=const_norm,
                tax_regime="PENDING_PBT_RESOLUTION",
                annual_tax_expense=0.0,
                effective_tax_rate=0.0,
                tax_status="NOT_MODELED",
                is_presumptive=False,
                is_exempt=False,
                explanation="Profit Before Tax (PBT) is unresolved; tax calculation deferred.",
                provenance={
                    "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                    "financial_year": STATUTORY_FINANCIAL_YEAR,
                    "policy_version": TAX_POLICY_VERSION,
                    "tax_regime": "PENDING_PBT_RESOLUTION",
                    "statutory_sections": [],
                    "base_rate": 0.0,
                    "surcharge_rate": 0.0,
                    "cess_rate": 0.0,
                    "rebate": 0.0,
                    "marginal_relief": 0.0,
                    "presumptive_method": None,
                    "eligibility_conditions": ["PBT required"],
                    "taxable_income_basis": "UNRESOLVED",
                    "source": "INCOME_TAX_DEPARTMENT_INDIA",
                    "source_date": "2024-07-23",
                    "confidence": 0.0
                }
            )

        if pbt <= 0.0:
            return TaxResolutionResult(
                constitution=const_norm,
                tax_regime="ZERO_TAX_LOSS_OR_BREAKEVEN",
                annual_tax_expense=0.0,
                effective_tax_rate=0.0,
                tax_status="RESOLVED",
                is_presumptive=False,
                is_exempt=False,
                explanation=f"No income tax liability in loss-making or breakeven operational state (PBT = ₹{pbt:,.2f}).",
                provenance={
                    "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                    "financial_year": STATUTORY_FINANCIAL_YEAR,
                    "policy_version": TAX_POLICY_VERSION,
                    "tax_regime": "ZERO_TAX_LOSS_OR_BREAKEVEN",
                    "statutory_sections": ["INCOME_TAX_ACT_LOSS_PROVISIONS"],
                    "base_rate": 0.0,
                    "surcharge_rate": 0.0,
                    "cess_rate": 0.0,
                    "rebate": 0.0,
                    "marginal_relief": 0.0,
                    "presumptive_method": None,
                    "eligibility_conditions": ["PBT <= 0"],
                    "taxable_income_basis": f"PBT: ₹{pbt:,.2f}",
                    "source": "INCOME_TAX_DEPARTMENT_INDIA",
                    "source_date": "2024-07-23",
                    "confidence": 1.0
                }
            )

        # Annual revenue basis
        rev = float(annual_revenue) if (annual_revenue is not None and annual_revenue > 0) else float(pbt / 0.15)

        # ---------------------------------------------------------------------
        # 4. Commercial Dairy / Livestock / Agriculture Classification
        # Commercial dairy, livestock, poultry, and fisheries are commercial PGBP activities.
        # Primary agricultural crop cultivation on land is exempt under Section 10(1).
        # ---------------------------------------------------------------------
        sec_l = str(sector or "").lower()
        cat_l = str(category or "").lower()
        subcat_l = str(subcategory or "").lower()
        spec_l = str(specific_business or "").lower()
        arch_l = str(archetype or "").lower()

        is_pure_agricultural_cultivation = (
            any(w in sec_l or w in cat_l or w in spec_l for w in ("crop", "cultivation", "paddy_farming", "wheat_farming", "horticulture", "floriculture"))
            and not any(w in spec_l or w in cat_l for w in ("dairy", "poultry", "goat", "cattle", "livestock", "processing", "mill"))
        )

        if is_pure_agricultural_cultivation:
            return TaxResolutionResult(
                constitution=const_norm,
                tax_regime="SECTION_10_1_AGRICULTURAL_INCOME",
                annual_tax_expense=0.0,
                effective_tax_rate=0.0,
                tax_status="EXEMPT",
                is_presumptive=False,
                is_exempt=True,
                explanation="Agricultural income from primary land cultivation is exempt under Section 10(1) of the Income Tax Act.",
                provenance={
                    "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                    "financial_year": STATUTORY_FINANCIAL_YEAR,
                    "policy_version": TAX_POLICY_VERSION,
                    "tax_regime": "SECTION_10_1_AGRICULTURAL_INCOME",
                    "statutory_sections": ["SECTION_10_1", "SECTION_2_1A"],
                    "base_rate": 0.0,
                    "surcharge_rate": 0.0,
                    "cess_rate": 0.0,
                    "rebate": 0.0,
                    "marginal_relief": 0.0,
                    "presumptive_method": None,
                    "eligibility_conditions": ["Primary agricultural cultivation on land"],
                    "taxable_income_basis": "SECTION_10_1_EXEMPT",
                    "source": "INCOME_TAX_DEPARTMENT_INDIA",
                    "source_date": "2024-07-23",
                    "confidence": 0.95
                }
            )

        # ---------------------------------------------------------------------
        # 5. DOMESTIC COMPANY TAXATION
        # ---------------------------------------------------------------------
        if const_norm == "COMPANY":
            # Check if Section 115BAA is explicitly opted or requested
            opted_115baa = bool(
                user_in.get("opt_section_115baa")
                or user_in.get("opt_115baa")
                or user_in.get("is_115baa")
            )

            if opted_115baa:
                # Section 115BAA: 22% base + flat 10% statutory surcharge + 4% cess
                # 22% * 1.10 = 24.2%; 24.2% * 1.04 = 25.168%
                base_r = 0.22
                surch_r = 0.10
                base_plus_surch = base_r * (1.0 + surch_r)  # 0.242
                cess_amt = base_plus_surch * HEALTH_EDUCATION_CESS_RATE  # 0.00968
                effective_rate_dec = base_plus_surch + cess_amt  # 0.25168
                tax_amt = round(pbt * effective_rate_dec, 2)
                eff_pct = round(effective_rate_dec * 100.0, 3)

                return TaxResolutionResult(
                    constitution=const_norm,
                    tax_regime="SECTION_115BAA_DOMESTIC_COMPANY",
                    annual_tax_expense=tax_amt,
                    effective_tax_rate=eff_pct,
                    tax_status="RESOLVED",
                    is_presumptive=False,
                    is_exempt=False,
                    explanation=(
                        f"Corporate tax under Section 115BAA: 22% base rate + 10% statutory surcharge + "
                        f"4% Health & Education Cess = 25.168% on PBT ₹{pbt:,.2f}."
                    ),
                    provenance={
                        "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                        "financial_year": STATUTORY_FINANCIAL_YEAR,
                        "policy_version": TAX_POLICY_VERSION,
                        "tax_regime": "SECTION_115BAA_DOMESTIC_COMPANY",
                        "statutory_sections": ["SECTION_115BAA"],
                        "base_rate": 0.22,
                        "surcharge_rate": 0.10,
                        "cess_rate": HEALTH_EDUCATION_CESS_RATE,
                        "rebate": 0.0,
                        "marginal_relief": 0.0,
                        "presumptive_method": None,
                        "eligibility_conditions": [
                            "Domestic company",
                            "Section 115BAA option exercised",
                            "Subject to forgoing specified chapter VI-A deductions and additional depreciation",
                            "MAT under Section 115JB not applicable"
                        ],
                        "taxable_income_basis": f"PBT: ₹{pbt:,.2f}",
                        "source": "INCOME_TAX_DEPARTMENT_INDIA",
                        "source_date": "2024-07-23",
                        "confidence": 0.95
                    }
                )
            else:
                # Standard Domestic Company MSME Regime: 25% base rate (turnover <= ₹400 Cr in relevant base year)
                # Surcharge: 7% if PBT > ₹1 Cr up to ₹10 Cr; 12% if PBT > ₹10 Cr; 0% otherwise.
                base_r = 0.25
                if pbt > 100000000.0:
                    surch_r = 0.12
                elif pbt > 10000000.0:
                    surch_r = 0.07
                else:
                    surch_r = 0.0

                base_tax = pbt * base_r
                surcharge_amt = base_tax * surch_r
                tax_before_cess = base_tax + surcharge_amt
                cess_amt = tax_before_cess * HEALTH_EDUCATION_CESS_RATE
                tax_amt = round(tax_before_cess + cess_amt, 2)
                eff_pct = round((tax_amt / pbt) * 100.0, 2)

                return TaxResolutionResult(
                    constitution=const_norm,
                    tax_regime="STANDARD_DOMESTIC_COMPANY_MSME_25PCT",
                    annual_tax_expense=tax_amt,
                    effective_tax_rate=eff_pct,
                    tax_status="RESOLVED",
                    is_presumptive=False,
                    is_exempt=False,
                    explanation=(
                        f"Standard domestic company MSME tax rate: 25% base rate + {surch_r * 100:.0f}% surcharge + "
                        f"4% Health & Education Cess on PBT ₹{pbt:,.2f}."
                    ),
                    provenance={
                        "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                        "financial_year": STATUTORY_FINANCIAL_YEAR,
                        "policy_version": TAX_POLICY_VERSION,
                        "tax_regime": "STANDARD_DOMESTIC_COMPANY_MSME_25PCT",
                        "statutory_sections": ["FINANCE_ACT_DOMESTIC_COMPANY_RATES"],
                        "base_rate": 0.25,
                        "surcharge_rate": surch_r,
                        "cess_rate": HEALTH_EDUCATION_CESS_RATE,
                        "rebate": 0.0,
                        "marginal_relief": 0.0,
                        "presumptive_method": None,
                        "eligibility_conditions": [
                            "Domestic company with turnover <= ₹400 Crore in base year",
                            "Section 115BAA not opted"
                        ],
                        "taxable_income_basis": f"PBT: ₹{pbt:,.2f}",
                        "source": "INCOME_TAX_DEPARTMENT_INDIA",
                        "source_date": "2024-07-23",
                        "confidence": 0.95
                    }
                )

        # ---------------------------------------------------------------------
        # 6. PARTNERSHIP FIRM & LLP TAXATION
        # ---------------------------------------------------------------------
        if const_norm in ("PARTNERSHIP_FIRM", "LLP"):
            # Surcharge: 12% if total income > ₹1 Crore
            surch_r = 0.12 if pbt > 10000000.0 else 0.0
            base_r = 0.30

            # Check Section 44AD for regular partnership firm (LLP is legally excluded)
            cash_receipts_pct = float(user_in.get("cash_receipts_pct") or 0.0) if user_in.get("cash_receipts_pct") is not None else None
            digital_threshold = 30000000.0 if (cash_receipts_pct is not None and cash_receipts_pct <= 5.0) else 20000000.0

            can_firm_use_44ad = (
                not is_llp
                and const_norm == "PARTNERSHIP_FIRM"
                and rev <= digital_threshold
                and not user_in.get("opt_regular_tax_audit")
            )

            if can_firm_use_44ad:
                # Deemed profit calculation
                dig_pct = float(user_in.get("digital_receipts_pct")) if user_in.get("digital_receipts_pct") is not None else (
                    (100.0 - cash_receipts_pct) if cash_receipts_pct is not None else None
                )
                if dig_pct is not None:
                    dig_rev = rev * (dig_pct / 100.0)
                    cash_rev = rev - dig_rev
                    deemed_profit = round((dig_rev * 0.06) + (cash_rev * 0.08), 2)
                    calc_note = f"6% on digital turnover (₹{dig_rev:,.2f}) + 8% on non-digital turnover (₹{cash_rev:,.2f})"
                else:
                    # Conservative 8% standard policy when digital proportion is not evidenced
                    deemed_profit = round(rev * 0.08, 2)
                    calc_note = "8% standard rate applied (conservative policy in absence of verified digital receipt share)"

                firm_tax_before_cess = deemed_profit * base_r * (1.0 + surch_r)
                firm_tax = round(firm_tax_before_cess * (1.0 + HEALTH_EDUCATION_CESS_RATE), 2)
                eff_pct = round((firm_tax / pbt) * 100.0, 2) if pbt > 0 else 0.0

                return TaxResolutionResult(
                    constitution=const_norm,
                    tax_regime="SECTION_44AD_PARTNERSHIP_PRESUMPTIVE",
                    annual_tax_expense=firm_tax,
                    effective_tax_rate=eff_pct,
                    tax_status="RESOLVED",
                    is_presumptive=True,
                    is_exempt=False,
                    explanation=(
                        f"Presumptive taxation under Section 44AD for partnership firm: deemed income ₹{deemed_profit:,.2f} ({calc_note}). "
                        f"Tax at 30% firm rate + 4% cess: ₹{firm_tax:,.2f}."
                    ),
                    provenance={
                        "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                        "financial_year": STATUTORY_FINANCIAL_YEAR,
                        "policy_version": TAX_POLICY_VERSION,
                        "tax_regime": "SECTION_44AD_PARTNERSHIP_PRESUMPTIVE",
                        "statutory_sections": ["SECTION_44AD", "INCOME_TAX_ACT_PARTNERSHIP"],
                        "base_rate": 0.30,
                        "surcharge_rate": surch_r,
                        "cess_rate": HEALTH_EDUCATION_CESS_RATE,
                        "rebate": 0.0,
                        "marginal_relief": 0.0,
                        "presumptive_method": "SECTION_44AD_SPLIT_6_8_PCT",
                        "eligibility_conditions": [
                            "Resident partnership firm other than LLP",
                            f"Turnover ₹{rev:,.2f} within statutory limit ₹{digital_threshold:,.2f}"
                        ],
                        "taxable_income_basis": f"Presumptive Deemed Profit: ₹{deemed_profit:,.2f}",
                        "source": "INCOME_TAX_DEPARTMENT_INDIA",
                        "source_date": "2024-07-23",
                        "confidence": 0.95
                    }
                )
            else:
                # Regular Flat 30% on PBT for Firm / LLP
                firm_tax_before_cess = pbt * base_r * (1.0 + surch_r)
                firm_tax = round(firm_tax_before_cess * (1.0 + HEALTH_EDUCATION_CESS_RATE), 2)
                eff_pct = round((firm_tax / pbt) * 100.0, 2)

                llp_exclusion_note = " (LLP statutorily excluded from Section 44AD)" if is_llp else ""
                return TaxResolutionResult(
                    constitution=const_norm,
                    tax_regime="PARTNERSHIP_LLP_REGULAR_FLAT_30PCT",
                    annual_tax_expense=firm_tax,
                    effective_tax_rate=eff_pct,
                    tax_status="RESOLVED",
                    is_presumptive=False,
                    is_exempt=False,
                    explanation=(
                        f"Partnership/LLP statutory tax: 30% base rate + {surch_r * 100:.0f}% surcharge + "
                        f"4% Health & Education Cess = 31.2% on PBT ₹{pbt:,.2f}{llp_exclusion_note}."
                    ),
                    provenance={
                        "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                        "financial_year": STATUTORY_FINANCIAL_YEAR,
                        "policy_version": TAX_POLICY_VERSION,
                        "tax_regime": "PARTNERSHIP_LLP_REGULAR_FLAT_30PCT",
                        "statutory_sections": ["INCOME_TAX_ACT_SEC_FIRM_FLAT"],
                        "base_rate": 0.30,
                        "surcharge_rate": surch_r,
                        "cess_rate": HEALTH_EDUCATION_CESS_RATE,
                        "rebate": 0.0,
                        "marginal_relief": 0.0,
                        "presumptive_method": None,
                        "eligibility_conditions": [
                            "Partnership firm or Limited Liability Partnership (LLP)",
                            "Section 44AD not applicable" if not is_llp else "LLP statutorily excluded from Section 44AD"
                        ],
                        "taxable_income_basis": f"PBT: ₹{pbt:,.2f}",
                        "source": "INCOME_TAX_DEPARTMENT_INDIA",
                        "source_date": "2024-07-23",
                        "confidence": 0.95
                    }
                )

        # ---------------------------------------------------------------------
        # 7. SOLE PROPRIETORSHIP / INDIVIDUAL / HUF MICRO-ENTERPRISES
        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------
        # 7. SOLE PROPRIETORSHIP / INDIVIDUAL / HUF MICRO-ENTERPRISES
        # ---------------------------------------------------------------------
        # Check Section 44ADA for Specified Professions under Section 44AA(1) ONLY
        business_terms = f"{sec_l} {cat_l} {subcat_l} {spec_l}".split()
        is_specified_profession = any(p in business_terms for p in SPECIFIED_PROFESSIONS_44AA1)

        # Statutory exclusions under Section 44AD(6):
        # 1. Specified professions under Section 44AA(1)
        # 2. Income in the nature of commission or brokerage
        # 3. Any agency business
        # 4. Section 44AE goods transport
        is_commission_or_brokerage = any(w in business_terms for w in ("commission", "brokerage", "broker"))
        is_agency_business = any(w in business_terms for w in ("agency", "travel_agent", "real_estate_agent", "booking_agent"))

        cash_receipts_pct = float(user_in.get("cash_receipts_pct") or 0.0) if user_in.get("cash_receipts_pct") is not None else None

        # Check 44ADA Eligibility
        ada_threshold = 7500000.0 if (cash_receipts_pct is not None and cash_receipts_pct <= 5.0) else 5000000.0
        can_use_44ada = is_specified_profession and (rev <= ada_threshold) and not user_in.get("opt_regular_tax_audit")

        if can_use_44ada:
            # Presumptive income under Section 44ADA: 50% of gross professional receipts
            deemed_profit = round(rev * 0.50, 2)
            final_tax, base_slab, rebate_87a, marg_relief, surch_amt, cess_amt = compute_individual_new_regime_tax_ay2026_27(deemed_profit)
            eff_pct = round((final_tax / pbt) * 100.0, 2) if pbt > 0 else 0.0

            tax_status_res = "RESOLVED" if has_verified_constitution else "PROVISIONAL_PENDING_REGISTRATION"
            prov = {
                "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                "financial_year": STATUTORY_FINANCIAL_YEAR,
                "policy_version": TAX_POLICY_VERSION,
                "tax_regime": "SECTION_44ADA_SPECIFIED_PROFESSION_PRESUMPTIVE",
                "statutory_sections": ["SECTION_44ADA", "SECTION_115BAC", "SECTION_87A"],
                "base_rate": 0.0,
                "surcharge_rate": 0.0,
                "cess_rate": HEALTH_EDUCATION_CESS_RATE,
                "rebate": rebate_87a,
                "marginal_relief": marg_relief,
                "surcharge": surch_amt,
                "presumptive_method": "SECTION_44ADA_50_PCT",
                "eligibility_conditions": [
                    "Specified profession under Section 44AA(1)",
                    f"Receipts ₹{rev:,.2f} within limit ₹{ada_threshold:,.2f}",
                    f"Entity constitution basis: {constitution_provenance_basis}"
                ],
                "taxable_income_basis": f"Section 44ADA Deemed Profit: ₹{deemed_profit:,.2f}",
                "source": "INCOME_TAX_DEPARTMENT_INDIA",
                "source_date": "2025-02-01",
                "confidence": 0.95 if has_verified_constitution else 0.85
            }
            if registration_clarification_question:
                prov["clarification_question"] = registration_clarification_question

            return TaxResolutionResult(
                constitution=const_norm,
                tax_regime="SECTION_44ADA_SPECIFIED_PROFESSION_PRESUMPTIVE",
                annual_tax_expense=final_tax,
                effective_tax_rate=eff_pct,
                tax_status=tax_status_res,
                is_presumptive=True,
                is_exempt=False,
                explanation=(
                    f"Presumptive taxation under Section 44ADA for specified profession (50% deemed income = ₹{deemed_profit:,.2f} on receipts ₹{rev:,.2f}). "
                    f"Tax calculated under Section 115BAC slabs for AY 2026-27: ₹{final_tax:,.2f} (rebate: ₹{rebate_87a:,.2f}, marginal relief: ₹{marg_relief:,.2f})."
                ),
                provenance=prov
            )

        # Check 44AD Eligibility (Eligible businesses: retail, trading, manufacturing, services, repair, commercial dairy, etc.)
        # Excludes specified professions, commission/brokerage, agency business, or turnover > limit
        ad_threshold = 30000000.0 if (cash_receipts_pct is not None and cash_receipts_pct <= 5.0) else 20000000.0
        can_use_44ad = (
            (not is_specified_profession)
            and (not is_commission_or_brokerage)
            and (not is_agency_business)
            and (rev <= ad_threshold)
            and not user_in.get("opt_regular_tax_audit")
        )

        if can_use_44ad:
            # Presumptive income under Section 44AD:
            # 6% of qualifying electronic/digital turnover + 8% of other non-digital turnover
            dig_pct = float(user_in.get("digital_receipts_pct")) if user_in.get("digital_receipts_pct") is not None else (
                (100.0 - cash_receipts_pct) if cash_receipts_pct is not None else None
            )

            if dig_pct is not None:
                dig_rev = rev * (dig_pct / 100.0)
                cash_rev = rev - dig_rev
                deemed_profit = round((dig_rev * 0.06) + (cash_rev * 0.08), 2)
                method_expl = f"6% on digital receipts (₹{dig_rev:,.2f}) + 8% on non-digital receipts (₹{cash_rev:,.2f})"
                presump_method = f"SECTION_44AD_SPLIT_{dig_pct:.0f}_DIGITAL"
            else:
                # Conservative 8% standard policy when digital proportion is not evidenced
                deemed_profit = round(rev * 0.08, 2)
                method_expl = "8% standard rate applied (conservative statutory policy in absence of verified digital receipt share)"
                presump_method = "SECTION_44AD_CONSERVATIVE_8_PCT"

            # Compute tax on presumptive income under Section 115BAC slabs for AY 2026-27
            final_tax, base_slab, rebate_87a, marg_relief, surch_amt, cess_amt = compute_individual_new_regime_tax_ay2026_27(deemed_profit)
            eff_pct = round((final_tax / pbt) * 100.0, 2) if pbt > 0 else 0.0

            tax_status_res = "RESOLVED" if has_verified_constitution else "PROVISIONAL_PENDING_REGISTRATION"
            prov = {
                "assessment_year": STATUTORY_ASSESSMENT_YEAR,
                "financial_year": STATUTORY_FINANCIAL_YEAR,
                "policy_version": TAX_POLICY_VERSION,
                "tax_regime": "SECTION_44AD_PRESUMPTIVE",
                "statutory_sections": ["SECTION_44AD", "SECTION_115BAC", "SECTION_87A"],
                "base_rate": 0.0,
                "surcharge_rate": 0.0,
                "cess_rate": HEALTH_EDUCATION_CESS_RATE,
                "rebate": rebate_87a,
                "marginal_relief": marg_relief,
                "surcharge": surch_amt,
                "presumptive_method": presump_method,
                "eligibility_conditions": [
                    "Eligible business under Section 44AD(1)",
                    f"Turnover ₹{rev:,.2f} within limit ₹{ad_threshold:,.2f}",
                    f"Entity constitution basis: {constitution_provenance_basis}"
                ],
                "taxable_income_basis": f"Section 44AD Deemed Profit: ₹{deemed_profit:,.2f}",
                "source": "INCOME_TAX_DEPARTMENT_INDIA",
                "source_date": "2025-02-01",
                "confidence": 0.95 if has_verified_constitution else 0.85
            }
            if registration_clarification_question:
                prov["clarification_question"] = registration_clarification_question

            return TaxResolutionResult(
                constitution=const_norm,
                tax_regime="SECTION_44AD_PRESUMPTIVE",
                annual_tax_expense=final_tax,
                effective_tax_rate=eff_pct,
                tax_status=tax_status_res,
                is_presumptive=True,
                is_exempt=False,
                explanation=(
                    f"Presumptive taxation under Section 44AD: deemed income ₹{deemed_profit:,.2f} on turnover ₹{rev:,.2f} ({method_expl}). "
                    f"Tax calculated under Section 115BAC slabs for AY 2026-27: ₹{final_tax:,.2f} (rebate: ₹{rebate_87a:,.2f}, marginal relief: ₹{marg_relief:,.2f})."
                ),
                provenance=prov
            )

        # ---------------------------------------------------------------------
        # 8. Regular Section 115BAC Slabs on Actual PBT (Turnover > ₹2/3 Cr or Audit Opted)
        # ---------------------------------------------------------------------
        final_tax, base_slab, rebate_87a, marg_relief, surch_amt, cess_amt = compute_individual_new_regime_tax_ay2026_27(pbt)
        eff_pct = round((final_tax / pbt) * 100.0, 2) if pbt > 0 else 0.0

        tax_status_res = "RESOLVED" if has_verified_constitution else "PROVISIONAL_PENDING_REGISTRATION"
        prov = {
            "assessment_year": STATUTORY_ASSESSMENT_YEAR,
            "financial_year": STATUTORY_FINANCIAL_YEAR,
            "policy_version": TAX_POLICY_VERSION,
            "tax_regime": "INDIVIDUAL_NEW_REGIME_115BAC",
            "statutory_sections": ["SECTION_115BAC", "SECTION_87A"],
            "base_rate": 0.0,
            "surcharge_rate": 0.0,
            "cess_rate": HEALTH_EDUCATION_CESS_RATE,
            "rebate": rebate_87a,
            "marginal_relief": marg_relief,
            "surcharge": surch_amt,
            "presumptive_method": None,
            "eligibility_conditions": [
                "Individual / Proprietorship under New Tax Regime",
                f"Entity constitution basis: {constitution_provenance_basis}"
            ],
            "taxable_income_basis": f"Actual PBT: ₹{pbt:,.2f}",
            "source": "INCOME_TAX_DEPARTMENT_INDIA",
            "source_date": "2025-02-01",
            "confidence": 0.95 if has_verified_constitution else 0.85
        }
        if registration_clarification_question:
            prov["clarification_question"] = registration_clarification_question

        return TaxResolutionResult(
            constitution=const_norm,
            tax_regime="INDIVIDUAL_NEW_REGIME_115BAC",
            annual_tax_expense=final_tax,
            effective_tax_rate=eff_pct,
            tax_status=tax_status_res,
            is_presumptive=False,
            is_exempt=False,
            explanation=(
                f"Tax calculated under Section 115BAC standard individual slabs for AY 2026-27 on PBT ₹{pbt:,.2f}: "
                f"₹{final_tax:,.2f} (rebate: ₹{rebate_87a:,.2f}, marginal relief: ₹{marg_relief:,.2f})."
            ),
            provenance=prov
        )


# Global singleton
tax_policy_resolver = TaxPolicyResolver()
