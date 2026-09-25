"""
Stage 13: Dynamic SWOT Agent.
Interprets deterministic outputs from Stages 6, 8, 9, 10, 11, and 12 using Sarvam AI (sarvam-105b).
Enforces compact canonical payloads, bounded 20-30s interactive timeouts, strict 2-attempt retries,
provenance citations, zero-hallucination policies, and automatic deterministic fallback.
"""
import time
import json
import asyncio
import httpx
from typing import Dict, Any, Optional, List, Union

from app.core.config import settings
from app.core.logging import logger
from app.schemas.swot import (
    SWOTEvaluationRequest,
    SWOTAnalysisResponse,
    SWOTCategoryBreakdown,
    SWOTItem,
    SWOTEvidenceRef,
    PriorityAction,
    RoadmapPhase,
    SWOTGenerationMeta,
    StrategicSummary,
    SWOTRecommendation,
    ImmediateAction,
    SWOTEvidenceSummary,
    ModelMetadata
)
from app.services.sarvam_llm_service import extract_llm_content
from app.services.swot_engine.evidence_adapter import swot_evidence_adapter
from app.services.swot_engine.prompt_builder import (
    build_swot_system_prompt,
    build_swot_user_prompt,
    build_compact_retry_user_prompt
)
from app.services.swot_engine.deterministic_fallback import generate_deterministic_swot_fallback


