"""
KALPA DPR Master Specification — Canonical 39-Section DPR Registry.
Defines the canonical 9 modules (Module 0 + Module I through Module VIII), 39 sections, and all underlying granular fields
with explicit metadata, materiality, applicability, dependencies, and validation rules.
"""
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from pydantic import BaseModel, Field


class DPR_STATE_ISOLATION_ERROR(ValueError):
    """Raised when cross-business contamination, scenario identity violation, or state mismatch occurs."""
    pass


def is_business_concept_match(
    requested_business_id: str,
    candidate_text: Optional[str] = None,
    candidate_nic: Optional[str] = None,
) -> bool:
    """
    Deterministically validates whether an upstream entity, profile, or field
    belongs to the requested business concept or if it is from an opposing business.
    Prevents cross-scenario data contamination between unrelated businesses
    (e.g., Kirana/Grocery vs Saree Retail vs Dairy Farm vs Rice Mill).
    """
    if not requested_business_id:
        return True

    b_id = str(requested_business_id).lower().replace("-", "_")
    cand = str(candidate_text or "").lower()
    nic = str(candidate_nic or "").strip()

    DOMAINS = {
        "dairy": {
            "keywords": ["dairy", "cow", "cattle", "milk", "buffalo", "ghee", "paneer", "livestock", "01411", "014"],
            "conflicts": ["grocery", "kirana", "fmcg", "saree", "textile", "garment", "apparel", "rice_mill", "bakery", "47110", "47711", "10612"],
        },
        "grocery": {
            "keywords": ["grocery", "kirana", "fmcg", "provision", "supermarket", "47110"],
            "conflicts": ["dairy", "cow", "cattle", "buffalo", "milk", "livestock", "saree", "textile", "apparel", "rice_mill", "01411", "47711", "10612"],
        },
        "saree": {
            "keywords": ["saree", "textile", "apparel", "garment", "cloth", "silk", "47711", "4751"],
            "conflicts": ["dairy", "cow", "cattle", "buffalo", "milk", "livestock", "grocery", "kirana", "fmcg", "rice_mill", "01411", "47110", "10612"],
        },
        "rice_mill": {
            "keywords": ["rice_mill", "paddy", "dehusking", "10612"],
            "conflicts": ["dairy", "cow", "milk", "saree", "grocery", "kirana", "01411", "47110", "47711"],
        },
    }

    # Determine domain of requested_business_id
    req_domain = None
    for d_name, d_cfg in DOMAINS.items():
        if any(k in b_id for k in d_cfg["keywords"]):
            req_domain = d_name
            break

    if req_domain:
        cfg = DOMAINS[req_domain]
        for conflict in cfg["conflicts"]:
            if conflict in cand:
                return False
            if nic and conflict == nic:
                return False

    # Also check if candidate belongs to a domain that conflicts with requested_business_id
    for d_name, d_cfg in DOMAINS.items():
        if any(k in cand for k in d_cfg["keywords"]) or (nic and any(k == nic for k in d_cfg["keywords"])):
            if any(conflict in b_id for conflict in d_cfg["conflicts"]):
                return False

    return True


class DPRModuleId(str, Enum):
    MODULE_0 = "module_0"  # Cover & Underwriting Snapshot
    MODULE_I = "module_1"  # Promoter & Enterprise Background
    MODULE_II = "module_2"  # Product, Technology & Operations
    MODULE_III = "module_3"  # Hyper-Local Market & Supply Chain
    MODULE_IV = "module_4"  # Project Outlay & Financing Plan
    MODULE_V = "module_5"  # 5-to-7 Year Financial Schedules
    MODULE_VI = "module_6"  # Debt Servicing & Banking Ratios
    MODULE_VII = "module_7"  # Risk, Strategy & Viability Synthesis
    MODULE_VIII = "module_8"  # Audit Trail, Checklists & Certifications


class FieldMateriality(str, Enum):
    CRITICAL = "CRITICAL"          # Blocks DPR readiness if unresolved
    HIGH = "HIGH"                  # Strongly recommended / credit-sensitive
    MEDIUM = "MEDIUM"              # Operational / business contextual
    LOW = "LOW"                    # Minor descriptive details
    INFORMATIONAL = "INFORMATIONAL"# System generated / header info


class FieldSourceType(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    USER_OVERRIDE = "USER_OVERRIDE"
    VERIFIED_DOCUMENT = "VERIFIED_DOCUMENT"
    ENGINE_CALCULATED = "ENGINE_CALCULATED"
    MARKET_INTELLIGENCE = "MARKET_INTELLIGENCE"
    BENCHMARK = "BENCHMARK"
    POLICY = "POLICY"
    DERIVED = "DERIVED"
    SYSTEM_GENERATED = "SYSTEM_GENERATED"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FieldStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    USER_REQUIRED = "USER_REQUIRED"
    RESOLVED_USER = "RESOLVED_USER"
    DOCUMENT_PENDING = "DOCUMENT_PENDING"
    RESOLVED_DOCUMENT = "RESOLVED_DOCUMENT"
    RESOLVED_BENCHMARK = "RESOLVED_BENCHMARK"
    BENCHMARK_ACCEPTED = "BENCHMARK_ACCEPTED"
    RESOLVED_POLICY = "RESOLVED_POLICY"
    RESOLVED_MARKET = "RESOLVED_MARKET"
    RESOLVED_ENGINE = "RESOLVED_ENGINE"
    RESOLVED_DERIVED = "RESOLVED_DERIVED"
    RESOLVED_OVERRIDE = "RESOLVED_OVERRIDE"
    OVERRIDE = "OVERRIDE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING_CLASSIFICATION = "PENDING_CLASSIFICATION"
    CONFLICT = "CONFLICT"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    SOURCE_MAPPING_ERROR = "SOURCE_MAPPING_ERROR"


class SectionCompleteness(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIALLY_COMPLETE = "PARTIALLY_COMPLETE"
    USER_INPUT_REQUIRED = "USER_INPUT_REQUIRED"
    DOCUMENT_PENDING = "DOCUMENT_PENDING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DPRReadinessStatus(str, Enum):
    DPR_INPUT_INCOMPLETE = "DPR_INPUT_INCOMPLETE"
    DPR_INPUT_READY = "DPR_INPUT_READY"
    DPR_REVIEW_READY = "DPR_REVIEW_READY"
    BANK_REVIEW_READY = "BANK_REVIEW_READY"


class DPRFieldDefinition(BaseModel):
    field_id: str
    section_id: str
    module_id: DPRModuleId
    label: str
    description: str
    field_type: str = "string"  # string, number, currency, percentage, boolean, list, date, object
    unit: Optional[str] = None
    materiality: FieldMateriality = FieldMateriality.MEDIUM
    editable: bool = True
    user_override_allowed: bool = True
    blocking_if_missing: bool = False
    applicable_archetypes: Optional[List[str]] = None  # None means all archetypes apply
    downstream_dependencies: List[str] = []
    why_required: str = "Required for bank appraisal and project viability assessment."
    allowed_values: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_source: FieldSourceType = FieldSourceType.UNKNOWN


class DPRSectionDefinition(BaseModel):
    section_id: str
    section_number: str
    module_id: DPRModuleId
    title: str
    description: str
    field_ids: List[str] = []


class DPRModuleDefinition(BaseModel):
    module_id: DPRModuleId
    module_number: str
    title: str
    description: str
    section_ids: List[str] = []


# ============================================================================
# 8 CANONICAL MODULES DEFINITIONS
# ============================================================================

CANONICAL_MODULES: Dict[DPRModuleId, DPRModuleDefinition] = {
    DPRModuleId.MODULE_0: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_0,
        module_number="0",
        title="Cover & Underwriting Snapshot",
        description="DPR Title, Metadata, Project at a Glance, and Credit Appraisal Memo.",
        section_ids=["0.1", "0.2"]
    ),
    DPRModuleId.MODULE_I: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_I,
        module_number="I",
        title="Promoter & Enterprise Background",
        description="Promoter Dossier, Legal Constitution, and Statutory Compliance Matrix.",
        section_ids=["1.1", "1.2", "1.3"]
    ),
    DPRModuleId.MODULE_II: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_II,
        module_number="II",
        title="Product, Technology & Operations",
        description="Product Specifications, Process Flow, Infrastructure, Machinery Schedule, and Manpower.",
        section_ids=["2.1", "2.2", "2.3", "2.4", "2.5"]
    ),
    DPRModuleId.MODULE_III: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_III,
        module_number="III",
        title="Hyper-Local Market & Supply Chain",
        description="Catchment Demographics, Competitor Mapping, Raw Material Sourcing, and Marketing Channels.",
        section_ids=["3.1", "3.2", "3.3", "3.4"]
    ),
    DPRModuleId.MODULE_IV: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_IV,
        module_number="IV",
        title="Project Outlay & Financing Plan",
        description="Total Project Cost, Means of Finance, Working Capital Assessment, and Scheme Alignment.",
        section_ids=["4.1", "4.2", "4.3", "4.4", "4.5"]
    ),
    DPRModuleId.MODULE_V: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_V,
        module_number="V",
        title="5-to-7 Year Financial Schedules",
        description="Capacity Utilization, Depreciation, Projected P&L, Balance Sheet, and Cash Flow.",
        section_ids=["5.1", "5.2", "5.3", "5.4", "5.5"]
    ),
    DPRModuleId.MODULE_VI: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_VI,
        module_number="VI",
        title="Debt Servicing & Banking Ratios",
        description="Loan Amortization, DSCR Analysis, Break-Even Analysis, Underwriting Ratios, and Stress Tests.",
        section_ids=["6.1", "6.2", "6.3", "6.4", "6.5", "6.6"]
    ),
    DPRModuleId.MODULE_VII: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_VII,
        module_number="VII",
        title="Risk, Strategy & Viability Synthesis",
        description="Multi-Vector Risk Matrix, Dynamic SWOT, Feasibility Synthesis, and Implementation Milestones.",
        section_ids=["7.1", "7.2", "7.3", "7.4", "7.5"]
    ),
    DPRModuleId.MODULE_VIII: DPRModuleDefinition(
        module_id=DPRModuleId.MODULE_VIII,
        module_number="VIII",
        title="Audit Trail, Checklists & Certifications",
        description="Evidence Source Register, Financial Integrity Checks, Document Checklist, and Sanction Sign-Off.",
        section_ids=["8.1", "8.2", "8.3", "8.4"]
    ),
}


