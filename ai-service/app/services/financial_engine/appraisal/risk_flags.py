"""
Risk Flag definitions and helpers for M4 Banking Appraisal.
Deterministic, institutional risk categorization across 8 risk domains.
"""
from typing import Optional
from app.services.financial_engine.appraisal.appraisal_schema import (
    RiskFlag,
    RiskCategory,
    RiskSeverity,
    MetricSource
)
from app.services.financial_engine.appraisal.reason_codes import ReasonCode


def create_risk_flag(
    category: RiskCategory,
    severity: RiskSeverity,
    reason_code: ReasonCode,
    trigger: str,
    evidence: str,
    source: MetricSource,
    affected_metric: str,
    message: str,
    mitigation: Optional[str] = None
) -> RiskFlag:
    return RiskFlag(
        category=category,
        severity=severity,
        reason_code=reason_code,
        trigger=trigger,
        evidence=evidence,
        source=source,
        affected_metric=affected_metric,
        message=message,
        mitigation_if_determinable=mitigation
    )
