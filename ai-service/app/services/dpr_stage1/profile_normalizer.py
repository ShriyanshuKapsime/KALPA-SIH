"""
KALPA DPR Stage 14.1 / 14.2 — Type-Safe Entrepreneur Profile Normalizer.
Authoritative normalization layer for upstream profile data (Stages 1–13) before
DPR context construction and EntrepreneurContext validation.

Architecture Invariants:
1. Eliminates numeric enum leaks (e.g. 2.0 -> "12TH_PASS" / "Higher Secondary (12th Pass)")
2. Preserves 0.0 / 0 as valid non-null experience years (no truthiness loss)
3. Never converts 2.0 -> "2.0" for textual enum fields.
4. Returns SOURCE_MAPPING_ERROR if an enum ID or type cannot be resolved, never crashing with 500.
5. Captures complete diagnostic provenance: raw_value, raw_type, canonical_value, canonical_type,
   normalization_method, source, source_path, source_stage.
"""
import re
import logging
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EducationStatus(str, Enum):
    NO_FORMAL_EDUCATION = "NO_FORMAL_EDUCATION"
    BELOW_8TH = "BELOW_8TH"
    SECONDARY_10TH = "10TH_PASS"
    HIGHER_SECONDARY_12TH = "12TH_PASS"
    GRADUATE = "GRADUATE"
    POST_GRADUATE = "POST_GRADUATE"
    PROFESSIONAL_DOCTORATE = "PROFESSIONAL_DOCTORATE"
    UNKNOWN = "UNKNOWN"


class SocialCategory(str, Enum):
    GENERAL = "GENERAL"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    MINORITY = "MINORITY"
    WOMEN = "WOMEN"
    EWS = "EWS"
    PH_PWD = "PH_PWD"
    UNKNOWN = "UNKNOWN"


class TrainingStatus(str, Enum):
    NOT_UNDERTAKEN = "NOT_UNDERTAKEN"
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    PLANNED = "PLANNED"
    UNKNOWN = "UNKNOWN"


class PremisesStatus(str, Enum):
    OWNED = "OWNED"
    RENTED = "RENTED"
    LEASED = "LEASED"
    PROPOSED_PURCHASE = "PROPOSED_PURCHASE"
    ANCESTRAL = "ANCESTRAL"
    UNKNOWN = "UNKNOWN"


class LegalConstitution(str, Enum):
    PROPRIETORSHIP = "PROPRIETORSHIP"
    PARTNERSHIP = "PARTNERSHIP"
    LLP = "LLP"
    PRIVATE_LIMITED = "PRIVATE_LIMITED"
    FPO = "FPO"
    COOPERATIVE = "COOPERATIVE"
    ONE_PERSON_COMPANY = "ONE_PERSON_COMPANY"
    UNKNOWN = "UNKNOWN"


# Human-Readable Display Labels
EDUCATION_DISPLAY_LABELS: Dict[EducationStatus, str] = {
    EducationStatus.NO_FORMAL_EDUCATION: "No Formal Education",
    EducationStatus.BELOW_8TH: "Below 8th Pass",
    EducationStatus.SECONDARY_10TH: "Secondary (10th Pass)",
    EducationStatus.HIGHER_SECONDARY_12TH: "Higher Secondary (12th Pass)",
    EducationStatus.GRADUATE: "Graduate",
    EducationStatus.POST_GRADUATE: "Post Graduate",
    EducationStatus.PROFESSIONAL_DOCTORATE: "Doctorate / Professional Degree",
    EducationStatus.UNKNOWN: "Unknown Education",
}

SOCIAL_CATEGORY_DISPLAY_LABELS: Dict[SocialCategory, str] = {
    SocialCategory.GENERAL: "General",
    SocialCategory.OBC: "Other Backward Class (OBC)",
    SocialCategory.SC: "Scheduled Caste (SC)",
    SocialCategory.ST: "Scheduled Tribe (ST)",
    SocialCategory.MINORITY: "Minority Community",
    SocialCategory.WOMEN: "Women Entrepreneur",
    SocialCategory.EWS: "Economically Weaker Section (EWS)",
    SocialCategory.PH_PWD: "Person with Disability / Ex-Servicemen",
    SocialCategory.UNKNOWN: "General",
}