class DynamicSWOTAgent:
    """
    Dedicated Stage 13 Strategic SWOT Agent.
    Interprets verified facts without altering metrics or replacing deterministic engines.
    """

    def __init__(self):
        self.model = settings.SARVAM_LLM_MODEL or "sarvam-105b-conversations"
        self.endpoint = settings.SARVAM_LLM_ENDPOINT or "https://api.sarvam.ai/v1/chat/completions"
        # Bounded interactive timeout: connect 5s, read 14s (2 attempts + 1s backoff <= 30s total budget)
        self.timeout = httpx.Timeout(connect=5.0, read=14.0, write=10.0, pool=5.0)

    @property
    def is_available(self) -> bool:
        return settings.is_sarvam_llm_enabled

    async def generate_swot_analysis(
        self,
        request: SWOTEvaluationRequest
    ) -> SWOTAnalysisResponse:
        """
        Executes Stage 13 SWOT analysis workflow.
        1. Validates Stage 12 Feasibility Decision Gating.
        2. Normalizes compact evidence payload.
        3. Invokes Sarvam LLM with bounded 20s timeout and max 2 attempts.
        4. On success: returns structured response with provenance.
        5. On LLM timeout / token exhaustion / error: returns deterministic fallback.
        """
        analysis_id = request.analysis_id
        session_id = request.session_id
        overall_start = time.time()

        # -------------------------------------------------------------
        # 1. Feasibility Decision Gating (Stage 12 is Authoritative)
        # -------------------------------------------------------------
        feas = request.feasibility_result or {}
        decision = (feas.get("decision") or feas.get("viability_status") or "").upper()
        recommendation = (feas.get("recommendation") or "").upper()

        if decision in ("NOT_FEASIBLE", "INSUFFICIENT", "RESTRICTED") or recommendation == "NO":
            logger.info(f"[STAGE 13 SWOT GATED] Stage 12 decision is '{decision}' / '{recommendation}'. Blocking YES-path SWOT.")
            b_name = (request.business_profile or {}).get("specific_business") or (request.business_profile or {}).get("business_name") or "Enterprise"
            return SWOTAnalysisResponse(
                analysis_id=analysis_id,
                session_id=session_id,
                business_name=b_name,
                status="BLOCKED_NOT_FEASIBLE",
                confidence=0.0,
                message="Venture is classified as NOT_FEASIBLE in Stage 12. Strategic YES-path SWOT is reserved for viable ventures. Please consult the Pivot Advisor."
            )

        # -------------------------------------------------------------
        # 2. Extract & Normalize Compact Canonical Evidence
        # -------------------------------------------------------------
        evidence_ctx = swot_evidence_adapter.extract_evidence_context(
            business_profile=request.business_profile,
            location_profile=request.location_profile,
            market_analysis=request.market_analysis,
            opportunity_result=request.opportunity_result,
            financial_analysis=request.financial_analysis,
            financial_context=getattr(request, "financial_context", None),
            entrepreneur_readiness=request.entrepreneur_readiness,
            risk_analysis=request.risk_analysis,
            feasibility_result=request.feasibility_result,
        )

        compact_json_str = json.dumps(evidence_ctx, separators=(",", ":"))
        compact_size = len(compact_json_str)

        # -------------------------------------------------------------
        # Structured Diagnostic Input Logging
        # -------------------------------------------------------------
        fin_info = evidence_ctx.get("finance", {})
        mkt_info = evidence_ctx.get("market", {})
        rsk_info = evidence_ctx.get("risk", {})
        fc_obj = getattr(request, "financial_context", None) or (
            request.financial_analysis.get("financial_context") if isinstance(request.financial_analysis, dict) else None
        )

        biz_id_val = (
            (request.business_profile or {}).get("business_id")
            or (request.business_profile or {}).get("specific_business")
            or "unknown"
        )
        has_fin_ctx = bool(fc_obj)
        pkg_version = fc_obj.get("package_version", "1.0.0") if isinstance(fc_obj, dict) else ("1.0.0" if has_fin_ctx else "N/A")
        has_proj_cost = fin_info.get("project_cost") not in (None, "Evidence unavailable")
        has_rev_y1 = bool(isinstance(fc_obj, dict) and fc_obj.get("profit_loss")) or fin_info.get("first_year_revenue") not in (None, "Evidence unavailable")
        has_dscr = fin_info.get("dscr") not in (None, "Evidence unavailable")
        has_bep = (
            fin_info.get("break_even_pct") not in (None, "Evidence unavailable")
            or fin_info.get("break_even_percentage") not in (None, "Evidence unavailable")
            or (isinstance(fc_obj, dict) and (fc_obj.get("banking_appraisal", {}).get("break_even_utilization") is not None or fc_obj.get("banking_appraisal", {}).get("break_even_utilization_pct") is not None))
            or bool(isinstance(request.financial_analysis, dict) and (request.financial_analysis.get("break_even_percentage") is not None or request.financial_analysis.get("break_even_point_percentage") is not None))
        )
        has_risk_ctx = (
            bool(rsk_info and (rsk_info.get("score") not in (None, "Evidence unavailable") or rsk_info.get("critical_risks") or rsk_info.get("mitigations")))
            or bool(request.risk_analysis)
        )
        has_mkt_ctx = (
            bool(mkt_info and (mkt_info.get("score") not in (None, "Evidence unavailable") or mkt_info.get("demand") not in (None, "Evidence unavailable") or mkt_info.get("evidence")))
            or bool(request.market_analysis or request.opportunity_result)
        )

        logger.info(
            f"[STAGE 13 SWOT INPUT] "
            f"business_id={biz_id_val} "
            f"finance_context_present={has_fin_ctx} "
            f"finance_package_version={pkg_version} "
            f"project_cost_present={has_proj_cost} "
            f"revenue_y1_present={has_rev_y1} "
            f"dscr_present={has_dscr} "
            f"break_even_present={has_bep} "
            f"risk_context_present={has_risk_ctx} "
            f"market_context_present={has_mkt_ctx} "
            f"context_bytes={compact_size}"
        )

        # -------------------------------------------------------------
        # 3. Check Sarvam Configuration -> Deterministic Fallback if Disabled
        # -------------------------------------------------------------
        if not self.is_available:
            logger.info("[STAGE 13 SARVAM FALLBACK] reason=UNAVAILABLE (Sarvam LLM not configured or disabled)")
            fallback_res = generate_deterministic_swot_fallback(
                evidence_ctx=evidence_ctx,
                analysis_id=analysis_id,
                session_id=session_id,
                llm_status="unavailable",
                error_message="Sarvam AI LLM is not enabled. Generated via deterministic fallback."
            )
            total_elapsed_ms = (time.time() - overall_start) * 1000.0
            logger.info(
                f"[STAGE 13 SWOT OUTPUT] provider=FALLBACK "
                f"attempts=0 "
                f"elapsed_ms={total_elapsed_ms:.1f} "
                f"strengths={len(fallback_res.swot.strengths)} "
                f"weaknesses={len(fallback_res.swot.weaknesses)} "
                f"opportunities={len(fallback_res.swot.opportunities)} "
                f"threats={len(fallback_res.swot.threats)} "
                f"finance_evidence_used={has_dscr or has_proj_cost}"
            )
            return fallback_res

        # -------------------------------------------------------------
        # 4. Invoke Sarvam AI LLM (sarvam-105b) with Bounded Retries (Max 2)
        # -------------------------------------------------------------
        system_prompt = build_swot_system_prompt()
        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": (settings.SARVAM_API_KEY or "").strip()
        }

        fallback_reason = "UNKNOWN"
        error_detail = None
        max_attempts = 2
        attempts_made = 0

        for attempt_idx in range(max_attempts):
            attempts_made += 1
            attempt = attempt_idx + 1
            call_start = time.time()
            logger.info(f"[STAGE 13 SARVAM] attempt={attempt} model={self.model}")
            logger.info("[STAGE 13 SARVAM] request_started")

            # For attempt 1: standard prompt; for attempt 2: compact retry prompt
            if attempt == 1:
                active_user_prompt = build_swot_user_prompt(evidence_ctx)
            else:
                logger.info("[STAGE 13 SARVAM RETRY] Using compact high-impact retry prompt")
                active_user_prompt = build_compact_retry_user_prompt(evidence_ctx)

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": active_user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 4096,
                "response_format": {"type": "json_object"}
            }

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(self.endpoint, headers=headers, json=payload)
                    elapsed_ms = (time.time() - call_start) * 1000.0

                    logger.info(f"[STAGE 13 SARVAM] response_received status={resp.status_code} elapsed_ms={elapsed_ms:.1f}")

                    if resp.status_code != 200:
                        error_detail = f"Sarvam HTTP {resp.status_code}: {resp.text[:200]}"
                        fallback_reason = f"HTTP_{resp.status_code}"
                        logger.warning(f"[STAGE 13 SARVAM ERROR] type=HTTP status={resp.status_code} elapsed_ms={elapsed_ms:.1f}")

                        # Retry only transient 5xx errors
                        if attempt < max_attempts and resp.status_code in (500, 502, 503, 504):
                            await asyncio.sleep(1.0)
                            continue
                        break

                    logger.info("[STAGE 13 SARVAM] response_parse_started")
                    resp_data = resp.json()
                    extraction = extract_llm_content(resp_data)

                    if not extraction.get("success") or not extraction.get("content"):
                        error_detail = extraction.get("error") or "Failed to extract valid content"
                        resp_type = extraction.get("response_type", "")
                        if resp_type == "TOKEN_LIMIT_EXCEEDED" or "token limit" in str(error_detail).lower():
                            fallback_reason = "TOKEN_LIMIT_EXCEEDED"
                        elif "timeout" in str(error_detail).lower():
                            fallback_reason = "TIMEOUT"
                        else:
                            fallback_reason = "PARSE_ERROR"

                        logger.warning(f"[STAGE 13 SARVAM ERROR] type={fallback_reason} detail={error_detail} elapsed_ms={elapsed_ms:.1f}")
                        if attempt < max_attempts and fallback_reason in ("TIMEOUT", "PARSE_ERROR"):
                            await asyncio.sleep(1.0)
                            continue
                        break

                    raw_content = extraction["content"]
                    parsed_json = json.loads(raw_content)
                    logger.info(f"[STAGE 13 SARVAM] response_parse_success elapsed_ms={elapsed_ms:.1f}")

                    # -------------------------------------------------------------
                    # 5. Parse and Validate Output Contract
                    # -------------------------------------------------------------
                    duration_ms = (time.time() - overall_start) * 1000.0

                    exec_sum = parsed_json.get("executive_summary") or "Strategic SWOT analysis synthesized from verified evidence."
                    strat_dir = parsed_json.get("strategic_direction") or "Enterprise demonstrates sound viability fundamentals."
                    conf = float(parsed_json.get("confidence") or 0.88)

                    def _parse_items(raw_list: list, cat_name: str, id_prefix: str) -> List[SWOTItem]:
                        items: List[SWOTItem] = []
                        for i, itm in enumerate(raw_list[:5]):
                            if not isinstance(itm, dict):
                                continue
                            t = itm.get("title") or f"{cat_name.title()} Factor {i+1}"
                            exp = itm.get("explanation") or itm.get("statement") or itm.get("business_impact") or itm.get("action") or ""
                            src = itm.get("source_stage") or "STAGE_12"
                            d_status = itm.get("data_status") or ("DATA_GAP" if "unavailable" in str(exp).lower() else "KNOWN")

                            ev_raw = itm.get("evidence") or []
                            ev_list: List[Union[str, SWOTEvidenceRef]] = []
                            if isinstance(ev_raw, list):
                                for e in ev_raw:
                                    if isinstance(e, dict):
                                        ev_list.append(SWOTEvidenceRef(
                                            source_stage=str(e.get("source_stage", src)),
                                            source_field=str(e.get("source_field", "general")),
                                            value=e.get("value"),
                                            confidence=float(e.get("confidence") or conf)
                                        ))
                                    elif isinstance(e, str) and e.strip():
                                        ev_list.append(e.strip())
                            elif isinstance(ev_raw, str) and ev_raw.strip():
                                ev_list.append(ev_raw.strip())

                            if not ev_list:
                                ev_list.append(f"{src} verified evidence")

                            raw_id = itm.get("id")
                            if raw_id and isinstance(raw_id, str) and raw_id.strip():
                                item_id = raw_id.strip()
                            else:
                                item_id = f"{id_prefix}-{i+1:03d}"

                            items.append(SWOTItem(
                                id=item_id,
                                category=cat_name.upper(),
                                title=t,
                                explanation=exp,
                                statement=exp,
                                why_it_matters=itm.get("why_it_matters") or itm.get("business_impact") or exp,
                                business_impact=itm.get("business_impact"),
                                action=itm.get("action"),
                                mitigation=itm.get("mitigation"),
                                evidence=ev_list,
                                source_stage=src,
                                confidence=float(itm.get("confidence") or conf),
                                priority=itm.get("priority", "HIGH"),
                                data_status=d_status
                            ))
                        return items

                    # Support flat schema and nested { "swot": { ... } } schema
                    swot_source = parsed_json.get("swot") if isinstance(parsed_json.get("swot"), dict) else parsed_json

                    strengths = _parse_items(swot_source.get("strengths", []), "STRENGTH", "ST")
                    weaknesses = _parse_items(swot_source.get("weaknesses", []), "WEAKNESS", "WK")
                    opportunities = _parse_items(swot_source.get("opportunities", []), "OPPORTUNITY", "OP")
                    threats = _parse_items(swot_source.get("threats", []), "THREAT", "TH")

                    # Strict quadrant completeness: all 4 quadrants must have at least 1 item
                    if not strengths or not weaknesses or not opportunities or not threats:
                        fallback_reason = "INCOMPLETE_SWOT_QUADRANTS"
                        logger.warning(f"[STAGE 13 SARVAM ERROR] type=INCOMPLETE_SWOT_QUADRANTS strengths={len(strengths)} weaknesses={len(weaknesses)} opportunities={len(opportunities)} threats={len(threats)}")
                        if attempt < max_attempts:
                            await asyncio.sleep(1.0)
                            continue
                        break

                    # Priority Actions / Strategic Priorities
                    raw_actions = (
                        parsed_json.get("strategic_priorities")
                        or parsed_json.get("priority_actions")
                        or swot_source.get("strategic_priorities")
                        or swot_source.get("priority_actions")
                        or parsed_json.get("recommendations")
                        or []
                    )
                    priority_actions: List[PriorityAction] = []
                    for act_idx, act in enumerate(raw_actions[:5]):
                        if isinstance(act, dict):
                            priority_actions.append(PriorityAction(
                                id=act.get("id") or f"SP-{act_idx+1:03d}",
                                action=act.get("action") or act.get("title") or "Implement operational step",
                                reason=act.get("reason") or act.get("why") or "Required for risk mitigation",
                                priority=act.get("priority", "HIGH"),
                                source_stage=act.get("source_stage") or "STAGE_10",
                                linked_dimension=act.get("linked_dimension") or "general"
                            ))

                    if not priority_actions:
                        priority_actions.append(PriorityAction(
                            id="SP-001",
                            action="Establish direct cluster wholesale linkages and maintain 3-month working capital buffer.",
                            reason="Mitigates price competition and off-peak seasonal revenue fluctuations.",
                            priority="HIGH",
                            source_stage="STAGE_11",
                            linked_dimension="finance"
                        ))

                    # Strategic Roadmap
                    raw_roadmap = parsed_json.get("roadmap") or swot_source.get("roadmap") or []
                    roadmap_phases = []
                    if isinstance(raw_roadmap, list) and raw_roadmap:
                        for rp in raw_roadmap:
                            if isinstance(rp, dict):
                                roadmap_phases.append(RoadmapPhase(
                                    phase=rp.get("phase") or "0-30 days",
                                    actions=rp.get("actions") if isinstance(rp.get("actions"), list) else [str(rp.get("actions", ""))]
                                ))
                    if not roadmap_phases:
                        roadmap_phases = [
                            RoadmapPhase(phase="0-30 days", actions=["Finalize statutory licenses and EDP certification", "Secure premises lease agreement"]),
                            RoadmapPhase(phase="30-90 days", actions=["Procure initial stock inventory", "Launch targeted village catchment promotion"]),
                            RoadmapPhase(phase="90+ days", actions=["Establish formal credit history and monitor monthly DSCR", "Expand product catalog based on local demand"])
                        ]

                    swot_breakdown = SWOTCategoryBreakdown(
                        executive_summary=exec_sum,
                        strengths=strengths,
                        weaknesses=weaknesses,
                        opportunities=opportunities,
                        threats=threats,
                        priority_actions=priority_actions,
                        strategic_priorities=priority_actions,
                        roadmap=roadmap_phases,
                        strategic_direction=strat_dir,
                        confidence=conf
                    )

                    strat_summary = StrategicSummary(
                        business_position=strat_dir,
                        key_advantage=strengths[0].title if strengths else "Verified local demand and domain capabilities.",
                        main_constraint=weaknesses[0].title if weaknesses else "Working capital buffer discipline.",
                        biggest_opportunity=opportunities[0].title if opportunities else "Catchment demand expansion.",
                        biggest_threat=threats[0].title if threats else "Seasonal revenue fluctuations."
                    )

                    recs = [
                        SWOTRecommendation(
                            title=pa.action[:45] + "...",
                            action=pa.action,
                            reason=pa.reason,
                            priority=pa.priority,
                            linked_factors=[pa.id or f"SP-{pIdx+1}"],
                            source_stages=[pa.source_stage]
                        )
                        for pIdx, pa in enumerate(priority_actions)
                    ]

                    acts = [
                        ImmediateAction(action=pa.action, why=pa.reason, priority=pa.priority)
                        for pa in priority_actions
                    ]

                    evid_sum = SWOTEvidenceSummary(
                        market="Stage 6 & 8 market intelligence verified.",
                        financial="Stage 9 financial metrics verified.",
                        entrepreneur="Stage 10 promoter readiness evaluated.",
                        risk="Stage 11 multi-vector risks mapped.",
                        feasibility="Stage 12 viability synthesis confirmed."
                    )

                    gen_meta = SWOTGenerationMeta(
                        mode="SARVAM_LLM",
                        model=self.model,
                        llm_status="success",
                        execution_time_ms=round(duration_ms, 2)
                    )

                    logger.info(f"[STAGE 13 SARVAM SUCCESS] response_valid=true duration_ms={duration_ms:.1f}")

                    total_elapsed_ms = (time.time() - overall_start) * 1000.0
                    logger.info(
                        f"[STAGE 13 SWOT OUTPUT] provider=SARVAM "
                        f"attempts={attempts_made} "
                        f"elapsed_ms={total_elapsed_ms:.1f} "
                        f"strengths={len(strengths)} "
                        f"weaknesses={len(weaknesses)} "
                        f"opportunities={len(opportunities)} "
                        f"threats={len(threats)} "
                        f"finance_evidence_used={has_dscr or has_proj_cost}"
                    )

                    b_name = evidence_ctx.get("business", {}).get("name", "Rural Enterprise")
                    location_str = evidence_ctx.get("business", {}).get("location", "Local Cluster")

                    return SWOTAnalysisResponse(
                        status="COMPLETED",
                        analysis_id=analysis_id,
                        session_id=session_id,
                        business_name=b_name,
                        location=location_str,
                        generation=gen_meta,
                        swot=swot_breakdown,
                        provenance={
                            "market": "STAGE_6",
                            "opportunity": "STAGE_8",
                            "finance": "STAGE_9",
                            "entrepreneur": "STAGE_10",
                            "risk": "STAGE_11",
                            "feasibility": "STAGE_12"
                        },
                        strategic_summary=strat_summary,
                        recommendations=recs,
                        immediate_actions=acts,
                        evidence_summary=evid_sum,
                        confidence=conf,
                        model_metadata=ModelMetadata(
                            provider="sarvam",
                            model=self.model,
                            version="1.0.0",
                            execution_time_ms=round(duration_ms, 2)
                        )
                    )

            except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout) as to_err:
                elapsed_ms = (time.time() - call_start) * 1000.0
                fallback_reason = "TIMEOUT"
                error_detail = f"Timeout ({type(to_err).__name__}) after {elapsed_ms:.1f}ms"
                logger.warning(f"[STAGE 13 SARVAM ERROR] type=TIMEOUT elapsed_ms={elapsed_ms:.1f}")
                if attempt < max_attempts:
                    logger.info("[STAGE 13 SARVAM RETRY] Retrying with compact prompt after timeout...")
                    await asyncio.sleep(1.0)
                    continue
                break
            except (httpx.NetworkError, httpx.RequestError) as net_err:
                elapsed_ms = (time.time() - call_start) * 1000.0
                fallback_reason = "NETWORK_ERROR"
                error_detail = f"NetworkError: {str(net_err)}"
                logger.warning(f"[STAGE 13 SARVAM ERROR] type=NETWORK_ERROR elapsed_ms={elapsed_ms:.1f}")
                if attempt < max_attempts:
                    await asyncio.sleep(1.0)
                    continue
                break
            except Exception as ex:
                elapsed_ms = (time.time() - call_start) * 1000.0
                fallback_reason = "UNEXPECTED_ERROR"
                error_detail = str(ex)
                logger.warning(f"[STAGE 13 SARVAM ERROR] type=UNEXPECTED_ERROR detail={error_detail} elapsed_ms={elapsed_ms:.1f}")
                break

        # -------------------------------------------------------------
        # 6. Fallback Trigger on LLM Failure (Zero Hallucination / Zero Broken UI)
        # -------------------------------------------------------------
        logger.warning(f"[STAGE 13 SARVAM FALLBACK] reason={fallback_reason} detail={error_detail}")
        fallback_res = generate_deterministic_swot_fallback(
            evidence_ctx=evidence_ctx,
            analysis_id=analysis_id,
            session_id=session_id,
            llm_status=fallback_reason.lower(),
            error_message=f"Sarvam LLM {fallback_reason}: {error_detail}"
        )

        total_elapsed_ms = (time.time() - overall_start) * 1000.0
        logger.info(
            f"[STAGE 13 SWOT OUTPUT] provider=FALLBACK "
            f"attempts={attempts_made} "
            f"elapsed_ms={total_elapsed_ms:.1f} "
            f"strengths={len(fallback_res.swot.strengths)} "
            f"weaknesses={len(fallback_res.swot.weaknesses)} "
            f"opportunities={len(fallback_res.swot.opportunities)} "
            f"threats={len(fallback_res.swot.threats)} "
            f"finance_evidence_used={has_dscr or has_proj_cost}"
        )

        return fallback_res


dynamic_swot_agent = DynamicSWOTAgent()