# ============================================================================
# 39 CANONICAL SECTIONS DEFINITIONS
# ============================================================================

CANONICAL_SECTIONS: Dict[str, DPRSectionDefinition] = {
    # Module 0
    "0.1": DPRSectionDefinition(
        section_id="0.1",
        section_number="0.1",
        module_id=DPRModuleId.MODULE_0,
        title="Title & Metadata",
        description="Project identification, business activity, location coordinates, dates and versions.",
    ),
    "0.2": DPRSectionDefinition(
        section_id="0.2",
        section_number="0.2",
        module_id=DPRModuleId.MODULE_0,
        title="Project at a Glance / Credit Appraisal Memo",
        description="High-value executive snapshot for bank credit officers.",
    ),

    # Module I
    "1.1": DPRSectionDefinition(
        section_id="1.1",
        section_number="1.1",
        module_id=DPRModuleId.MODULE_I,
        title="Promoter Dossier & Readiness Score",
        description="Promoter qualifications, experience, training, and entrepreneurial readiness.",
    ),
    "1.2": DPRSectionDefinition(
        section_id="1.2",
        section_number="1.2",
        module_id=DPRModuleId.MODULE_I,
        title="Enterprise Constitution & Legal Profile",
        description="Legal entity structure, ownership, premises ownership, registrations.",
    ),
    "1.3": DPRSectionDefinition(
        section_id="1.3",
        section_number="1.3",
        module_id=DPRModuleId.MODULE_I,
        title="Statutory Compliance & Clearance Matrix",
        description="Required licences, permits, and regulatory compliance status.",
    ),

    # Module II
    "2.1": DPRSectionDefinition(
        section_id="2.1",
        section_number="2.1",
        module_id=DPRModuleId.MODULE_II,
        title="Product / Service / Utility & By-Products",
        description="Product specifications, target use, by-products, and value proposition.",
    ),
    "2.2": DPRSectionDefinition(
        section_id="2.2",
        section_number="2.2",
        module_id=DPRModuleId.MODULE_II,
        title="Production / Service Process Flow",
        description="Sequential operating steps, material conversion, and operating cycle.",
    ),
    "2.3": DPRSectionDefinition(
        section_id="2.3",
        section_number="2.3",
        module_id=DPRModuleId.MODULE_II,
        title="Plant Layout, Utilities & Civil Infrastructure",
        description="Land area, shed/civil work, power/water load, and waste management.",
    ),
    "2.4": DPRSectionDefinition(
        section_id="2.4",
        section_number="2.4",
        module_id=DPRModuleId.MODULE_II,
        title="Plant & Machinery Schedule",
        description="Itemized machinery, vendor quotations, capacity, and procurement costs.",
    ),
    "2.5": DPRSectionDefinition(
        section_id="2.5",
        section_number="2.5",
        module_id=DPRModuleId.MODULE_II,
        title="Manpower & Organization Plan",
        description="Promoter role, skilled/unskilled staffing, wage structure, and employment.",
    ),

    # Module III
    "3.1": DPRSectionDefinition(
        section_id="3.1",
        section_number="3.1",
        module_id=DPRModuleId.MODULE_III,
        title="Catchment Demographics & Demand-Supply Gap",
        description="Catchment population, consumer demand estimates, and demand-supply gap.",
    ),
    "3.2": DPRSectionDefinition(
        section_id="3.2",
        section_number="3.2",
        module_id=DPRModuleId.MODULE_III,
        title="Competitor Mapping / Competitive Landscape",
        description="Identified local competitors, pricing comparison, and competitive density.",
    ),
    "3.3": DPRSectionDefinition(
        section_id="3.3",
        section_number="3.3",
        module_id=DPRModuleId.MODULE_III,
        title="Raw Material Sourcing & Input Price Trends",
        description="Primary raw materials, supplier locations, seasonal availability, and prices.",
    ),
    "3.4": DPRSectionDefinition(
        section_id="3.4",
        section_number="3.4",
        module_id=DPRModuleId.MODULE_III,
        title="Marketing Channels & Off-Take Arrangements",
        description="Sales channels, customer segments, distribution, and off-take arrangements.",
    ),

    # Module IV
    "4.1": DPRSectionDefinition(
        section_id="4.1",
        section_number="4.1",
        module_id=DPRModuleId.MODULE_IV,
        title="Total Project Cost",
        description="Land, civil works, plant/machinery, preliminary expenses, and working capital margin.",
    ),
    "4.2": DPRSectionDefinition(
        section_id="4.2",
        section_number="4.2",
        module_id=DPRModuleId.MODULE_IV,
        title="Means of Finance",
        description="Promoter equity, bank term loan, working capital facility, and subsidies.",
    ),
    "4.3": DPRSectionDefinition(
        section_id="4.3",
        section_number="4.3",
        module_id=DPRModuleId.MODULE_IV,
        title="Working Capital Assessment",
        description="Holding periods, raw material/WIP/finished goods inventory, and credit facilities.",
    ),
    "4.4": DPRSectionDefinition(
        section_id="4.4",
        section_number="4.4",
        module_id=DPRModuleId.MODULE_IV,
        title="Applicable Scheme / Subsidy Alignment",
        description="Target nodal government financing scheme, subsidy eligibility, and terms.",
    ),
    "4.5": DPRSectionDefinition(
        section_id="4.5",
        section_number="4.5",
        module_id=DPRModuleId.MODULE_IV,
        title="Alternative Financing & Equity Fit",
        description="Alternative credit guarantee and nodal financing options for optimal leverage.",
    ),

    # Module V
    "5.1": DPRSectionDefinition(
        section_id="5.1",
        section_number="5.1",
        module_id=DPRModuleId.MODULE_V,
        title="Capacity Utilization & Revenue Drivers",
        description="Installed capacity, operating ramp-up, unit sales, and multi-year revenue.",
    ),
    "5.2": DPRSectionDefinition(
        section_id="5.2",
        section_number="5.2",
        module_id=DPRModuleId.MODULE_V,
        title="Depreciation / Fixed Asset Schedule",
        description="Straight-line or WDV asset depreciation schedules across projection years.",
    ),
    "5.3": DPRSectionDefinition(
        section_id="5.3",
        section_number="5.3",
        module_id=DPRModuleId.MODULE_V,
        title="Projected Profit & Loss Statements",
        description="5-to-7 year revenue, direct costs, gross profit, operating expenses, EBITDA, PBT, PAT.",
    ),
    "5.4": DPRSectionDefinition(
        section_id="5.4",
        section_number="5.4",
        module_id=DPRModuleId.MODULE_V,
        title="Projected Balance Sheet",
        description="5-to-7 year Assets (Fixed + Current) vs Liabilities (Equity + Borrowings + Payables).",
    ),
    "5.5": DPRSectionDefinition(
        section_id="5.5",
        section_number="5.5",
        module_id=DPRModuleId.MODULE_V,
        title="Projected Cash Flow Statement",
        description="Operating, investing, and financing cash flow reconciliation across projection years.",
    ),

    # Module VI
    "6.1": DPRSectionDefinition(
        section_id="6.1",
        section_number="6.1",
        module_id=DPRModuleId.MODULE_VI,
        title="Loan Repayment / Amortization Schedule",
        description="Term loan schedule, moratorium period, monthly/yearly principal and interest.",
    ),
    "6.2": DPRSectionDefinition(
        section_id="6.2",
        section_number="6.2",
        module_id=DPRModuleId.MODULE_VI,
        title="DSCR Analysis",
        description="Annual and average Debt Service Coverage Ratio (Cash Accrual vs Debt Obligation).",
    ),
    "6.3": DPRSectionDefinition(
        section_id="6.3",
        section_number="6.3",
        module_id=DPRModuleId.MODULE_VI,
        title="Break-Even Analysis",
        description="Fixed vs variable cost separation, break-even sales turnover, and capacity %.",
    ),
    "6.4": DPRSectionDefinition(
        section_id="6.4",
        section_number="6.4",
        module_id=DPRModuleId.MODULE_VI,
        title="Key Underwriting Ratios",
        description="Current ratio, Debt-Equity, TOL/TNW, ROCE, ROE, Asset Turnover, Payback period.",
    ),
    "6.5": DPRSectionDefinition(
        section_id="6.5",
        section_number="6.5",
        module_id=DPRModuleId.MODULE_VI,
        title="Downside Stress / Sensitivity Tests",
        description="M5 stress testing under revenue drop, cost increase, and interest rate spikes.",
    ),
    "6.6": DPRSectionDefinition(
        section_id="6.6",
        section_number="6.6",
        module_id=DPRModuleId.MODULE_VI,
        title="CMA Statement & Multi-Year Trend Analysis",
        description="Credit Monitoring Arrangement (CMA) format trends for working capital and term loan appraisal.",
    ),

    # Module VII
    "7.1": DPRSectionDefinition(
        section_id="7.1",
        section_number="7.1",
        module_id=DPRModuleId.MODULE_VII,
        title="Multi-Vector Risk & Mitigation Matrix",
        description="Market, operational, financial, seasonal, and promoter risks with mitigation plans.",
    ),
    "7.2": DPRSectionDefinition(
        section_id="7.2",
        section_number="7.2",
        module_id=DPRModuleId.MODULE_VII,
        title="Dynamic SWOT with Provenance",
        description="Evidence-backed Strengths, Weaknesses, Opportunities, and Threats with source stages.",
    ),
    "7.3": DPRSectionDefinition(
        section_id="7.3",
        section_number="7.3",
        module_id=DPRModuleId.MODULE_VII,
        title="Feasibility / Viability Synthesis",
        description="Market, technical, financial, operational gating decision and credit viability.",
    ),
    "7.4": DPRSectionDefinition(
        section_id="7.4",
        section_number="7.4",
        module_id=DPRModuleId.MODULE_VII,
        title="Project Implementation Plan / Milestones",
        description="Implementation timeline, equipment delivery, trial runs, and commercial launch.",
    ),
    "7.5": DPRSectionDefinition(
        section_id="7.5",
        section_number="7.5",
        module_id=DPRModuleId.MODULE_VII,
        title="Viability Gating Decision & Contingency Protocol",
        description="Final bank underwriting gating decision, contingency buffer, and loan disbursement conditions.",
    ),

    # Module VIII
    "8.1": DPRSectionDefinition(
        section_id="8.1",
        section_number="8.1",
        module_id=DPRModuleId.MODULE_VIII,
        title="Evidence & Benchmark Source Register",
        description="Full audit trail of all benchmark, engine, document, and market sources.",
    ),
    "8.2": DPRSectionDefinition(
        section_id="8.2",
        section_number="8.2",
        module_id=DPRModuleId.MODULE_VIII,
        title="Financial Integrity Verification",
        description="Automated mathematical reconciliation (Sources = Uses, Assets = Liab+Eq, DSCR reconciles).",
    ),
    "8.3": DPRSectionDefinition(
        section_id="8.3",
        section_number="8.3",
        module_id=DPRModuleId.MODULE_VIII,
        title="Document Enclosure Checklist",
        description="Promoter KYC, Land/Lease deed, Quotations, Udyam, Bank statements checklist.",
    ),
    "8.4": DPRSectionDefinition(
        section_id="8.4",
        section_number="8.4",
        module_id=DPRModuleId.MODULE_VIII,
        title="Inspection / Sanction Sign-Off Box",
        description="Bank branch appraisal, field verification, sanction conditions, and signature blocks.",
    ),
}