TRAINING_STATUS_DISPLAY_LABELS: Dict[TrainingStatus, str] = {
    TrainingStatus.NOT_UNDERTAKEN: "Not Yet Undertaken",
    TrainingStatus.COMPLETED: "Completed (EDP/Skill Certified)",
    TrainingStatus.IN_PROGRESS: "In Progress / Ongoing Training",
    TrainingStatus.PLANNED: "Planned / Scheduled Training",
    TrainingStatus.UNKNOWN: "Not Yet Undertaken",
}

PREMISES_STATUS_DISPLAY_LABELS: Dict[PremisesStatus, str] = {
    PremisesStatus.OWNED: "Owned",
    PremisesStatus.RENTED: "Rented",
    PremisesStatus.LEASED: "Leased",
    PremisesStatus.PROPOSED_PURCHASE: "Proposed for Purchase / Construction",
    PremisesStatus.ANCESTRAL: "Ancestral Property",
    PremisesStatus.UNKNOWN: "Rented",
}

LEGAL_CONSTITUTION_DISPLAY_LABELS: Dict[LegalConstitution, str] = {
    LegalConstitution.PROPRIETORSHIP: "Sole Proprietorship",
    LegalConstitution.PARTNERSHIP: "Partnership Firm",
    LegalConstitution.LLP: "Limited Liability Partnership (LLP)",
    LegalConstitution.PRIVATE_LIMITED: "Private Limited Company",
    LegalConstitution.FPO: "Farmer Producer Org (FPO) / Cooperative",
    LegalConstitution.COOPERATIVE: "Cooperative Society",
    LegalConstitution.ONE_PERSON_COMPANY: "One Person Company (OPC)",
    LegalConstitution.UNKNOWN: "Sole Proprietorship",
}

# Authoritative Numeric Enum ID Mappings
EDUCATION_ID_MAP: Dict[int, EducationStatus] = {
    0: EducationStatus.BELOW_8TH,
    1: EducationStatus.SECONDARY_10TH,
    2: EducationStatus.HIGHER_SECONDARY_12TH,
    3: EducationStatus.GRADUATE,
    4: EducationStatus.POST_GRADUATE,
    5: EducationStatus.PROFESSIONAL_DOCTORATE,
}

SOCIAL_CATEGORY_ID_MAP: Dict[int, SocialCategory] = {
    1: SocialCategory.GENERAL,
    2: SocialCategory.OBC,
    3: SocialCategory.SC,
    4: SocialCategory.ST,
    5: SocialCategory.MINORITY,
    6: SocialCategory.WOMEN,
    7: SocialCategory.EWS,
    8: SocialCategory.PH_PWD,
}

TRAINING_STATUS_ID_MAP: Dict[int, TrainingStatus] = {
    0: TrainingStatus.NOT_UNDERTAKEN,
    1: TrainingStatus.COMPLETED,
    2: TrainingStatus.IN_PROGRESS,
    3: TrainingStatus.PLANNED,
}


class NormalizedFieldResult(BaseModel):
    """Diagnostic provenance container for normalized profile fields."""
    field_id: str
    canonical_value: Any
    canonical_enum: Optional[str] = None
    display_label: Optional[str] = None
    raw_value: Any = None
    raw_type: str = "NoneType"
    canonical_type: str = "str"
    status: str = "RESOLVED_PROFILE"  # RESOLVED_PROFILE, RESOLVED_USER, SOURCE_MAPPING_ERROR, UNKNOWN
    source: str = "UPSTREAM_PROFILE"
    source_stage: str = "STAGE_10"
    source_path: str = ""
    normalization_method: str = "DIRECT"
    is_valid: bool = True
    error_message: Optional[str] = None


