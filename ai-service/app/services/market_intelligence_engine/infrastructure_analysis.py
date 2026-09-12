"""
Infrastructure Analysis Layer for Stage 6 Market Intelligence Engine.
Evaluates business-specific utility, transport, and facility requirements.
Explicitly identifies data gaps when evidence is missing, never falsely assuming availability.
"""
from typing import Dict, Any, List, Optional
from app.services.market_intelligence_engine.schemas import (
    InfrastructureReadiness,
    InfrastructureAnalysisResult,
    CleanedInfrastructureRequirement,
    DataStatus
)


class InfrastructureAnalysisService:
    def analyze_infrastructure(
        self,
        cleaned_requirements: List[CleanedInfrastructureRequirement],
        data_status: DataStatus,
        benchmarks: Dict[str, Any]
    ) -> InfrastructureAnalysisResult:
        """
        Executes deterministic infrastructure readiness analysis.
        """
        expected_reqs = benchmarks.get("infrastructure_requirements", [
            "Road freight access",
            "Continuous grid electricity",
            "Clean water source"
        ])

        total_reqs = len(cleaned_requirements) if cleaned_requirements else len(expected_reqs)
        satisfied_count = 0
        critical_gaps: List[Dict[str, Any]] = []

        if data_status == DataStatus.MISSING or not cleaned_requirements or all(r.status == "UNKNOWN" for r in cleaned_requirements):
            # Evidence gap handling
            readiness = InfrastructureReadiness.UNKNOWN_DATA_GAP
            readiness_score = 0.50
            confidence = 0.30

            for req_name in expected_reqs:
                critical_gaps.append({
                    "requirement": req_name,
                    "status": "DATA_GAP",
                    "severity": "HIGH",
                    "description": f"Mandatory infrastructure parameter '{req_name}' was not retrieved in Stage 5 dataset; requires ground verification."
                })

            return InfrastructureAnalysisResult(
                readiness=readiness,
                readiness_score=readiness_score,
                requirements=cleaned_requirements,
                satisfied_requirements_count=0,
                total_requirements_count=total_reqs,
                critical_gaps=critical_gaps,
                confidence=confidence
            )

        # Evaluate provided evidence
        for req in cleaned_requirements:
            if req.status == "AVAILABLE":
                satisfied_count += 1
            elif req.status in ["UNAVAILABLE", "UNKNOWN"]:
                critical_gaps.append({
                    "requirement": req.requirement,
                    "status": req.status,
                    "severity": "HIGH" if req.impact == "HIGH" else "MEDIUM",
                    "description": f"Infrastructure requirement '{req.requirement}' status is {req.status}."
                })

        readiness_score = round(satisfied_count / max(1, total_reqs), 2)

        if readiness_score >= 0.80:
            readiness = InfrastructureReadiness.AVAILABLE
            confidence = 0.90
        elif readiness_score >= 0.40:
            readiness = InfrastructureReadiness.PARTIAL
            confidence = 0.75
        else:
            readiness = InfrastructureReadiness.UNAVAILABLE
            confidence = 0.80

        return InfrastructureAnalysisResult(
            readiness=readiness,
            readiness_score=readiness_score,
            requirements=cleaned_requirements,
            satisfied_requirements_count=satisfied_count,
            total_requirements_count=total_reqs,
            critical_gaps=critical_gaps,
            confidence=confidence
        )


infrastructure_service = InfrastructureAnalysisService()