# ============================================================================
# MASTER FIELD REGISTRY
# ============================================================================

ALL_DPR_FIELDS: List[DPRFieldDefinition] = [
    # -------------------------------------------------------------
    # 0.1 Title & Metadata
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="dpr_title",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="DPR Title",
        description="Formal title of the Detailed Project Report.",
        materiality=FieldMateriality.INFORMATIONAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.SYSTEM_GENERATED
    ),
    DPRFieldDefinition(
        field_id="business_name",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="Business / Enterprise Name",
        description="Registered or proposed trade name of the enterprise.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True,
        why_required="Required to identify the legal borrowing entity."
    ),
    DPRFieldDefinition(
        field_id="promoter_name",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="Promoter / Entrepreneur Name",
        description="Full legal name of the lead applicant or entrepreneur.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True,
        why_required="Required for primary KYC and credit bureau verification."
    ),
    DPRFieldDefinition(
        field_id="business_activity",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="Business Activity",
        description="Specific commercial activity performed by the enterprise.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True
    ),
    DPRFieldDefinition(
        field_id="business_archetype",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="Business Archetype",
        description="Sectoral classification: Retail, Manufacturing, Dairy/Agri, Services, etc. (Owned by Stage 2).",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        blocking_if_missing=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="nic_code",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="National Industrial Classification (NIC) Code",
        description="Official 5-digit NIC code for the business activity.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="location_district",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="Operating District",
        description="District where project is situated.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True
    ),
    DPRFieldDefinition(
        field_id="location_state",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="Operating State",
        description="State or Union Territory of India.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True
    ),
    DPRFieldDefinition(
        field_id="target_scheme_code",
        section_id="0.1",
        module_id=DPRModuleId.MODULE_0,
        label="Target Financing Scheme",
        description="Nodal credit scheme such as PMEGP, Mudra, Stand-Up India, or CGTMSE.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 0.2 Project at a Glance / Credit Appraisal Memo
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="project_at_a_glance_summary",
        section_id="0.2",
        module_id=DPRModuleId.MODULE_0,
        label="Executive Credit Appraisal Summary",
        description="Condensed synthesis of project cost, funding, profitability, and debt metrics.",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="glance_total_project_cost",
        section_id="0.2",
        module_id=DPRModuleId.MODULE_0,
        label="Total Project Outlay (₹)",
        description="Reconciled total capital and working capital outlay.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="glance_promoter_contribution",
        section_id="0.2",
        module_id=DPRModuleId.MODULE_0,
        label="Promoter Margin Money (₹)",
        description="Own funds invested by the entrepreneur.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="glance_term_loan",
        section_id="0.2",
        module_id=DPRModuleId.MODULE_0,
        label="Bank Term Loan Requirement (₹)",
        description="Proposed bank term loan assistance.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="glance_average_dscr",
        section_id="0.2",
        module_id=DPRModuleId.MODULE_0,
        label="Average DSCR",
        description="Average Debt Service Coverage Ratio over loan tenure.",
        field_type="number",
        unit="x",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="glance_break_even_utilization",
        section_id="0.2",
        module_id=DPRModuleId.MODULE_0,
        label="Break-Even Capacity Utilization (%)",
        description="Operating percentage required to meet all fixed costs.",
        field_type="percentage",
        unit="%",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="glance_employment_generation",
        section_id="0.2",
        module_id=DPRModuleId.MODULE_0,
        label="Direct Employment Generated",
        description="Number of jobs created by the project.",
        field_type="number",
        unit="persons",
        materiality=FieldMateriality.MEDIUM,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 1.1 Promoter Dossier & Readiness Score
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="promoter_education",
        section_id="1.1",
        module_id=DPRModuleId.MODULE_I,
        label="Educational Qualification",
        description="Highest academic qualification attained.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        why_required="Required by bank guidelines (e.g., PMEGP requires 8th pass for > ₹10L projects)."
    ),
    DPRFieldDefinition(
        field_id="promoter_experience_years",
        section_id="1.1",
        module_id=DPRModuleId.MODULE_I,
        label="Relevant Sector Experience (Years)",
        description="Years of practical or domain experience.",
        field_type="number",
        unit="years",
        materiality=FieldMateriality.HIGH,
        editable=True,
        min_value=0,
        max_value=60,
        why_required="Assesses operational competence and project execution risk."
    ),
    DPRFieldDefinition(
        field_id="promoter_edp_training_status",
        section_id="1.1",
        module_id=DPRModuleId.MODULE_I,
        label="EDP / Skill Training Status",
        description="Entrepreneurship Development Programme training completion.",
        field_type="string",
        materiality=FieldMateriality.HIGH,
        editable=True,
        allowed_values=["COMPLETED", "IN_PROGRESS", "NOT_UNDERTAKEN", "EXEMPTED"],
        why_required="Mandatory for PMEGP subsidy release (offline/online EDP certificate)."
    ),
    DPRFieldDefinition(
        field_id="promoter_social_category",
        section_id="1.1",
        module_id=DPRModuleId.MODULE_I,
        label="Social / Special Category",
        description="General, SC/ST, OBC, Women, Minority, Ex-Servicemen, PwD.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        allowed_values=["GENERAL", "OBC", "SC", "ST", "WOMEN", "MINORITY", "EX_SERVICEMEN", "PH_PWD"],
        why_required="Determines government subsidy rate (e.g. 15% vs 25% or 35% under PMEGP)."
    ),
    DPRFieldDefinition(
        field_id="promoter_readiness_score",
        section_id="1.1",
        module_id=DPRModuleId.MODULE_I,
        label="Entrepreneur Readiness Score",
        description="Readiness index evaluated by Stage 10.",
        field_type="number",
        unit="/100",
        materiality=FieldMateriality.MEDIUM,
        editable=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 1.2 Enterprise Constitution & Legal Profile
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="legal_constitution",
        section_id="1.2",
        module_id=DPRModuleId.MODULE_I,
        label="Legal Constitution of Business",
        description="Proprietorship, Partnership, LLP, Private Limited, FPO, or Cooperative.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True,
        allowed_values=["PROPRIETORSHIP", "PARTNERSHIP", "LLP", "PRIVATE_LIMITED", "FPO", "COOPERATIVE"],
        why_required="Establishes borrower legal liability and documentation requirements."
    ),
    DPRFieldDefinition(
        field_id="premises_status",
        section_id="1.2",
        module_id=DPRModuleId.MODULE_I,
        label="Premises Ownership Status",
        description="Whether premises are owned, rented, leased, or proposed to be acquired.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True,
        allowed_values=["OWNED", "RENTED", "LEASED", "PROPOSED_PURCHASE"],
        downstream_dependencies=["rent_expense", "civil_construction_cost", "project_cost"],
        why_required="Determines if civil works or rental lease agreement are required."
    ),
    DPRFieldDefinition(
        field_id="udyam_registration_number",
        section_id="1.2",
        module_id=DPRModuleId.MODULE_I,
        label="Udyam Registration Number",
        description="Official MSME Udyam certificate identifier if already registered.",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        why_required="Required for priority sector lending classification and interest subvention."
    ),
    DPRFieldDefinition(
        field_id="gst_applicability",
        section_id="1.2",
        module_id=DPRModuleId.MODULE_I,
        label="GST Registration Status",
        description="Applicability and registration status under Goods and Services Tax.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        allowed_values=["REGISTERED", "EXEMPTED_BELOW_THRESHOLD", "APPLIED", "NOT_APPLICABLE"],
        why_required="Legal compliance for interstate sales and input tax credit."
    ),

    # -------------------------------------------------------------
    # 1.3 Statutory Compliance & Clearance Matrix
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="statutory_compliance_matrix",
        section_id="1.3",
        module_id=DPRModuleId.MODULE_I,
        label="Statutory Clearances Matrix",
        description="Status of Trade License, FSSAI, Pollution Consent, Shop & Establishment.",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=True,
        default_source=FieldSourceType.ENGINE_CALCULATED,
        why_required="Assesses statutory readiness and pre-disbursement compliance."
    ),
    DPRFieldDefinition(
        field_id="fssai_clearance_status",
        section_id="1.3",
        module_id=DPRModuleId.MODULE_I,
        label="FSSAI Food Safety Licence Status",
        description="FSSAI registration/license status for food processing or dairy.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        applicable_archetypes=["food_processing", "dairy", "restaurant", "bakery"],
        allowed_values=["OBTAINED", "APPLIED", "REQUIRED", "NOT_APPLICABLE"],
        why_required="Mandatory food safety clearance for food and beverage enterprises."
    ),
    DPRFieldDefinition(
        field_id="pollution_consent_status",
        section_id="1.3",
        module_id=DPRModuleId.MODULE_I,
        label="State Pollution Control Board Consent (CTO/CTE)",
        description="Consent to Establish / Operate under Air & Water Acts.",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        applicable_archetypes=["manufacturing", "food_processing", "chemical", "textiles"],
        allowed_values=["WHITE_CATEGORY_EXEMPTED", "OBTAINED", "APPLIED", "NOT_APPLICABLE"],
        why_required="Environmental clearance required by commercial lenders for manufacturing."
    ),

    # -------------------------------------------------------------
    # 2.1 Product / Service / Utility & By-Products
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="primary_product_name",
        section_id="2.1",
        module_id=DPRModuleId.MODULE_II,
        label="Primary Product / Service Name",
        description="Main revenue-generating product or service.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True
    ),
    DPRFieldDefinition(
        field_id="product_specifications",
        section_id="2.1",
        module_id=DPRModuleId.MODULE_II,
        label="Product Specifications / Grade",
        description="Quality standards, dimensions, composition, or service parameters.",
        materiality=FieldMateriality.MEDIUM,
        editable=True
    ),
    DPRFieldDefinition(
        field_id="by_products_and_waste",
        section_id="2.1",
        module_id=DPRModuleId.MODULE_II,
        label="By-Products and Waste Recovery",
        description="Identified secondary outputs, scrap yield, or manure/bio-gas generation.",
        materiality=FieldMateriality.LOW,
        editable=True,
        applicable_archetypes=["dairy", "poultry", "manufacturing", "food_processing", "agri_processing"]
    ),

    # -------------------------------------------------------------
    # 2.2 Production / Service Process Flow
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="process_flow_summary",
        section_id="2.2",
        module_id=DPRModuleId.MODULE_II,
        label="Manufacturing / Service Delivery Flow",
        description="Step-by-step technological process from raw material intake to finished dispatch.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        default_source=FieldSourceType.BENCHMARK
    ),
    DPRFieldDefinition(
        field_id="operating_cycle_days",
        section_id="2.2",
        module_id=DPRModuleId.MODULE_II,
        label="Operating / Processing Cycle (Days)",
        description="Time required to convert raw materials into marketable finished goods.",
        field_type="number",
        unit="days",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        min_value=1,
        max_value=365,
        default_source=FieldSourceType.BENCHMARK
    ),

    # -------------------------------------------------------------
    # 2.3 Plant Layout, Utilities & Civil Infrastructure
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="covered_area_sqft",
        section_id="2.3",
        module_id=DPRModuleId.MODULE_II,
        label="Total Covered / Working Area (sq. ft.)",
        description="Required floor area for operations, storage, and customer area.",
        field_type="number",
        unit="sq. ft.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        min_value=50,
        max_value=100000,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["rent_expense", "civil_construction_cost"]
    ),
    DPRFieldDefinition(
        field_id="power_load_kw",
        section_id="2.3",
        module_id=DPRModuleId.MODULE_II,
        label="Connected Power Load (kW / HP)",
        description="Connected electrical load required for machinery and utilities.",
        field_type="number",
        unit="kW",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        min_value=1,
        max_value=500,
        default_source=FieldSourceType.BENCHMARK
    ),
    DPRFieldDefinition(
        field_id="water_requirement_litres_day",
        section_id="2.3",
        module_id=DPRModuleId.MODULE_II,
        label="Water Requirement (Litres/Day)",
        description="Daily water consumption for processing, cleaning, or livestock.",
        field_type="number",
        unit="L/day",
        materiality=FieldMateriality.LOW,
        editable=True,
        applicable_archetypes=["dairy", "poultry", "food_processing", "manufacturing", "textiles"],
        default_source=FieldSourceType.BENCHMARK
    ),

    # -------------------------------------------------------------
    # 2.4 Plant & Machinery Schedule
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="machinery_schedule_items",
        section_id="2.4",
        module_id=DPRModuleId.MODULE_II,
        label="Itemized Plant & Machinery Schedule",
        description="Schedule of capital assets, capacity, unit price, installation, and vendor status.",
        field_type="list",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["capex", "project_cost", "depreciation", "loan_amount"]
    ),
    DPRFieldDefinition(
        field_id="machinery_quotation_status",
        section_id="2.4",
        module_id=DPRModuleId.MODULE_II,
        label="Machinery Quotation Status",
        description="Whether firm vendor proforma invoices are uploaded or benchmark costs are utilized.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        allowed_values=["QUOTATIONS_UPLOADED", "BENCHMARK_ESTIMATES_USED", "PENDING_VENDOR_SELECTION"],
        default_source=FieldSourceType.BENCHMARK
    ),

    # -------------------------------------------------------------
    # 2.5 Manpower & Organization Plan
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="skilled_workers_count",
        section_id="2.5",
        module_id=DPRModuleId.MODULE_II,
        label="Skilled Personnel Count",
        description="Number of skilled technical/operational staff.",
        field_type="number",
        unit="persons",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        min_value=0,
        max_value=500,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["labor_cost", "operating_expenses", "ebitda"]
    ),
    DPRFieldDefinition(
        field_id="unskilled_workers_count",
        section_id="2.5",
        module_id=DPRModuleId.MODULE_II,
        label="Semi-Skilled / Unskilled Staff Count",
        description="Number of helper / manual staff members.",
        field_type="number",
        unit="persons",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        min_value=0,
        max_value=500,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["labor_cost", "operating_expenses", "ebitda"]
    ),
    DPRFieldDefinition(
        field_id="monthly_wages_total",
        section_id="2.5",
        module_id=DPRModuleId.MODULE_II,
        label="Total Monthly Payroll (₹)",
        description="Total monthly wage and salary outgo for all employees.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.HIGH,
        editable=True,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["operating_expenses", "ebitda", "working_capital"]
    ),

    # -------------------------------------------------------------
    # 3.1 Catchment Demographics & Demand-Supply Gap
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="catchment_radius_km",
        section_id="3.1",
        module_id=DPRModuleId.MODULE_III,
        label="Target Catchment Radius (km)",
        description="Geographical coverage for customers and immediate supply.",
        field_type="number",
        unit="km",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        default_source=FieldSourceType.MARKET_INTELLIGENCE
    ),
    DPRFieldDefinition(
        field_id="catchment_population_estimate",
        section_id="3.1",
        module_id=DPRModuleId.MODULE_III,
        label="Catchment Population Base",
        description="Estimated population residing within the economic catchment area.",
        field_type="number",
        unit="persons",
        materiality=FieldMateriality.MEDIUM,
        editable=False,
        default_source=FieldSourceType.MARKET_INTELLIGENCE
    ),
    DPRFieldDefinition(
        field_id="local_demand_supply_gap",
        section_id="3.1",
        module_id=DPRModuleId.MODULE_III,
        label="Demand-Supply Gap Assessment",
        description="Assessment of unmet demand and growth headroom in the target territory.",
        materiality=FieldMateriality.HIGH,
        editable=False,
        default_source=FieldSourceType.MARKET_INTELLIGENCE
    ),

    # -------------------------------------------------------------
    # 3.2 Competitor Mapping / Competitive Landscape
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="competitor_count_in_radius",
        section_id="3.2",
        module_id=DPRModuleId.MODULE_III,
        label="Competitors Mapped in Catchment",
        description="Number of verified active competitors identified.",
        field_type="number",
        unit="competitors",
        materiality=FieldMateriality.HIGH,
        editable=False,
        default_source=FieldSourceType.MARKET_INTELLIGENCE
    ),
    DPRFieldDefinition(
        field_id="competitor_pricing_range",
        section_id="3.2",
        module_id=DPRModuleId.MODULE_III,
        label="Prevailing Market Price Range (₹)",
        description="Market retail or wholesale pricing observed among peers.",
        materiality=FieldMateriality.HIGH,
        editable=False,
        default_source=FieldSourceType.MARKET_INTELLIGENCE
    ),

    # -------------------------------------------------------------
    # 3.3 Raw Material Sourcing & Input Price Trends
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="primary_raw_material",
        section_id="3.3",
        module_id=DPRModuleId.MODULE_III,
        label="Primary Raw Material / Inventory Item",
        description="Core input required for manufacturing or trading inventory.",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        blocking_if_missing=True,
        default_source=FieldSourceType.BENCHMARK
    ),
    DPRFieldDefinition(
        field_id="raw_material_sourcing_mode",
        section_id="3.3",
        module_id=DPRModuleId.MODULE_III,
        label="Raw Material Sourcing Mode",
        description="Local farm gate, wholesale mandi, direct manufacturer, or regional distributor.",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        default_source=FieldSourceType.BENCHMARK
    ),
    DPRFieldDefinition(
        field_id="raw_material_supplier_credit_days",
        section_id="3.3",
        module_id=DPRModuleId.MODULE_III,
        label="Supplier Credit Period (Days)",
        description="Average credit period extended by raw material suppliers.",
        field_type="number",
        unit="days",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        min_value=0,
        max_value=120,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["creditor_days", "working_capital"]
    ),

    # -------------------------------------------------------------
    # 3.4 Marketing Channels & Off-Take Arrangements
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="primary_sales_channel",
        section_id="3.4",
        module_id=DPRModuleId.MODULE_III,
        label="Primary Sales Channel",
        description="Direct retail counter, local B2B wholesale, institutional supply, or online.",
        materiality=FieldMateriality.HIGH,
        editable=True,
        default_source=FieldSourceType.BENCHMARK
    ),
    DPRFieldDefinition(
        field_id="offtake_agreement_status",
        section_id="3.4",
        module_id=DPRModuleId.MODULE_III,
        label="Off-Take / Buyer Agreement Status",
        description="Confirmed institutional buyer contracts, MOUs, or open market sales.",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        allowed_values=["CONTRACT_SIGNED", "MOU_OBTAINED", "RETAIL_OPEN_MARKET", "LOCAL_TIE_UP"],
        default_source=FieldSourceType.BENCHMARK
    ),

    # -------------------------------------------------------------
    # 4.1 Total Project Cost
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="cost_land_building",
        section_id="4.1",
        module_id=DPRModuleId.MODULE_IV,
        label="Land & Civil Construction Cost (₹)",
        description="Civil shed, civil renovation, or site development outlay.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="cost_plant_machinery",
        section_id="4.1",
        module_id=DPRModuleId.MODULE_IV,
        label="Plant & Machinery Cost (₹)",
        description="Total equipment, machinery, and installation outlay.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="cost_preliminary_preoperative",
        section_id="4.1",
        module_id=DPRModuleId.MODULE_IV,
        label="Preliminary & Pre-operative Expenses (₹)",
        description="Registration, statutory fees, DPR consultancy, trial runs.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.MEDIUM,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="cost_working_capital_margin",
        section_id="4.1",
        module_id=DPRModuleId.MODULE_IV,
        label="Margin Money for Working Capital (₹)",
        description="Promoter contribution towards first cycle working capital requirement.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="total_project_cost",
        section_id="4.1",
        module_id=DPRModuleId.MODULE_IV,
        label="Total Project Cost (₹)",
        description="Total reconciled capital expenditure and initial working capital margin.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 4.2 Means of Finance
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="promoter_equity_amount",
        section_id="4.2",
        module_id=DPRModuleId.MODULE_IV,
        label="Promoter Margin Contribution (₹)",
        description="Own capital invested by entrepreneur.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="bank_term_loan_amount",
        section_id="4.2",
        module_id=DPRModuleId.MODULE_IV,
        label="Bank Term Loan (₹)",
        description="Term loan component funded by financing bank.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="government_subsidy_amount",
        section_id="4.2",
        module_id=DPRModuleId.MODULE_IV,
        label="Eligible Government Margin Money / Subsidy (₹)",
        description="Nodal scheme capital subsidy or back-ended margin money.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="means_of_finance_reconciliation",
        section_id="4.2",
        module_id=DPRModuleId.MODULE_IV,
        label="Sources vs Uses Balanced",
        description="Strict mathematical reconciliation confirming Total Sources == Total Uses.",
        field_type="boolean",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 4.3 Working Capital Assessment
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="inventory_holding_days",
        section_id="4.3",
        module_id=DPRModuleId.MODULE_IV,
        label="Inventory Holding Period (Days)",
        description="Average days of raw material and finished stock held.",
        field_type="number",
        unit="days",
        materiality=FieldMateriality.HIGH,
        editable=True,
        min_value=5,
        max_value=180,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["working_capital", "cash_credit_limit", "interest_expense"]
    ),
    DPRFieldDefinition(
        field_id="receivable_credit_days",
        section_id="4.3",
        module_id=DPRModuleId.MODULE_IV,
        label="Receivables / Customer Credit Period (Days)",
        description="Average credit period allowed to trade buyers or credit sales.",
        field_type="number",
        unit="days",
        materiality=FieldMateriality.HIGH,
        editable=True,
        min_value=0,
        max_value=120,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["working_capital", "cash_credit_limit"]
    ),
    DPRFieldDefinition(
        field_id="working_capital_bank_facility",
        section_id="4.3",
        module_id=DPRModuleId.MODULE_IV,
        label="Assessed Working Capital Bank Limit (CC/OD) (₹)",
        description="Bank working capital limit calculated under Nayak Committee / Turnover method.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 4.4 Applicable Scheme / Subsidy Alignment
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="scheme_subsidy_percentage",
        section_id="4.4",
        module_id=DPRModuleId.MODULE_IV,
        label="Nodal Scheme Subsidy Rate (%)",
        description="Applicable subsidy percentage under the recommended government scheme.",
        field_type="percentage",
        unit="%",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.POLICY
    ),
    DPRFieldDefinition(
        field_id="scheme_beneficiary_contribution_pct",
        section_id="4.4",
        module_id=DPRModuleId.MODULE_IV,
        label="Mandatory Beneficiary Margin (%)",
        description="Minimum mandatory borrower equity mandated by scheme guidelines.",
        field_type="percentage",
        unit="%",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.POLICY
    ),

    # -------------------------------------------------------------
    # 5.1 Capacity Utilization & Revenue Drivers
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="operational_unit_count",
        section_id="5.1",
        module_id=DPRModuleId.MODULE_V,
        label="Core Operational Units / Batch Scale",
        description="Number of operational units: Dairy animals, machines, loom count, seating capacity, or inventory base.",
        field_type="number",
        materiality=FieldMateriality.CRITICAL,
        editable=True,
        min_value=1,
        max_value=100000,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["capex", "revenue", "operating_expenses", "project_cost", "dscr"]
    ),
    DPRFieldDefinition(
        field_id="daily_production_sales_units",
        section_id="5.1",
        module_id=DPRModuleId.MODULE_V,
        label="Expected Daily Output / Sales Volume",
        description="Units produced or sold on a normal business operating day.",
        field_type="number",
        materiality=FieldMateriality.HIGH,
        editable=True,
        min_value=1,
        max_value=1000000,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["annual_revenue", "ebitda", "pat", "cash_flow", "dscr"]
    ),
    DPRFieldDefinition(
        field_id="unit_selling_price",
        section_id="5.1",
        module_id=DPRModuleId.MODULE_V,
        label="Average Realization / Selling Price per Unit (₹)",
        description="Average price realized per product unit or customer transaction.",
        field_type="currency",
        unit="INR",
        materiality=FieldMateriality.HIGH,
        editable=True,
        min_value=0.1,
        max_value=10000000,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["annual_revenue", "gross_profit", "ebitda", "pat", "dscr"]
    ),
    DPRFieldDefinition(
        field_id="operating_days_per_year",
        section_id="5.1",
        module_id=DPRModuleId.MODULE_V,
        label="Annual Operating Days",
        description="Number of productive operating days per calendar year.",
        field_type="number",
        unit="days",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        min_value=100,
        max_value=365,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["annual_revenue", "ebitda", "dscr"]
    ),
    DPRFieldDefinition(
        field_id="capacity_utilization_year1",
        section_id="5.1",
        module_id=DPRModuleId.MODULE_V,
        label="Year 1 Capacity Utilization (%)",
        description="Starting capacity ramp-up percentage for Year 1.",
        field_type="percentage",
        unit="%",
        materiality=FieldMateriality.HIGH,
        editable=True,
        min_value=20,
        max_value=100,
        default_source=FieldSourceType.BENCHMARK,
        downstream_dependencies=["annual_revenue", "ebitda", "dscr"]
    ),

    # -------------------------------------------------------------
    # 5.2 Depreciation Schedule
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="depreciation_schedule_summary",
        section_id="5.2",
        module_id=DPRModuleId.MODULE_V,
        label="5-Year Depreciation Schedule",
        description="Annual depreciation expense computed under Income Tax Act rules.",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 5.3 Projected Profit & Loss
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="projected_pnl_statements",
        section_id="5.3",
        module_id=DPRModuleId.MODULE_V,
        label="5-Year Projected Profit & Loss Statements",
        description="5-year Revenue, Raw Material, Operating Costs, EBITDA, PBT, Tax, PAT.",
        field_type="object",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 5.4 Projected Balance Sheet
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="projected_balance_sheet",
        section_id="5.4",
        module_id=DPRModuleId.MODULE_V,
        label="5-Year Projected Balance Sheet Statements",
        description="5-year Assets vs Liabilities balanced statements.",
        field_type="object",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 5.5 Projected Cash Flow Statement
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="projected_cash_flow",
        section_id="5.5",
        module_id=DPRModuleId.MODULE_V,
        label="5-Year Projected Cash Flow Statements",
        description="5-year Operating, Investing, and Financing cash flow reconciliation.",
        field_type="object",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 6.1 Loan Repayment / Amortization Schedule
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="loan_amortization_schedule",
        section_id="6.1",
        module_id=DPRModuleId.MODULE_VI,
        label="Term Loan Repayment Schedule",
        description="Monthly / yearly EMI schedule, moratorium interest, and principal amortization.",
        field_type="object",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),
    DPRFieldDefinition(
        field_id="moratorium_period_months",
        section_id="6.1",
        module_id=DPRModuleId.MODULE_VI,
        label="Moratorium Period (Months)",
        description="Repayment grace period before principal amortization begins.",
        field_type="number",
        unit="months",
        materiality=FieldMateriality.HIGH,
        editable=True,
        user_override_allowed=True,
        default_source=FieldSourceType.BENCHMARK
    ),

    # -------------------------------------------------------------
    # 6.2 DSCR Analysis
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="dscr_analysis_multi_year",
        section_id="6.2",
        module_id=DPRModuleId.MODULE_VI,
        label="Annual and Average DSCR Schedule",
        description="Year-by-year cash accruals vs total debt service obligations.",
        field_type="object",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 6.3 Break-Even Analysis
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="break_even_metrics",
        section_id="6.3",
        module_id=DPRModuleId.MODULE_VI,
        label="Break-Even Sales and Capacity Analysis",
        description="Fixed costs, variable costs, contribution margin, and break-even sales.",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 6.4 Key Underwriting Ratios
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="banking_ratios_summary",
        section_id="6.4",
        module_id=DPRModuleId.MODULE_VI,
        label="Key Underwriting and Solvency Ratios",
        description="Current ratio, Debt-Equity, TOL/TNW, ROCE, ROE, Asset turnover, and Payback.",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 6.5 Downside Stress / Sensitivity Tests
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="stress_scenarios_appraisal",
        section_id="6.5",
        module_id=DPRModuleId.MODULE_VI,
        label="Downside Sensitivity & Stress Tests (M5)",
        description="Stress tests for -10% revenue drop, +10% raw material hike, and +200 bps interest rate.",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 7.1 Multi-Vector Risk & Mitigation Matrix
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="risk_mitigation_matrix",
        section_id="7.1",
        module_id=DPRModuleId.MODULE_VII,
        label="Multi-Vector Risk Matrix & Mitigation Plans",
        description="Evaluated market, financial, operational, and regulatory risks with mitigations (Stage 11).",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 7.2 Dynamic SWOT with Provenance
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="dynamic_swot_matrix",
        section_id="7.2",
        module_id=DPRModuleId.MODULE_VII,
        label="Dynamic SWOT Matrix with Evidence Provenance",
        description="Strengths, Weaknesses, Opportunities, Threats with source-stage tags (Stage 13).",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 7.3 Feasibility / Viability Synthesis
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="feasibility_viability_synthesis",
        section_id="7.3",
        module_id=DPRModuleId.MODULE_VII,
        label="Feasibility & Bank Viability Verdict",
        description="Comprehensive gating decision synthesized from Stage 12.",
        field_type="object",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 7.4 Project Implementation Plan / Milestones
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="implementation_schedule_milestones",
        section_id="7.4",
        module_id=DPRModuleId.MODULE_VII,
        label="Implementation Schedule & Key Milestones",
        description="Timeline for sanction, site preparation, equipment procurement, trial run, commercial start.",
        field_type="list",
        materiality=FieldMateriality.MEDIUM,
        editable=True,
        default_source=FieldSourceType.BENCHMARK
    ),
    DPRFieldDefinition(
        field_id="project_timeline_months",
        section_id="7.4",
        module_id=DPRModuleId.MODULE_VII,
        label="Total Implementation Timeline (Months)",
        description="Total duration from financial sanction to commercial operations.",
        field_type="number",
        unit="months",
        materiality=FieldMateriality.HIGH,
        editable=True,
        user_override_allowed=True,
        default_source=FieldSourceType.BENCHMARK
    ),

    # -------------------------------------------------------------
    # 8.1 Evidence & Benchmark Source Register
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="evidence_source_register",
        section_id="8.1",
        module_id=DPRModuleId.MODULE_VIII,
        label="Evidence & Benchmark Source Register",
        description="Comprehensive audit register linking every material fact to its verified data origin.",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.SYSTEM_GENERATED
    ),

    # -------------------------------------------------------------
    # 8.2 Financial Integrity Verification
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="financial_integrity_verification",
        section_id="8.2",
        module_id=DPRModuleId.MODULE_VIII,
        label="Mathematical Integrity & Balance Verification",
        description="System verification verifying zero financial variance across statements.",
        field_type="object",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        blocking_if_missing=True,
        default_source=FieldSourceType.SYSTEM_GENERATED
    ),

    # -------------------------------------------------------------
    # 8.3 Document Enclosure Checklist
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="document_enclosure_checklist",
        section_id="8.3",
        module_id=DPRModuleId.MODULE_VIII,
        label="Institutional Document Enclosure Checklist",
        description="Tracking status of KYC, Quotations, Land deeds, and Permits.",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=True,
        default_source=FieldSourceType.SYSTEM_GENERATED
    ),

    # -------------------------------------------------------------
    # 4.5 Alternative Financing & Equity Fit
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="alternative_scheme_recommendations",
        section_id="4.5",
        module_id=DPRModuleId.MODULE_IV,
        label="Alternative Financing & Scheme Recommendations",
        description="Alternative nodal schemes (Mudra, Stand-Up India, CGTMSE) and equity structures.",
        field_type="list",
        materiality=FieldMateriality.MEDIUM,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 6.6 CMA Statement & Multi-Year Trend Analysis
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="cma_statement_summary",
        section_id="6.6",
        module_id=DPRModuleId.MODULE_VI,
        label="Credit Monitoring Arrangement (CMA) Trend Analysis",
        description="Standardized banking CMA statement tracking multi-year working capital and repayment trends.",
        field_type="object",
        materiality=FieldMateriality.HIGH,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 7.5 Viability Gating Decision & Contingency Protocol
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="contingency_mitigation_protocol",
        section_id="7.5",
        module_id=DPRModuleId.MODULE_VII,
        label="Viability Gating & Contingency Protocol",
        description="Formal credit underwriting conditions, contingency buffers, and pre-disbursement compliance.",
        field_type="object",
        materiality=FieldMateriality.CRITICAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.ENGINE_CALCULATED
    ),

    # -------------------------------------------------------------
    # 8.4 Inspection / Sanction Sign-Off Box
    # -------------------------------------------------------------
    DPRFieldDefinition(
        field_id="inspection_sanction_signoff_box",
        section_id="8.4",
        module_id=DPRModuleId.MODULE_VIII,
        label="Bank Inspection & Sanction Sign-Off",
        description="Reserved institutional section for branch manager and credit officer appraisal.",
        field_type="object",
        materiality=FieldMateriality.INFORMATIONAL,
        editable=False,
        user_override_allowed=False,
        default_source=FieldSourceType.SYSTEM_GENERATED
    ),
]


