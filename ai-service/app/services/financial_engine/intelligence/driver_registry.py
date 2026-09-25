"""
Financial Driver Registry.
Defines WHAT the financial model needs per archetype — not values.
Drivers describe requirements and semantics.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.financial_engine.intelligence.archetype_registry import FinancialArchetype


class DriverDefinition(BaseModel):
    driver_id: str
    label: str
    unit: str = "INR"
    data_type: str = "currency"  # currency, percentage, integer, float, enum, boolean
    required_for: List[str] = Field(default_factory=list)
    criticality: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    can_be_benchmarked: bool = False
    can_be_calculated: bool = False
    can_be_derived: bool = False
    default_benchmark_key: Optional[str] = None
    question_hi: Optional[str] = None
    question_en: Optional[str] = None
    enum_options: Optional[List[str]] = None
    sensitivity: str = "MEDIUM"  # HIGH, MEDIUM, LOW — financial impact
    # M2 derivation metadata (declarative specification, no M2 execution yet)
    derivation_rule: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)


# ─── Master Driver Catalog ───────────────────────────────────────────────────
_DRIVERS: Dict[str, DriverDefinition] = {}


def _d(driver_id: str, label: str, **kw) -> DriverDefinition:
    dd = DriverDefinition(driver_id=driver_id, label=label, **kw)
    _DRIVERS[driver_id] = dd
    return dd


# ── Common Drivers (all archetypes) ──
_d("ownership_type", "Premises Ownership", unit="enum", data_type="enum",
   required_for=["ALL"], criticality="HIGH", can_be_benchmarked=False,
   enum_options=["OWN", "RENTED", "LEASED", "SHARED"],
   question_hi="क्या दुकान/कार्यशाला आपकी अपनी है या किराये पर?",
   question_en="Is the shop/workshop owned or rented?", sensitivity="HIGH")

_d("monthly_rent", "Monthly Rent", unit="INR/month",
   required_for=["INVENTORY_RETAIL", "SERVICE", "SMALL_MANUFACTURING", "FOOD_PROCESSING", "TRADING", "REPAIR"],
   criticality="HIGH", can_be_benchmarked=True, sensitivity="HIGH",
   question_hi="मासिक किराया लगभग कितना होगा?",
   question_en="What will be the approximate monthly rent?")

_d("store_area", "Premises Area", unit="sqft", data_type="float",
   required_for=["INVENTORY_RETAIL", "SMALL_MANUFACTURING", "FOOD_PROCESSING"],
   criticality="MEDIUM", can_be_benchmarked=True, sensitivity="MEDIUM",
   question_hi="दुकान/कार्यशाला लगभग कितने वर्ग फुट की होगी?",
   question_en="What will be the approximate area in square feet?")

_d("staff_count", "Staff Count", unit="persons", data_type="integer",
   required_for=["ALL"], criticality="MEDIUM", can_be_benchmarked=True, sensitivity="MEDIUM",
   question_hi="क्या शुरुआत में आप खुद संभालेंगे या कर्मचारी रखेंगे? कितने?",
   question_en="Will you manage alone or hire staff? How many?")

_d("salary_cost", "Monthly Staff Salary", unit="INR/month",
   required_for=["ALL"], criticality="MEDIUM", can_be_benchmarked=True, can_be_derived=True, sensitivity="MEDIUM")

_d("electricity_cost", "Monthly Electricity", unit="INR/month",
   required_for=["ALL"], criticality="LOW", can_be_benchmarked=True, sensitivity="LOW")

_d("transport_cost", "Monthly Transport", unit="INR/month",
   required_for=["INVENTORY_RETAIL", "TRADING", "SMALL_MANUFACTURING", "FOOD_PROCESSING"],
   criticality="LOW", can_be_benchmarked=True, sensitivity="LOW")

_d("marketing_cost", "Monthly Marketing", unit="INR/month",
   required_for=["ALL"], criticality="LOW", can_be_benchmarked=True, sensitivity="LOW")

# ── Retail-Specific ──
_d("opening_inventory", "Opening Inventory Investment", unit="INR",
   required_for=["INVENTORY_RETAIL", "TRADING"], criticality="HIGH",
   can_be_benchmarked=True, default_benchmark_key="typical_working_capital_monthly_inr", sensitivity="HIGH",
   question_hi="शुरुआती स्टॉक/माल में कितना निवेश करेंगे?",
   question_en="How much will you invest in opening stock?")

_d("inventory_days", "Inventory Holding Period", unit="days", data_type="integer",
   required_for=["INVENTORY_RETAIL", "TRADING"], criticality="MEDIUM",
   can_be_benchmarked=True, sensitivity="MEDIUM")

_d("monthly_transactions", "Expected Monthly Transactions", unit="count/month", data_type="integer",
   required_for=["INVENTORY_RETAIL", "SERVICE"], criticality="MEDIUM",
   can_be_benchmarked=True, sensitivity="HIGH")

_d("average_ticket", "Average Transaction Value", unit="INR",
   required_for=["INVENTORY_RETAIL", "SERVICE"], criticality="MEDIUM",
   can_be_benchmarked=True, sensitivity="HIGH")

_d("gross_margin", "Gross Margin", unit="%", data_type="percentage",
   required_for=["INVENTORY_RETAIL", "TRADING", "SMALL_MANUFACTURING", "FOOD_PROCESSING"],
   criticality="HIGH", can_be_benchmarked=True, default_benchmark_key="gross_margin_pct", sensitivity="HIGH")

# ── Manufacturing-Specific ──
_d("installed_capacity", "Installed Capacity", unit="units/day", data_type="float",
   required_for=["SMALL_MANUFACTURING", "FOOD_PROCESSING"], criticality="HIGH",
   can_be_benchmarked=True, sensitivity="HIGH",
   question_hi="प्रतिदिन कितनी इकाइयाँ/मात्रा उत्पादन कर पाएंगे?",
   question_en="How many units/quantity can you produce per day?")

_d("operating_days", "Operating Days per Month", unit="days/month", data_type="integer",
   required_for=["SMALL_MANUFACTURING", "FOOD_PROCESSING", "SERVICE"], criticality="MEDIUM",
   can_be_benchmarked=True, sensitivity="MEDIUM")

_d("utilization", "Capacity Utilization", unit="%", data_type="percentage",
   required_for=["SMALL_MANUFACTURING", "FOOD_PROCESSING"], criticality="MEDIUM",
   can_be_benchmarked=True, sensitivity="HIGH")

_d("selling_price", "Unit Selling Price", unit="INR/unit",
   required_for=["SMALL_MANUFACTURING", "FOOD_PROCESSING"], criticality="HIGH",
   can_be_benchmarked=True, sensitivity="HIGH",
   question_hi="प्रति इकाई बिक्री मूल्य क्या होगा?",
   question_en="What will be the selling price per unit?")

_d("raw_material_cost", "Raw Material Cost per Unit", unit="INR/unit",
   required_for=["SMALL_MANUFACTURING", "FOOD_PROCESSING"], criticality="HIGH",
   can_be_benchmarked=True, sensitivity="HIGH")

# ── Service-Specific ──
_d("jobs_per_day", "Jobs/Customers per Day", unit="count/day", data_type="integer",
   required_for=["SERVICE", "REPAIR"], criticality="HIGH",
   can_be_benchmarked=True, sensitivity="HIGH",
   question_hi="प्रतिदिन कितने ग्राहकों/कार्यों की अपेक्षा है?",
   question_en="How many customers/jobs do you expect per day?")

_d("average_realization", "Average Revenue per Job", unit="INR/job",
   required_for=["SERVICE", "REPAIR"], criticality="HIGH",
   can_be_benchmarked=True, sensitivity="HIGH")

_d("material_cost_per_job", "Material Cost per Job", unit="INR/job",
   required_for=["REPAIR"], criticality="MEDIUM",
   can_be_benchmarked=True, sensitivity="MEDIUM")

# ── Working Capital ──
_d("working_capital_cycle", "Working Capital Cycle", unit="days", data_type="integer",
   required_for=["INVENTORY_RETAIL", "TRADING", "SMALL_MANUFACTURING"],
   criticality="MEDIUM", can_be_benchmarked=True, can_be_calculated=True, sensitivity="MEDIUM")

_d("receivable_days", "Receivable Days", unit="days", data_type="integer",
   required_for=["TRADING", "SMALL_MANUFACTURING"], criticality="MEDIUM",
   can_be_benchmarked=True, sensitivity="MEDIUM")

_d("payable_days", "Payable Days", unit="days", data_type="integer",
   required_for=["TRADING", "SMALL_MANUFACTURING"], criticality="MEDIUM",
   can_be_benchmarked=True, sensitivity="MEDIUM")


# ─── Archetype → Required Drivers Mapping ────────────────────────────────────
_ARCHETYPE_DRIVERS: Dict[str, List[str]] = {
    FinancialArchetype.INVENTORY_RETAIL.value: [
        "ownership_type", "monthly_rent", "store_area", "opening_inventory",
        "inventory_days", "monthly_transactions", "average_ticket", "gross_margin",
        "staff_count", "salary_cost", "electricity_cost", "transport_cost",
        "marketing_cost", "working_capital_cycle",
    ],
    FinancialArchetype.SMALL_MANUFACTURING.value: [
        "ownership_type", "monthly_rent", "store_area", "installed_capacity",
        "operating_days", "utilization", "selling_price", "raw_material_cost",
        "gross_margin", "staff_count", "salary_cost", "electricity_cost",
        "transport_cost", "inventory_days", "receivable_days", "payable_days",
    ],
    FinancialArchetype.FOOD_PROCESSING.value: [
        "ownership_type", "monthly_rent", "store_area", "installed_capacity",
        "operating_days", "utilization", "selling_price", "raw_material_cost",
        "gross_margin", "staff_count", "salary_cost", "electricity_cost",
    ],
    FinancialArchetype.SERVICE.value: [
        "ownership_type", "monthly_rent", "jobs_per_day", "average_realization",
        "operating_days", "staff_count", "salary_cost", "electricity_cost",
        "marketing_cost",
    ],
    FinancialArchetype.TRADING.value: [
        "ownership_type", "monthly_rent", "opening_inventory", "inventory_days",
        "monthly_transactions", "average_ticket", "gross_margin",
        "staff_count", "salary_cost", "transport_cost",
    ],
    FinancialArchetype.AGRICULTURE.value: [
        "ownership_type", "installed_capacity", "operating_days",
        "selling_price", "raw_material_cost", "staff_count", "salary_cost",
    ],
    FinancialArchetype.LIVESTOCK.value: [
        "ownership_type", "installed_capacity", "selling_price",
        "raw_material_cost", "staff_count", "salary_cost",
    ],
    FinancialArchetype.CRAFT.value: [
        "ownership_type", "monthly_rent", "jobs_per_day", "average_realization",
        "raw_material_cost", "staff_count", "salary_cost", "electricity_cost",
    ],
    FinancialArchetype.REPAIR.value: [
        "ownership_type", "monthly_rent", "jobs_per_day", "average_realization",
        "material_cost_per_job", "staff_count", "salary_cost", "electricity_cost",
    ],
    FinancialArchetype.OTHER.value: [
        "ownership_type", "monthly_rent", "staff_count", "salary_cost",
        "electricity_cost", "gross_margin",
    ],
}


class DriverRegistry:
    """Registry of financial driver definitions and archetype mappings."""

    def get_driver(self, driver_id: str) -> Optional[DriverDefinition]:
        return _DRIVERS.get(driver_id)

    def get_all_drivers(self) -> Dict[str, DriverDefinition]:
        return dict(_DRIVERS)

    def get_drivers_for_archetype(self, archetype: FinancialArchetype) -> List[DriverDefinition]:
        driver_ids = _ARCHETYPE_DRIVERS.get(archetype.value, _ARCHETYPE_DRIVERS[FinancialArchetype.OTHER.value])
        return [_DRIVERS[did] for did in driver_ids if did in _DRIVERS]

    def get_driver_ids_for_archetype(self, archetype: FinancialArchetype) -> List[str]:
        return _ARCHETYPE_DRIVERS.get(archetype.value, _ARCHETYPE_DRIVERS[FinancialArchetype.OTHER.value])

    def get_high_criticality_drivers(self, archetype: FinancialArchetype) -> List[DriverDefinition]:
        return [d for d in self.get_drivers_for_archetype(archetype) if d.criticality == "HIGH"]


# Global singleton
driver_registry = DriverRegistry()
