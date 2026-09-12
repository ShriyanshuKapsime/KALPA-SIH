import os
import json
import logging
from typing import List, Optional, Dict, Any
from app.schemas.knowledge import (
    GovernmentSchemeSchema,
    SchemeEligibilityQuery,
    SchemeEligibilityResult,
)

logger = logging.getLogger(__name__)

CURATED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "curated")


class SchemesRepository:
    """
    Repository for official government schemes and SIH challenge baseline rules with explicit provenance.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or os.path.join(CURATED_DATA_DIR, "schemes", "government_schemes.json")
        self._schemes: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._schemes = json.load(f)
                logger.info(f"Loaded {len(self._schemes)} curated government schemes from {self.file_path}")
            else:
                logger.warning(f"Government schemes data not found at {self.file_path}")
                self._schemes = []
        except Exception as e:
            logger.error(f"Failed to load government schemes: {e}")
            self._schemes = []

    def get_all(self, category: Optional[str] = None, tier: Optional[str] = None) -> List[GovernmentSchemeSchema]:
        filtered = self._schemes
        if category:
            filtered = [s for s in filtered if s.get("category", "").upper() == category.upper()]
        if tier:
            filtered = [s for s in filtered if s.get("scheme_tier", "").upper() == tier.upper()]
        return [GovernmentSchemeSchema(**s) for s in filtered]

    def get_by_id(self, scheme_id: str) -> Optional[GovernmentSchemeSchema]:
        for s in self._schemes:
            if s.get("scheme_id") == scheme_id:
                return GovernmentSchemeSchema(**s)
        return None

    def get_baseline_rule(self, project_cost: float) -> Optional[GovernmentSchemeSchema]:
        """
        Challenge Baseline Rules specified in SIH Problem Statement:
        - Project Cost <= 1.40 Lakhs: Micro finance support (6.5% interest, max loan 90% up to 1.25L, 3yr tenure, 3mo moratorium)
        - Project Cost > 1.40 Lakhs (up to 50L): Term loan (8.0% interest, max loan 90% up to 45L, 7yr tenure, 6mo moratorium)
        """
        if project_cost <= 140000.0:
            return self.get_by_id("challenge_baseline_micro_finance")
        else:
            return self.get_by_id("challenge_baseline_term_loan")

    def evaluate_eligibility(self, query: SchemeEligibilityQuery) -> SchemeEligibilityResult:
        """
        Evaluates project parameters against curated schemes and challenge baseline rules.
        """
        cost = query.project_cost
        matched: List[GovernmentSchemeSchema] = []
        baseline_rule = self.get_baseline_rule(cost)

        for s_data in self._schemes:
            s = GovernmentSchemeSchema(**s_data)
            crit = s.eligibility_criteria

            # Project cost range checks
            min_cost = crit.min_project_cost or 0.0
            max_cost = crit.max_project_cost or float("inf")
            if not (min_cost <= cost <= max_cost):
                continue

            # Rural filter check
            if crit.rural_only and not query.is_rural:
                continue

            # Gender / Caste filter check
            if crit.gender_preference == "FEMALE_OR_SC_ST":
                gender = (query.gender or "").upper()
                caste = (query.caste or "").upper()
                if gender != "FEMALE" and caste not in ["SC", "ST"]:
                    continue

            matched.append(s)

        # Determine recommended scheme
        recommended_id = None
        max_sub = 0.0
        est_interest = 8.0

        if baseline_rule:
            est_interest = baseline_rule.financial_terms.interest_rate_pct or 8.0

        for m in matched:
            sub = m.financial_terms.subsidy_pct or 0.0
            if sub > max_sub:
                max_sub = sub
                recommended_id = m.scheme_id
                if m.financial_terms.interest_rate_pct:
                    est_interest = m.financial_terms.interest_rate_pct

        if not recommended_id and baseline_rule:
            recommended_id = baseline_rule.scheme_id

        return SchemeEligibilityResult(
            matched_schemes=matched,
            challenge_baseline_applied=baseline_rule,
            recommended_scheme_id=recommended_id,
            estimated_subsidy_pct=max_sub,
            estimated_interest_rate_pct=est_interest,
            total_matched=len(matched),
        )