# Map field_ids to their definitions and populate sections
FIELD_REGISTRY_MAP: Dict[str, DPRFieldDefinition] = {f.field_id: f for f in ALL_DPR_FIELDS}

for f in ALL_DPR_FIELDS:
    if f.section_id in CANONICAL_SECTIONS:
        if f.field_id not in CANONICAL_SECTIONS[f.section_id].field_ids:
            CANONICAL_SECTIONS[f.section_id].field_ids.append(f.field_id)


def get_field_definition(field_id: str) -> Optional[DPRFieldDefinition]:
    """Retrieves definition for a registered DPR field, supporting canonical aliases."""
    if not field_id:
        return None
    canonical_id = normalize_field_id(field_id)
    return FIELD_REGISTRY_MAP.get(canonical_id)


def is_field_applicable(field_def: DPRFieldDefinition, archetype: Optional[str]) -> bool:
    """
    Checks if a field is applicable to the specified business archetype.
    If applicable_archetypes is None or empty, field applies universally to all businesses.
    If archetype is not yet determined (None or empty before Stage 2 classification),
    archetype-specific fields are NOT treated as actively applicable in Stage 1.
    """
    if not field_def.applicable_archetypes:
        return True
    if not archetype:
        return False
    arch_norm = archetype.strip().lower()
    return any(arch_norm in a.lower() or a.lower() in arch_norm for a in field_def.applicable_archetypes)