class ProfileNormalizer:
    """
    Canonical Profile Normalizer.
    Enforces field-specific type contracts, resolves numeric enum IDs to human-readable strings,
    and produces fully-provenanced NormalizedFieldResult records.
    """

    @staticmethod
    def _get_raw_type(val: Any) -> str:
        if val is None:
            return "NoneType"
        return type(val).__name__

    @staticmethod
    def _try_parse_numeric_id(val: Any) -> Optional[int]:
        """Safely parses int/float/numeric strings to integer ID without float truncation errors."""
        if val is None or isinstance(val, (dict, list)):
            return None
        if isinstance(val, bool):
            return 1 if val else 0
        if isinstance(val, (int, float)):
            try:
                f = float(val)
                if f.is_integer() and 0 <= f <= 50:
                    return int(f)
            except (ValueError, OverflowError):
                return None
        if isinstance(val, str):
            s = val.strip()
            if s.isdigit():
                return int(s)
            try:
                f = float(s)
                if f.is_integer() and 0 <= f <= 50:
                    return int(f)
            except ValueError:
                return None
        return None

    @staticmethod
    def _matches_any_term(text: str, terms: list) -> bool:
        """Matches exact word-bounded terms to avoid substring collision."""
        t_low = text.lower()
        for term in terms:
            t = term.strip().lower()
            if not t:
                continue
            escaped = re.escape(t)
            prefix = r"\b" if re.match(r"^\w", t) else ""
            suffix = r"\b" if re.match(r".*\w$", t) else ""
            pattern = rf"{prefix}{escaped}{suffix}"
            if re.search(pattern, t_low):
                return True
        return False

    @classmethod
    def normalize_education(
        cls,
        raw_value: Any,
        source_path: str = "profile.education",
        source_stage: str = "STAGE_10",
        source_type: str = "UPSTREAM_PROFILE"
    ) -> NormalizedFieldResult:
        """
        Normalizes promoter education to canonical EducationStatus and display string.
        Resolves enum IDs (e.g. 2.0 -> HIGHER_SECONDARY_12TH / Higher Secondary (12th Pass)).
        """
        raw_type = cls._get_raw_type(raw_value)

        if raw_value in (None, "", "UNKNOWN", "null", "None"):
            return NormalizedFieldResult(
                field_id="promoter_education",
                canonical_value=None,
                canonical_enum=None,
                display_label=None,
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="UNKNOWN",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="EMPTY_FALLBACK",
                is_valid=True
            )

        # 1. Check numeric ID (e.g. 2.0 -> 12TH_PASS)
        num_id = cls._try_parse_numeric_id(raw_value)
        if num_id is not None and num_id in EDUCATION_ID_MAP:
            enum_val = EDUCATION_ID_MAP[num_id]
            label = EDUCATION_DISPLAY_LABELS[enum_val]
            return NormalizedFieldResult(
                field_id="promoter_education",
                canonical_value=enum_val.value,
                canonical_enum=enum_val.value,
                display_label=label,
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="ENUM_ID_TO_LABEL",
                is_valid=True
            )

        # 2. String matching & text synonyms
        s_val = str(raw_value).strip()
        s_low = s_val.lower()

        # Check existing enum values (excluding UNKNOWN to avoid false catch-all)
        for e in EducationStatus:
            if e == EducationStatus.UNKNOWN:
                continue
            if s_low == e.value.lower() or s_low == e.name.lower():
                return NormalizedFieldResult(
                    field_id="promoter_education",
                    canonical_value=e.value,
                    canonical_enum=e.value,
                    display_label=EDUCATION_DISPLAY_LABELS[e],
                    raw_value=raw_value,
                    raw_type=raw_type,
                    canonical_type="string",
                    status="RESOLVED_PROFILE",
                    source=source_type,
                    source_stage=source_stage,
                    source_path=source_path,
                    normalization_method="CANONICAL_ENUM_MATCH",
                    is_valid=True
                )

        # Synonyms with word boundary checks
        if cls._matches_any_term(s_low, ["phd", "ph.d", "ph.d.", "doctorate", "doctoral", "doctor", "ca", "cs", "icwa", "mbbs", "llb", "d.phil", "post doc", "postdoc"]):
            e = EducationStatus.PROFESSIONAL_DOCTORATE
        elif cls._matches_any_term(s_low, ["post graduate", "post graduation", "postgraduate", "masters", "master", "m.tech", "mtech", "m.sc", "msc", "mba", "m.com", "mcom", "m.a", "ma", "mca", "me", "pg", "m.e", "m.pharm"]):
            e = EducationStatus.POST_GRADUATE
        elif cls._matches_any_term(s_low, ["graduate", "graduation", "bachelors", "bachelor", "degree", "b.tech", "btech", "b.sc", "bsc", "b.com", "bcom", "b.a", "ba", "bca", "bba", "b.e", "be", "ug", "b.pharm", "b.ed", "ll.b"]):
            e = EducationStatus.GRADUATE
        elif cls._matches_any_term(s_low, ["12th", "higher secondary", "intermediate", "hsc", "10+2", "class 12", "xii", "senior secondary", "+2", "12th pass", "class xii", "12 pass"]):
            e = EducationStatus.HIGHER_SECONDARY_12TH
        elif cls._matches_any_term(s_low, ["10th", "secondary", "metric", "matriculation", "sslc", "class 10", "high school", "10th pass", "class x", "10 pass"]):
            e = EducationStatus.SECONDARY_10TH
        elif cls._matches_any_term(s_low, ["below 8th", "8th", "8th pass", "primary", "middle school", "elementary", "5th", "5th pass", "7th", "under 8th"]):
            e = EducationStatus.BELOW_8TH
        elif cls._matches_any_term(s_low, ["illiterate", "no formal", "no formal education", "uneducated", "none", "nil"]):
            e = EducationStatus.NO_FORMAL_EDUCATION
        else:
            e = None

        if e:
            return NormalizedFieldResult(
                field_id="promoter_education",
                canonical_value=e.value,
                canonical_enum=e.value,
                display_label=EDUCATION_DISPLAY_LABELS[e],
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="TEXT_SYNONYM_MAPPING",
                is_valid=True
            )

        # Unmappable input: Record SOURCE_MAPPING_ERROR diagnostics
        logger.warning(
            f"[ProfileNormalizer] Unmappable promoter_education: raw_value={raw_value} "
            f"raw_type={raw_type} source_path={source_path}"
        )
        return NormalizedFieldResult(
            field_id="promoter_education",
            canonical_value=None,
            canonical_enum=None,
            display_label=None,
            raw_value=raw_value,
            raw_type=raw_type,
            canonical_type="string",
            status="SOURCE_MAPPING_ERROR",
            source=source_type,
            source_stage=source_stage,
            source_path=source_path,
            normalization_method="MAPPING_FAILED",
            is_valid=False,
            error_message=f"Unable to resolve education enum from '{raw_value}' ({raw_type})"
        )

    @classmethod
    def normalize_social_category(
        cls,
        raw_value: Any,
        source_path: str = "profile.social_category",
        source_stage: str = "STAGE_10",
        source_type: str = "UPSTREAM_PROFILE"
    ) -> NormalizedFieldResult:
        """
        Normalizes promoter social category to canonical SocialCategory.
        Resolves numeric IDs (e.g. 2.0 -> OBC / Other Backward Class (OBC)).
        """
        raw_type = cls._get_raw_type(raw_value)

        if raw_value in (None, "", "UNKNOWN", "null", "None"):
            return NormalizedFieldResult(
                field_id="promoter_social_category",
                canonical_value="GENERAL",
                canonical_enum="GENERAL",
                display_label="General",
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="DEFAULT_FALLBACK",
                is_valid=True
            )

        # 1. Numeric ID resolution (e.g. 2.0 -> OBC)
        num_id = cls._try_parse_numeric_id(raw_value)
        if num_id is not None and num_id in SOCIAL_CATEGORY_ID_MAP:
            enum_val = SOCIAL_CATEGORY_ID_MAP[num_id]
            label = SOCIAL_CATEGORY_DISPLAY_LABELS[enum_val]
            return NormalizedFieldResult(
                field_id="promoter_social_category",
                canonical_value=enum_val.value,
                canonical_enum=enum_val.value,
                display_label=label,
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="ENUM_ID_TO_LABEL",
                is_valid=True
            )

        s_val = str(raw_value).strip()
        s_low = s_val.lower()

        # Check existing enum values (excluding UNKNOWN)
        for e in SocialCategory:
            if e == SocialCategory.UNKNOWN:
                continue
            if s_low == e.value.lower() or s_low == e.name.lower():
                return NormalizedFieldResult(
                    field_id="promoter_social_category",
                    canonical_value=e.value,
                    canonical_enum=e.value,
                    display_label=SOCIAL_CATEGORY_DISPLAY_LABELS[e],
                    raw_value=raw_value,
                    raw_type=raw_type,
                    canonical_type="string",
                    status="RESOLVED_PROFILE",
                    source=source_type,
                    source_stage=source_stage,
                    source_path=source_path,
                    normalization_method="CANONICAL_ENUM_MATCH",
                    is_valid=True
                )

        if cls._matches_any_term(s_low, ["women", "female", "woman", "mahila"]):
            e = SocialCategory.WOMEN
        elif cls._matches_any_term(s_low, ["pwd", "ph", "disability", "handicap", "divyang", "ex-servicemen", "ex servicemen"]):
            e = SocialCategory.PH_PWD
        elif cls._matches_any_term(s_low, ["minority", "muslim", "christian", "sikh", "jain", "buddhist", "parsi"]):
            e = SocialCategory.MINORITY
        elif cls._matches_any_term(s_low, ["ews", "economically weaker"]):
            e = SocialCategory.EWS
        elif cls._matches_any_term(s_low, ["st", "scheduled tribe", "tribal", "adivasi"]):
            e = SocialCategory.ST
        elif cls._matches_any_term(s_low, ["sc", "scheduled caste", "dalit"]):
            e = SocialCategory.SC
        elif cls._matches_any_term(s_low, ["obc", "other backward", "backward class", "sebc"]):
            e = SocialCategory.OBC
        elif cls._matches_any_term(s_low, ["general", "open", "ur", "unreserved", "gen"]):
            e = SocialCategory.GENERAL
        else:
            e = None

        if e:
            return NormalizedFieldResult(
                field_id="promoter_social_category",
                canonical_value=e.value,
                canonical_enum=e.value,
                display_label=SOCIAL_CATEGORY_DISPLAY_LABELS[e],
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="TEXT_SYNONYM_MAPPING",
                is_valid=True
            )

        logger.warning(
            f"[ProfileNormalizer] Unmappable promoter_social_category: raw_value={raw_value} "
            f"raw_type={raw_type} source_path={source_path}"
        )
        return NormalizedFieldResult(
            field_id="promoter_social_category",
            canonical_value=None,
            canonical_enum=None,
            display_label=None,
            raw_value=raw_value,
            raw_type=raw_type,
            canonical_type="string",
            status="SOURCE_MAPPING_ERROR",
            source=source_type,
            source_stage=source_stage,
            source_path=source_path,
            normalization_method="MAPPING_FAILED",
            is_valid=False,
            error_message=f"Unable to resolve social category from '{raw_value}' ({raw_type})"
        )

    @classmethod
    def normalize_training_status(
        cls,
        raw_value: Any,
        source_path: str = "profile.edp_training_status",
        source_stage: str = "STAGE_10",
        source_type: str = "UPSTREAM_PROFILE"
    ) -> NormalizedFieldResult:
        """
        Normalizes promoter EDP training status to canonical TrainingStatus.
        Resolves numeric IDs / booleans (e.g. 2.0 -> IN_PROGRESS, True -> COMPLETED).
        """
        raw_type = cls._get_raw_type(raw_value)

        if raw_value in (None, "", "UNKNOWN", "null", "None"):
            return NormalizedFieldResult(
                field_id="promoter_edp_training_status",
                canonical_value="NOT_UNDERTAKEN",
                canonical_enum="NOT_UNDERTAKEN",
                display_label="Not Yet Undertaken",
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="DEFAULT_FALLBACK",
                is_valid=True
            )

        # 1. Numeric ID & boolean resolution
        num_id = cls._try_parse_numeric_id(raw_value)
        if num_id is not None and num_id in TRAINING_STATUS_ID_MAP:
            enum_val = TRAINING_STATUS_ID_MAP[num_id]
            label = TRAINING_STATUS_DISPLAY_LABELS[enum_val]
            return NormalizedFieldResult(
                field_id="promoter_edp_training_status",
                canonical_value=enum_val.value,
                canonical_enum=enum_val.value,
                display_label=label,
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="ENUM_ID_TO_LABEL",
                is_valid=True
            )

        s_val = str(raw_value).strip()
        s_low = s_val.lower()

        # Check existing enum values or known subtypes (e.g. COMPLETED_RSETI, COMPLETED_EDI)
        if s_low.startswith("completed_"):
            return NormalizedFieldResult(
                field_id="promoter_edp_training_status",
                canonical_value=s_val.upper(),
                canonical_enum=TrainingStatus.COMPLETED.value,
                display_label=f"Completed ({s_val.upper().replace('COMPLETED_', '')})",
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="SPECIFIC_SUBTYPE_MATCH",
                is_valid=True
            )

        for e in TrainingStatus:
            if e == TrainingStatus.UNKNOWN:
                continue
            if s_low == e.value.lower() or s_low == e.name.lower():
                return NormalizedFieldResult(
                    field_id="promoter_edp_training_status",
                    canonical_value=e.value,
                    canonical_enum=e.value,
                    display_label=TRAINING_STATUS_DISPLAY_LABELS[e],
                    raw_value=raw_value,
                    raw_type=raw_type,
                    canonical_type="string",
                    status="RESOLVED_PROFILE",
                    source=source_type,
                    source_stage=source_stage,
                    source_path=source_path,
                    normalization_method="CANONICAL_ENUM_MATCH",
                    is_valid=True
                )

        if cls._matches_any_term(s_low, ["completed", "done", "yes", "certified", "rseti", "pmkvy", "edp completed", "true"]):
            e = TrainingStatus.COMPLETED
        elif cls._matches_any_term(s_low, ["in progress", "ongoing", "undergoing", "pursuing", "in_progress", "underway"]):
            e = TrainingStatus.IN_PROGRESS
        elif cls._matches_any_term(s_low, ["planned", "scheduled", "applied", "registered", "upcoming"]):
            e = TrainingStatus.PLANNED
        elif cls._matches_any_term(s_low, ["not undertaken", "not done", "no", "none", "nil", "not yet", "false", "uncompleted", "not_undertaken"]):
            e = TrainingStatus.NOT_UNDERTAKEN
        else:
            e = None

        if e:
            return NormalizedFieldResult(
                field_id="promoter_edp_training_status",
                canonical_value=e.value,
                canonical_enum=e.value,
                display_label=TRAINING_STATUS_DISPLAY_LABELS[e],
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="TEXT_SYNONYM_MAPPING",
                is_valid=True
            )

        logger.warning(
            f"[ProfileNormalizer] Unmappable promoter_edp_training_status: raw_value={raw_value} "
            f"raw_type={raw_type} source_path={source_path}"
        )
        return NormalizedFieldResult(
            field_id="promoter_edp_training_status",
            canonical_value=None,
            canonical_enum=None,
            display_label=None,
            raw_value=raw_value,
            raw_type=raw_type,
            canonical_type="string",
            status="SOURCE_MAPPING_ERROR",
            source=source_type,
            source_stage=source_stage,
            source_path=source_path,
            normalization_method="MAPPING_FAILED",
            is_valid=False,
            error_message=f"Unable to resolve EDP training status from '{raw_value}' ({raw_type})"
        )

    @classmethod
    def normalize_experience_years(
        cls,
        raw_value: Any,
        source_path: str = "profile.experience_years",
        source_stage: str = "STAGE_10",
        source_type: str = "UPSTREAM_PROFILE"
    ) -> NormalizedFieldResult:
        """
        Normalizes promoter experience years to numeric float.
        Crucially: 0.0 or 0 is preserved as valid experience (not None or UNKNOWN).
        """
        raw_type = cls._get_raw_type(raw_value)

        if raw_value in (None, "", "UNKNOWN", "null", "None"):
            return NormalizedFieldResult(
                field_id="promoter_experience_years",
                canonical_value=None,
                display_label=None,
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="float",
                status="UNKNOWN",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="EMPTY_FALLBACK",
                is_valid=True
            )

        if isinstance(raw_value, (int, float)):
            f_val = float(raw_value)
            if f_val >= 0:
                return NormalizedFieldResult(
                    field_id="promoter_experience_years",
                    canonical_value=f_val,
                    display_label=f"{int(f_val) if f_val.is_integer() else f_val} Years",
                    raw_value=raw_value,
                    raw_type=raw_type,
                    canonical_type="float",
                    status="RESOLVED_PROFILE",
                    source=source_type,
                    source_stage=source_stage,
                    source_path=source_path,
                    normalization_method="DIRECT_NUMERIC",
                    is_valid=True
                )

        if isinstance(raw_value, str):
            s = raw_value.strip()
            match = re.search(r"[-+]?\d*\.?\d+", s)
            if match:
                try:
                    f_val = float(match.group(0))
                    if f_val >= 0:
                        return NormalizedFieldResult(
                            field_id="promoter_experience_years",
                            canonical_value=f_val,
                            display_label=f"{int(f_val) if f_val.is_integer() else f_val} Years",
                            raw_value=raw_value,
                            raw_type=raw_type,
                            canonical_type="float",
                            status="RESOLVED_PROFILE",
                            source=source_type,
                            source_stage=source_stage,
                            source_path=source_path,
                            normalization_method="REGEX_PARSED_FLOAT",
                            is_valid=True
                        )
                except ValueError:
                    pass

        return NormalizedFieldResult(
            field_id="promoter_experience_years",
            canonical_value=None,
            display_label=None,
            raw_value=raw_value,
            raw_type=raw_type,
            canonical_type="float",
            status="SOURCE_MAPPING_ERROR",
            source=source_type,
            source_stage=source_stage,
            source_path=source_path,
            normalization_method="MAPPING_FAILED",
            is_valid=False,
            error_message=f"Unable to parse experience years from '{raw_value}' ({raw_type})"
        )

    @classmethod
    def normalize_premises_status(
        cls,
        raw_value: Any,
        source_path: str = "profile.premises_status",
        source_stage: str = "STAGE_1",
        source_type: str = "UPSTREAM_PROFILE"
    ) -> NormalizedFieldResult:
        raw_type = cls._get_raw_type(raw_value)

        if raw_value in (None, "", "UNKNOWN", "null", "None"):
            return NormalizedFieldResult(
                field_id="premises_status",
                canonical_value=None,
                canonical_enum=None,
                display_label=None,
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="UNKNOWN",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="EMPTY_FALLBACK",
                is_valid=True
            )

        s_val = str(raw_value).strip()
        s_low = s_val.lower()

        for e in PremisesStatus:
            if e == PremisesStatus.UNKNOWN:
                continue
            if s_low == e.value.lower() or s_low == e.name.lower():
                return NormalizedFieldResult(
                    field_id="premises_status",
                    canonical_value=e.value,
                    canonical_enum=e.value,
                    display_label=PREMISES_STATUS_DISPLAY_LABELS[e],
                    raw_value=raw_value,
                    raw_type=raw_type,
                    canonical_type="string",
                    status="RESOLVED_PROFILE",
                    source=source_type,
                    source_stage=source_stage,
                    source_path=source_path,
                    normalization_method="CANONICAL_ENUM_MATCH",
                    is_valid=True
                )

        if cls._matches_any_term(s_low, ["own", "owned", "self owned", "already owned", "freehold"]):
            e = PremisesStatus.OWNED
        elif cls._matches_any_term(s_low, ["rent", "rented", "rental"]):
            e = PremisesStatus.RENTED
        elif cls._matches_any_term(s_low, ["lease", "leased", "leasehold"]):
            e = PremisesStatus.LEASED
        elif cls._matches_any_term(s_low, ["purchase", "proposed", "buy", "construct", "construction"]):
            e = PremisesStatus.PROPOSED_PURCHASE
        elif cls._matches_any_term(s_low, ["ancestral", "family", "inherited"]):
            e = PremisesStatus.ANCESTRAL
        else:
            e = None

        if e:
            return NormalizedFieldResult(
                field_id="premises_status",
                canonical_value=e.value,
                canonical_enum=e.value,
                display_label=PREMISES_STATUS_DISPLAY_LABELS[e],
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="TEXT_SYNONYM_MAPPING",
                is_valid=True
            )

        return NormalizedFieldResult(
            field_id="premises_status",
            canonical_value=None,
            canonical_enum=None,
            display_label=None,
            raw_value=raw_value,
            raw_type=raw_type,
            canonical_type="string",
            status="SOURCE_MAPPING_ERROR",
            source=source_type,
            source_stage=source_stage,
            source_path=source_path,
            normalization_method="MAPPING_FAILED",
            is_valid=False,
            error_message=f"Unable to resolve premises status from '{raw_value}' ({raw_type})"
        )

    @classmethod
    def normalize_legal_constitution(
        cls,
        raw_value: Any,
        source_path: str = "profile.constitution",
        source_stage: str = "STAGE_1",
        source_type: str = "UPSTREAM_PROFILE"
    ) -> NormalizedFieldResult:
        raw_type = cls._get_raw_type(raw_value)

        if raw_value in (None, "", "UNKNOWN", "null", "None"):
            return NormalizedFieldResult(
                field_id="legal_constitution",
                canonical_value="PROPRIETORSHIP",
                canonical_enum="PROPRIETORSHIP",
                display_label="Sole Proprietorship",
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="DEFAULT_FALLBACK",
                is_valid=True
            )

        s_val = str(raw_value).strip()
        s_low = s_val.lower()

        for e in LegalConstitution:
            if e == LegalConstitution.UNKNOWN:
                continue
            if s_low == e.value.lower() or s_low == e.name.lower():
                return NormalizedFieldResult(
                    field_id="legal_constitution",
                    canonical_value=e.value,
                    canonical_enum=e.value,
                    display_label=LEGAL_CONSTITUTION_DISPLAY_LABELS[e],
                    raw_value=raw_value,
                    raw_type=raw_type,
                    canonical_type="string",
                    status="RESOLVED_PROFILE",
                    source=source_type,
                    source_stage=source_stage,
                    source_path=source_path,
                    normalization_method="CANONICAL_ENUM_MATCH",
                    is_valid=True
                )

        if cls._matches_any_term(s_low, ["llp", "limited liability partnership"]):
            e = LegalConstitution.LLP
        elif cls._matches_any_term(s_low, ["pvt", "private limited", "ltd", "pvt ltd"]):
            e = LegalConstitution.PRIVATE_LIMITED
        elif cls._matches_any_term(s_low, ["fpo", "farmer producer", "producer company"]):
            e = LegalConstitution.FPO
        elif cls._matches_any_term(s_low, ["cooperative", "co-operative", "society"]):
            e = LegalConstitution.COOPERATIVE
        elif cls._matches_any_term(s_low, ["one person", "opc"]):
            e = LegalConstitution.ONE_PERSON_COMPANY
        elif cls._matches_any_term(s_low, ["partner", "partnership"]):
            e = LegalConstitution.PARTNERSHIP
        elif cls._matches_any_term(s_low, ["proprietor", "proprietorship", "sole", "individual", "single owner"]):
            e = LegalConstitution.PROPRIETORSHIP
        else:
            e = None

        if e:
            return NormalizedFieldResult(
                field_id="legal_constitution",
                canonical_value=e.value,
                canonical_enum=e.value,
                display_label=LEGAL_CONSTITUTION_DISPLAY_LABELS[e],
                raw_value=raw_value,
                raw_type=raw_type,
                canonical_type="string",
                status="RESOLVED_PROFILE",
                source=source_type,
                source_stage=source_stage,
                source_path=source_path,
                normalization_method="TEXT_SYNONYM_MAPPING",
                is_valid=True
            )

        return NormalizedFieldResult(
            field_id="legal_constitution",
            canonical_value=None,
            canonical_enum=None,
            display_label=None,
            raw_value=raw_value,
            raw_type=raw_type,
            canonical_type="string",
            status="SOURCE_MAPPING_ERROR",
            source=source_type,
            source_stage=source_stage,
            source_path=source_path,
            normalization_method="MAPPING_FAILED",
            is_valid=False,
            error_message=f"Unable to resolve legal constitution from '{raw_value}' ({raw_type})"
        )

    @classmethod
    def normalize_promoter_field(
        cls,
        field_id: str,
        raw_value: Any,
        source_path: str = "",
        source_stage: str = "STAGE_10",
        source_type: str = "UPSTREAM_PROFILE"
    ) -> NormalizedFieldResult:
        """Dispatcher for single promoter field normalization."""
        fid = field_id.lower().replace("-", "_")
        if fid in ("promoter_education", "education", "education_level"):
            return cls.normalize_education(raw_value, source_path=source_path, source_stage=source_stage, source_type=source_type)
        if fid in ("promoter_social_category", "social_category", "caste_category", "beneficiary_category"):
            return cls.normalize_social_category(raw_value, source_path=source_path, source_stage=source_stage, source_type=source_type)
        if fid in ("promoter_edp_training_status", "edp_training_status", "training_status", "edp_status"):
            return cls.normalize_training_status(raw_value, source_path=source_path, source_stage=source_stage, source_type=source_type)
        if fid in ("promoter_experience_years", "experience_years", "relevant_sector_experience_years", "prior_experience_years"):
            return cls.normalize_experience_years(raw_value, source_path=source_path, source_stage=source_stage, source_type=source_type)
        if fid in ("premises_status", "operating_premises"):
            return cls.normalize_premises_status(raw_value, source_path=source_path, source_stage=source_stage, source_type=source_type)
        if fid in ("legal_constitution", "constitution"):
            return cls.normalize_legal_constitution(raw_value, source_path=source_path, source_stage=source_stage, source_type=source_type)

        # Default string normalization
        raw_type = cls._get_raw_type(raw_value)
        c_val = str(raw_value).strip() if raw_value not in (None, "") else None
        return NormalizedFieldResult(
            field_id=field_id,
            canonical_value=c_val,
            display_label=c_val,
            raw_value=raw_value,
            raw_type=raw_type,
            canonical_type="string",
            status="RESOLVED_PROFILE" if c_val else "UNKNOWN",
            source=source_type,
            source_stage=source_stage,
            source_path=source_path,
            normalization_method="GENERIC_STRING",
            is_valid=True
        )


profile_normalizer = ProfileNormalizer()
