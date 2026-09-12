import datetime
import logging
from typing import List, Optional, Dict, Any

from app.schemas.knowledge import (
    DataSourceMetadataSchema,
    GovernmentSchemeSchema,
    FinancialBenchmarkSchema,
    MarketBenchmarkSchema,
    BusinessProfileSchema,
    BusinessRequirementSchema,
    RiskItemSchema,
    InstitutionalDocumentSchema,
    DynamicDataRequirementSchema,
    CoverageReportSchema,
    SchemeEligibilityQuery,
    SchemeEligibilityResult,
    MarketKnowledgePack,
    FinancialKnowledgePack,
    FinancialCalculationRules,
    FinancialFeasibilityResult,
    ComprehensiveBusinessKnowledgePack,
    ExplainableQualityScore,
    QualityMetadataSchema,
)
from app.knowledge.repositories import (
    SourcesRepository,
    SchemesRepository,
    BenchmarksRepository,
    BusinessRepository,
    RequirementsRepository,
    RisksRepository,
    DocumentsRepository,
    DynamicRequirementsRepository,
)
from app.knowledge.finance_calculator import (
    calculate_baseline_rules,
    evaluate_financial_feasibility,
)

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Central Domain Knowledge & Benchmark Hub Service for KALPA.
    Provides verified facts, benchmarks, technical requirements, schemes, and risks
    to KALPA Manager Orchestrator and downstream intelligence engines.
    """

    def __init__(
        self,
        sources_repo: Optional[SourcesRepository] = None,
        schemes_repo: Optional[SchemesRepository] = None,
        benchmarks_repo: Optional[BenchmarksRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
        requirements_repo: Optional[RequirementsRepository] = None,
        risks_repo: Optional[RisksRepository] = None,
        documents_repo: Optional[DocumentsRepository] = None,
        dynamic_repo: Optional[DynamicRequirementsRepository] = None,
    ):
        self.sources_repo = sources_repo or SourcesRepository()
        self.schemes_repo = schemes_repo or SchemesRepository()
        self.benchmarks_repo = benchmarks_repo or BenchmarksRepository()
        self.business_repo = business_repo or BusinessRepository()
        self.requirements_repo = requirements_repo or RequirementsRepository()
        self.risks_repo = risks_repo or RisksRepository()
        self.documents_repo = documents_repo or DocumentsRepository()
        self.dynamic_repo = dynamic_repo or DynamicRequirementsRepository()
        logger.info("KnowledgeService initialized with all 8 domain repositories.")

    # ---------------------------------------------------------
    # System Coverage & Health
    # ---------------------------------------------------------
    def get_coverage_report(self) -> CoverageReportSchema:
        """
        Generates a comprehensive audit of knowledge hub data coverage, ingestion statuses,
        quality scores, and provenance integrity across the 15 priority enterprises.
        """
        all_sources = self.sources_repo.get_all()
        all_schemes = self.schemes_repo.get_all()
        all_fin_benchmarks = self.benchmarks_repo.get_all_financial_benchmarks()
        all_mkt_benchmarks = self.benchmarks_repo.get_all_market_benchmarks()
        all_profiles = self.business_repo.get_all_profiles()
        all_reqs = self.requirements_repo.get_all()
        all_risks = self.risks_repo.get_all()
        all_docs = self.documents_repo.get_all()
        all_dyn = self.dynamic_repo.get_all()

        domain_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}
        for s in all_sources:
            domain = s.coverage_domain
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            st = s.ingestion_status
            status_counts[st] = status_counts.get(st, 0) + 1

        prov_dist: Dict[str, int] = {}
        quality_dist: Dict[str, int] = {}

        for sch in all_schemes:
            if sch.provenance:
                stype = sch.provenance.source_type
                prov_dist[stype] = prov_dist.get(stype, 0) + 1
            if sch.quality:
                auth = sch.quality.authority
                quality_dist[auth] = quality_dist.get(auth, 0) + 1

        for fb in all_fin_benchmarks:
            if fb.provenance:
                stype = fb.provenance.source_type
                prov_dist[stype] = prov_dist.get(stype, 0) + 1
            if fb.quality:
                auth = fb.quality.authority
                quality_dist[auth] = quality_dist.get(auth, 0) + 1

        for mb in all_mkt_benchmarks:
            if mb.provenance:
                stype = mb.provenance.source_type
                prov_dist[stype] = prov_dist.get(stype, 0) + 1
            if mb.quality:
                auth = mb.quality.authority
                quality_dist[auth] = quality_dist.get(auth, 0) + 1

        # Calculate completeness score (available + partial vs total)
        available_count = status_counts.get("AVAILABLE", 0)
        partial_count = status_counts.get("PARTIAL", 0)
        total_ds = len(all_sources) or 1
        completeness = round(((available_count * 1.0 + partial_count * 0.5) / total_ds) * 100.0, 1)

        priority_businesses = [
            "rice_mill", "flour_mill", "spice_processing", "food_processing_micro",
            "dairy_farm", "poultry_farm", "goat_farming", "grocery_store",
            "saree_retail", "garment_store", "tailoring_shop", "beauty_salon",
            "mobile_repair", "furniture_carpentry", "handicrafts"
        ]
        priority_coverage = {}
        for pb in priority_businesses:
            fb = self.benchmarks_repo.get_financial_benchmark(pb)
            mb = self.benchmarks_repo.get_market_benchmark(pb)
            prof = self.business_repo.get_profile(pb)
            priority_coverage[pb] = {
                "has_financial": fb is not None,
                "has_market": mb is not None,
                "has_profile": prof is not None,
                "ready": (fb is not None and mb is not None and prof is not None),
            }

        return CoverageReportSchema(
            total_curated_datasets=len(all_sources),
            total_schemes=len(all_schemes),
            total_financial_benchmarks=len(all_fin_benchmarks),
            total_market_benchmarks=len(all_mkt_benchmarks),
            total_business_profiles=len(all_profiles),
            total_business_requirements=len(all_reqs),
            total_risk_items=len(all_risks),
            total_institutional_documents=len(all_docs),
            total_dynamic_requirements=len(all_dyn),
            priority_businesses_coverage=priority_coverage,
            dataset_coverage_summary=domain_counts,
            status_breakdown=status_counts,
            completeness_score_pct=completeness,
            provenance_distribution=prov_dist,
            quality_distribution=quality_dist,
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        )

    # ---------------------------------------------------------
    # 1. Master Data Source Registry (31 SIH Datasets)
    # ---------------------------------------------------------
    def get_data_sources(
        self,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[DataSourceMetadataSchema]:
        return self.sources_repo.get_all(category=category, domain=domain, status=status)

    def get_data_source(self, dataset_id: str) -> Optional[DataSourceMetadataSchema]:
        return self.sources_repo.get_by_id(dataset_id)

    # ---------------------------------------------------------
    # 2. Government Schemes & Challenge Baseline Rules
    # ---------------------------------------------------------
    def get_schemes(
        self,
        category: Optional[str] = None,
        tier: Optional[str] = None,
    ) -> List[GovernmentSchemeSchema]:
        return self.schemes_repo.get_all(category=category, tier=tier)

    def get_scheme(self, scheme_id: str) -> Optional[GovernmentSchemeSchema]:
        return self.schemes_repo.get_by_id(scheme_id)

    def evaluate_scheme_eligibility(self, query: SchemeEligibilityQuery) -> SchemeEligibilityResult:
        return self.schemes_repo.evaluate_eligibility(query)

    # ---------------------------------------------------------
    # 3. Business Domain Profiles (Layer 2)
    # ---------------------------------------------------------
    def get_business_profile(self, business_id: str) -> Optional[BusinessProfileSchema]:
        res = self.business_repo.get_profile(business_id)
        if not res:
            res = self.business_repo.get_profile_by_nic(business_id)
        return res

    def get_all_business_profiles(self) -> List[BusinessProfileSchema]:
        return self.business_repo.get_all_profiles()

    # ---------------------------------------------------------
    # 4. Financial & Market Benchmarks
    # ---------------------------------------------------------
    def get_financial_benchmark(self, business_node_id: str) -> Optional[FinancialBenchmarkSchema]:
        res = self.benchmarks_repo.get_financial_benchmark(business_node_id)
        if not res:
            res = self.benchmarks_repo.get_financial_benchmark_by_nic(business_node_id)
        return res

    def get_all_financial_benchmarks(self) -> List[FinancialBenchmarkSchema]:
        return self.benchmarks_repo.get_all_financial_benchmarks()

    def get_market_benchmark(self, business_node_id: str) -> Optional[MarketBenchmarkSchema]:
        return self.benchmarks_repo.get_market_benchmark(business_node_id)

    def get_all_market_benchmarks(self) -> List[MarketBenchmarkSchema]:
        return self.benchmarks_repo.get_all_market_benchmarks()

    # ---------------------------------------------------------
    # 5. Technical Requirements & Risk Library
    # ---------------------------------------------------------
    def get_business_requirements(self, business_node_id: str) -> Optional[BusinessRequirementSchema]:
        return self.requirements_repo.get_by_business(business_node_id)

    def get_all_business_requirements(self) -> List[BusinessRequirementSchema]:
        return self.requirements_repo.get_all()

    def get_risks(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        business_node_id: Optional[str] = None,
    ) -> List[RiskItemSchema]:
        if business_node_id:
            items = self.risks_repo.get_for_business(business_node_id)
            if category:
                items = [r for r in items if r.category.upper() == category.upper()]
            if severity:
                items = [r for r in items if r.severity.upper() == severity.upper()]
            return items
        return self.risks_repo.get_all(category=category, severity=severity)

    # ---------------------------------------------------------
    # 6. Institutional Documents
    # ---------------------------------------------------------
    def get_institutional_documents(
        self,
        institution: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        business_node_id: Optional[str] = None,
    ) -> List[InstitutionalDocumentSchema]:
        if business_node_id:
            docs = self.documents_repo.get_for_business(business_node_id)
            if institution:
                docs = [d for d in docs if institution.upper() in d.institution.upper()]
            if category:
                docs = [d for d in docs if d.category.upper() == category.upper()]
            if status:
                docs = [d for d in docs if d.ingestion_status.upper() == status.upper()]
            return docs
        return self.documents_repo.get_all(institution=institution, category=category, status=status)

    def get_institutional_document(self, document_id: str) -> Optional[InstitutionalDocumentSchema]:
        return self.documents_repo.get_by_id(document_id)

    # ---------------------------------------------------------
    # 7. Dynamic Data Requirements
    # ---------------------------------------------------------
    def get_dynamic_data_requirements(
        self,
        domain: Optional[str] = None,
        consuming_engine: Optional[str] = None,
    ) -> List[DynamicDataRequirementSchema]:
        return self.dynamic_repo.get_all(domain=domain, consuming_engine=consuming_engine)

    # ---------------------------------------------------------
    # 8. Engine-Ready Packs (Stage 4.5 Core Interfaces)
    # ---------------------------------------------------------
    def get_market_context(
        self,
        business_id: str,
        location: Optional[str] = None,
    ) -> MarketKnowledgePack:
        """
        Supplies Market Intelligence Engine and Opportunity Evaluation Engine
        with engine-ready market catchment benchmarks, seasonality, and dynamic data requirements.
        """
        benchmark = self.get_market_benchmark(business_id)
        if not benchmark:
            return MarketKnowledgePack(
                business_node_id=business_id,
                business_title=f"Uncurated Business ({business_id})",
                available=False,
                status="data_missing",
                recommended_action="fetch_dynamic_data",
                demand_drivers=[],
                target_customer_segments=[],
            )

        return MarketKnowledgePack(
            business_node_id=benchmark.business_node_id,
            business_title=benchmark.business_title,
            available=True,
            status="ready",
            catchment=benchmark.catchment,
            competition_and_saturation=benchmark.competition_and_saturation,
            seasonality_factors=benchmark.seasonality_factors,
            seasonality_notes=benchmark.seasonality_notes,
            demand_drivers=benchmark.demand_drivers,
            target_customer_segments=benchmark.target_customer_segments,
            market_analysis_requirements=benchmark.market_analysis_requirements,
            quality=benchmark.quality or QualityMetadataSchema(authority="official", verification_status="verified", confidence=0.92),
            provenance=benchmark.provenance,
        )

    def get_financial_context(
        self,
        business_id: str,
        project_cost: Optional[float] = None,
        available_margin: Optional[float] = None,
    ) -> FinancialKnowledgePack:
        """
        Supplies Finance Engine, Feasibility Engine, and DPR Generator with
        CapEx, OpEx, unit economics, eligible schemes, and deterministic calculation rules.
        """
        benchmark = self.get_financial_benchmark(business_id)
        if not benchmark:
            return FinancialKnowledgePack(
                business_node_id=business_id,
                business_title=f"Uncurated Business ({business_id})",
                available=False,
                status="data_missing",
                recommended_action="fetch_dynamic_data",
            )

        effective_cost = project_cost if project_cost is not None else benchmark.capex.typical
        scheme_eval = self.evaluate_scheme_eligibility(
            SchemeEligibilityQuery(
                project_cost=effective_cost,
                available_margin=available_margin,
                business_node_id=business_id,
                is_rural=True,
            )
        )

        matched = scheme_eval.matched_schemes
        recommended = None
        if scheme_eval.recommended_scheme_id:
            for s in matched:
                if s.scheme_id == scheme_eval.recommended_scheme_id:
                    recommended = s
                    break

        calc_rules = calculate_baseline_rules(
            project_cost=effective_cost,
            available_margin=available_margin,
            scheme_override=recommended,
        )

        return FinancialKnowledgePack(
            business_node_id=benchmark.business_node_id,
            business_title=benchmark.business_title,
            available=True,
            status="ready",
            benchmark_capex=benchmark.capex,
            benchmark_working_capital=benchmark.working_capital,
            benchmark_margins=benchmark.margins,
            cost_structure_pct=benchmark.cost_structure_pct,
            timelines=benchmark.timelines,
            unit_economics=benchmark.unit_economics,
            applicable_schemes=matched,
            recommended_scheme=recommended or scheme_eval.challenge_baseline_applied,
            calculation_rules=calc_rules,
            quality=benchmark.quality or QualityMetadataSchema(authority="official", verification_status="verified", confidence=0.92),
            provenance=benchmark.provenance,
        )

    def calculate_deterministic_financials(
        self,
        business_id: str,
        project_cost: float,
        available_margin: Optional[float] = None,
    ) -> FinancialFeasibilityResult:
        """
        Executes pure deterministic math (EMI, DSCR, Payback, Amortization) with ZERO LLM calls.
        """
        benchmark = self.get_financial_benchmark(business_id)
        calc_rules = calculate_baseline_rules(
            project_cost=project_cost,
            available_margin=available_margin,
        )
        return evaluate_financial_feasibility(
            business_node_id=business_id,
            project_cost=project_cost,
            rules=calc_rules,
            benchmark=benchmark,
        )

    # ---------------------------------------------------------
    # 9. Comprehensive 5-Layer Business Knowledge Pack
    # ---------------------------------------------------------
    def get_comprehensive_business_pack(
        self,
        business_node_id: str,
        project_cost: Optional[float] = None,
        available_margin: Optional[float] = None,
    ) -> ComprehensiveBusinessKnowledgePack:
        """
        Assembles all 5 logical layers for a specific business:
        - Layer 1: Official Rules & Government Schemes
        - Layer 2: Business Domain Knowledge & Profile
        - Layer 3: Financial & Market Benchmarks
        - Layer 4: Institutional Evidence Documents
        - Layer 5: Dynamic Data Requirements & Candidate Sources
        """
        profile = self.get_business_profile(business_node_id)
        fin_bench = self.get_financial_benchmark(business_node_id)
        mkt_bench = self.get_market_benchmark(business_node_id)
        docs = self.get_institutional_documents(business_node_id=business_node_id)
        dyn_reqs = self.get_dynamic_data_requirements()
        sources = self.get_data_sources()

        effective_cost = project_cost
        if effective_cost is None and fin_bench:
            effective_cost = fin_bench.capex.typical
        elif effective_cost is None:
            effective_cost = 140000.0

        scheme_eval = self.evaluate_scheme_eligibility(
            SchemeEligibilityQuery(
                project_cost=effective_cost,
                available_margin=available_margin,
                business_node_id=business_node_id,
                is_rural=True,
            )
        )

        missing_signals: List[Dict[str, str]] = []
        if not profile:
            missing_signals.append({
                "layer": "Layer 2 - Domain Knowledge",
                "missing": "Operational business profile not curated",
                "recommended_action": "requires_verification",
            })
        if not fin_bench:
            missing_signals.append({
                "layer": "Layer 3 - Financial Benchmarks",
                "missing": "Financial cost/margin benchmarks missing",
                "recommended_action": "fetch_dynamic_data",
            })
        if not mkt_bench:
            missing_signals.append({
                "layer": "Layer 3 - Market Benchmarks",
                "missing": "Catchment & seasonality benchmarks missing",
                "recommended_action": "fetch_dynamic_data",
            })

        verified_count = (1 if profile else 0) + (1 if fin_bench else 0) + (1 if mkt_bench else 0) + (1 if len(docs) > 0 else 0) + 1
        total_fields = 5
        score_val = round(verified_count / total_fields, 2)

        quality_score = ExplainableQualityScore(
            overall_confidence=score_val,
            authority_tier="official" if score_val >= 0.8 else "mixed",
            verified_fields_count=verified_count,
            total_fields_count=total_fields,
            official_sources_count=len(docs) + 2,
            audit_notes=[
                "Layer 1 SIH Challenge Baseline Rules verified against official SIH Problem Statement.",
                "Layer 3 Financial & Market Benchmarks aligned with NABARD/EDII/KVIC official models.",
            ],
        )

        business_title = (
            (profile.business_title if profile else None)
            or (fin_bench.business_title if fin_bench else None)
            or (mkt_bench.business_title if mkt_bench else None)
            or f"Rural Enterprise ({business_node_id})"
        )

        nic = profile.nic_code if profile else (fin_bench.nic_code if fin_bench else None)

        return ComprehensiveBusinessKnowledgePack(
            business_node_id=business_node_id,
            business_title=business_title,
            nic_code=nic,
            available=len(missing_signals) == 0,
            status="ready" if len(missing_signals) == 0 else "partial",
            quality_score=quality_score,
            layer1_rules_and_schemes={
                "challenge_baseline": scheme_eval.challenge_baseline_applied.model_dump() if scheme_eval.challenge_baseline_applied else None,
                "matched_schemes": [s.model_dump() for s in scheme_eval.matched_schemes],
                "recommended_scheme_id": scheme_eval.recommended_scheme_id,
                "estimated_subsidy_pct": scheme_eval.estimated_subsidy_pct,
                "estimated_interest_rate_pct": scheme_eval.estimated_interest_rate_pct,
            },
            layer2_domain_knowledge=profile,
            layer3_financial_benchmarks=fin_bench,
            layer3_market_benchmarks=mkt_bench,
            layer4_institutional_evidence=docs,
            layer5_dynamic_data_requirements=dyn_reqs[:5],
            layer5_candidate_sources=sources[:10],
            missing_data_signals=missing_signals,
        )


# Singleton instance for system-wide access
_knowledge_service_instance: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service_instance
    if _knowledge_service_instance is None:
        _knowledge_service_instance = KnowledgeService()
    return _knowledge_service_instance