def get_field_applicability_status(field_def: DPRFieldDefinition, archetype: Optional[str]) -> str:
    """
    Returns 'APPLICABLE', 'NOT_APPLICABLE', or 'PENDING_CLASSIFICATION'.
    """
    if not field_def.applicable_archetypes:
        return "APPLICABLE"
    if not archetype:
        return "PENDING_CLASSIFICATION"
    arch_norm = archetype.strip().lower()
    if any(arch_norm in a.lower() or a.lower() in arch_norm for a in field_def.applicable_archetypes):
        return "APPLICABLE"
    return "NOT_APPLICABLE"


# Canonical Field Aliases Mapping
CANONICAL_FIELD_ALIASES: Dict[str, str] = {
    # Location
    "state": "location_state",
    "target_state": "location_state",
    "district": "location_district",
    "target_district": "location_district",
    "premises": "premises_status",
    "land_type": "premises_status",
    "premises_type": "premises_status",
    "operating_premises": "premises_status",
    "premises_arrangement": "premises_status",
    "has_land_or_premise": "premises_status",
    # Promoter Identity
    "entrepreneur_name": "promoter_name",
    "founder_name": "promoter_name",
    "applicant_name": "promoter_name",
    "proprietor_name": "promoter_name",
    "name": "promoter_name",
    # Promoter Qualifications & Education
    "education": "promoter_education",
    "education_level": "promoter_education",
    "educational_qualification": "promoter_education",
    "promoter_qualification": "promoter_education",
    "highest_education": "promoter_education",
    "qualification": "promoter_education",
    "academic_qualification": "promoter_education",
    "education.highest_level": "promoter_education",
    # Relevant Sector Experience (DPR 1.1)
    "experience": "promoter_experience_years",
    "experience_years": "promoter_experience_years",
    "years_of_experience": "promoter_experience_years",
    "prior_experience_years": "promoter_experience_years",
    "prior_experience": "promoter_experience_years",
    "relevant_sector_experience_years": "promoter_experience_years",
    "relevant_sector_experience": "promoter_experience_years",
    "sector_experience_years": "promoter_experience_years",
    "sector_experience": "promoter_experience_years",
    "relevant_experience": "promoter_experience_years",
    "industry_experience": "promoter_experience_years",
    "industry_experience_years": "promoter_experience_years",
    "professional_experience": "promoter_experience_years",
    "business_experience": "promoter_experience_years",
    "business_experience_years": "promoter_experience_years",
    "prior_business_experience": "promoter_experience_years",
    "entrepreneur_experience": "promoter_experience_years",
    "relevantsectorexperience": "promoter_experience_years",
    "experienceyears": "promoter_experience_years",
    "experience.years_of_experience": "promoter_experience_years",
    # Social Category
    "social_category": "promoter_social_category",
    "caste_category": "promoter_social_category",
    "promoter_caste_category": "promoter_social_category",
    "beneficiary_category": "promoter_social_category",
    "special_category": "promoter_social_category",
    "category_type": "promoter_social_category",
    # EDP & Skill Training
    "edp_training": "promoter_edp_training_status",
    "edp_training_status": "promoter_edp_training_status",
    "edp_status": "promoter_edp_training_status",
    "skill_training": "promoter_edp_training_status",
    "skill_training_status": "promoter_edp_training_status",
    "training_status": "promoter_edp_training_status",
    "training.edp_completed": "promoter_edp_training_status",
    "training.certifications": "promoter_edp_training_status",
    # Scheme
    "scheme": "target_scheme_code",
    "scheme_code": "target_scheme_code",
    "target_scheme": "target_scheme_code",
    # Business & Project
    "business_description": "business_activity",
    "raw_business_description": "business_activity",
    "activity": "business_activity",
    "constitution": "legal_constitution",
    "business_constitution": "legal_constitution",
    "ownership_structure": "legal_constitution",
    "entity_type": "legal_constitution",
    # Total Covered / Working Area (DPR 2.3)
    "total_covered_working_area_sqft": "covered_area_sqft",
    "carpet_area": "covered_area_sqft",
    "carpet_area_sqft": "covered_area_sqft",
    "working_area": "covered_area_sqft",
    "shop_area": "covered_area_sqft",
    "built_up_area": "covered_area_sqft",
    "premises_size": "covered_area_sqft",
    "floor_area": "covered_area_sqft",
    "covered_area": "covered_area_sqft",
    "resources.available_area_sqft": "covered_area_sqft",
    # Business Classification
    "archetype": "business_archetype",
    "category": "business_archetype",
    "nic": "nic_code",
    # Registrations
    "pan": "pan_number",
    "promoter_pan": "pan_number",
    "business_pan": "pan_number",
    "gst": "gst_number",
    "gstin": "gst_number",
    "udyam": "udyam_registration_number",
    "udyam_number": "udyam_registration_number",
    "udyam_registration": "udyam_registration_number",
    "msme_registration": "udyam_registration_number",
    # Financial items
    "cost_of_project": "total_project_cost",
    "total_cost": "total_project_cost",
    "working_capital": "cost_working_capital_margin",
    "working_capital_margin": "cost_working_capital_margin",
    "plant_machinery_cost": "cost_plant_machinery",
    "equipment_cost": "cost_plant_machinery",
    "land_building_cost": "cost_land_building",
    "project_cost": "total_project_cost",
    "promoter_margin": "promoter_equity_amount",
    "promoter_contribution": "promoter_equity_amount",
    "loan_amount": "bank_term_loan_amount",
    "term_loan": "bank_term_loan_amount",
}


def normalize_field_id(field_name: str) -> str:
    """Normalizes any field name or legacy alias to the canonical registered DPR field_id."""
    if not field_name:
        return field_name
    key = str(field_name).strip()
    if key in FIELD_REGISTRY_MAP:
        return key
    lower_key = key.lower()
    if lower_key in FIELD_REGISTRY_MAP:
        return lower_key
    if lower_key in CANONICAL_FIELD_ALIASES:
        return CANONICAL_FIELD_ALIASES[lower_key]
    try:
        from app.services.dpr_stage1.dpr_canonical_field_registry import resolve_canonical_id
        resolved = resolve_canonical_id(key)
        if resolved in FIELD_REGISTRY_MAP:
            return resolved
    except Exception:
        pass
    return CANONICAL_FIELD_ALIASES.get(lower_key, field_name)


def get_canonical_registry_stats() -> Dict[str, Any]:
    """Dynamically calculates canonical modules, sections, and fields count from canonical registry."""
    return {
        "total_modules": len(CANONICAL_MODULES),
        "total_sections": len(CANONICAL_SECTIONS),
        "total_fields": len(ALL_DPR_FIELDS),
    }

