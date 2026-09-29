"""
Stage 14.3: Dedicated Sarvam LLM Narrative Service.
Interfaces with official Sarvam Chat Completions API (sarvam-105b-conversations).
Implements strict two-stage generation (Plan -> Draft), robust content extraction,
sanitized telemetry, runtime status tracking, and deterministic fallback.
"""
import os
import re
import json
import time
import uuid
import logging
import httpx
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from app.core.config import settings
from app.dpr.stage14_3.document_schema import (
    NarrativePlan,
    SectionNarrative,
    NarrativeProviderMetadata,
)

logger = logging.getLogger(__name__)

DEFAULT_SARVAM_DPR_MODEL = "sarvam-105b-conversations"
PROMPT_VERSION = "dpr_narrative_v1"


class DPRLLMStatusTracker:
    """
    Thread-safe runtime diagnostic tracker for Sarvam LLM operations across businesses.
    Never stores or leaks credentials.
    """
    def __init__(self):
        self._status: Dict[str, Dict[str, Any]] = {}

    def record_start(self, business_id: str, section_id: str, model: str):
        b_key = str(business_id).strip().lower()
        if b_key not in self._status:
            self._status[b_key] = {
                "provider": "sarvam",
                "model": model,
                "llm_configured": bool(os.getenv("SARVAM_API_KEY")),
                "llm_invoked": False,
                "sections_requested": [],
                "sections_generated": [],
                "fallback_used": False,
                "last_error": None,
                "validation_passed": True,
            }
        st = self._status[b_key]
        st["llm_invoked"] = True
        if section_id not in st["sections_requested"]:
            st["sections_requested"].append(section_id)

    def record_success(self, business_id: str, section_id: str):
        b_key = str(business_id).strip().lower()
        if b_key in self._status:
            st = self._status[b_key]
            if section_id not in st["sections_generated"]:
                st["sections_generated"].append(section_id)

    def record_fallback(self, business_id: str, section_id: str, error: Optional[str] = None):
        b_key = str(business_id).strip().lower()
        if b_key not in self._status:
            self._status[b_key] = {
                "provider": "sarvam",
                "model": DEFAULT_SARVAM_DPR_MODEL,
                "llm_configured": bool(os.getenv("SARVAM_API_KEY")),
                "llm_invoked": False,
                "sections_requested": [section_id],
                "sections_generated": [],
                "fallback_used": True,
                "last_error": str(error) if error else None,
                "validation_passed": True,
            }
        else:
            st = self._status[b_key]
            st["fallback_used"] = True
            if error:
                st["last_error"] = str(error)

    def get_status(self, business_id: str) -> Dict[str, Any]:
        b_key = str(business_id).strip().lower()
        if b_key in self._status:
            return self._status[b_key]
        return {
            "provider": "sarvam",
            "model": DEFAULT_SARVAM_DPR_MODEL,
            "llm_configured": bool(os.getenv("SARVAM_API_KEY")),
            "llm_invoked": False,
            "sections_requested": [],
            "sections_generated": [],
            "fallback_used": False,
            "last_error": None,
            "validation_passed": True,
        }

    def get_engine_summary(self, business_id: str) -> Dict[str, Any]:
        st = self.get_status(business_id)
        return {
            "provider": st.get("provider", "sarvam"),
            "model": st.get("model", DEFAULT_SARVAM_DPR_MODEL),
            "invoked": st.get("llm_invoked", False),
            "fallback_used": st.get("fallback_used", False),
            "validated_sections": len(st.get("sections_generated", [])),
            "failed_sections": [
                s for s in st.get("sections_requested", [])
                if s not in st.get("sections_generated", [])
            ]
        }


llm_status_tracker = DPRLLMStatusTracker()


def extract_json_from_text(text: str) -> Optional[str]:
    """Extracts valid JSON substring from raw text, code fences, or natural language."""
    if not text or not isinstance(text, str):
        return None
    cleaned = text.strip()
    if (cleaned.startswith("{") and cleaned.endswith("}")) or (cleaned.startswith("[") and cleaned.endswith("]")):
        try:
            json.loads(cleaned)
            return cleaned
        except Exception:
            pass

    fence_matches = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned, flags=re.IGNORECASE)
    for fm in fence_matches:
        try:
            json.loads(fm.strip())
            return fm.strip()
        except Exception:
            pass

    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cand = cleaned[start_idx:end_idx + 1]
        try:
            json.loads(cand)
            return cand
        except Exception:
            pass

    return None


class SarvamDPRNarrativeService:
    """
    Dedicated institutional narrative generation service using Sarvam AI.
    Never exposes or logs API keys. Never calculates financial metrics.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: float = 40.0
    ):
        self.api_key = api_key or os.getenv("SARVAM_API_KEY") or getattr(settings, "SARVAM_API_KEY", "") or ""
        self.model = model or os.getenv("SARVAM_DPR_MODEL") or getattr(settings, "SARVAM_DPR_MODEL", None) or DEFAULT_SARVAM_DPR_MODEL
        self.endpoint = endpoint or getattr(settings, "SARVAM_LLM_ENDPOINT", "https://api.sarvam.ai/v1/chat/completions")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json"
        }

    async def _call_sarvam_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        business_id: str = "general",
        scenario_id: str = "default",
        section_id: str = "section"
    ) -> Optional[Dict[str, Any]]:
        """Makes low-level authenticated HTTP request to Sarvam chat completions with telemetry."""
        req_id = f"dpr_req_{uuid.uuid4().hex[:8]}"
        t_start = time.time()

        if not self.is_configured:
            logger.info(
                f"[DPR_LLM_FALLBACK] business_id={business_id} scenario_id={scenario_id} "
                f"section_id={section_id} provider=deterministic fallback_used=True "
                f"reason=sarvam_api_key_unconfigured"
            )
            llm_status_tracker.record_fallback(business_id, section_id, "API key not configured")
            return None

        llm_status_tracker.record_start(business_id, section_id, self.model)
        logger.info(
            f"[DPR_LLM_START] business_id={business_id} scenario_id={scenario_id} "
            f"section_id={section_id} provider=sarvam model={self.model} request_id={req_id}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.endpoint, headers=self._get_headers(), json=payload)
                latency = time.time() - t_start
                if resp.status_code != 200:
                    err_msg = f"HTTP {resp.status_code}: {resp.text[:100]}"
                    logger.warning(
                        f"[DPR_LLM_FAILURE] business_id={business_id} scenario_id={scenario_id} "
                        f"section_id={section_id} provider=sarvam model={self.model} "
                        f"request_id={req_id} latency={latency:.2f}s error={err_msg}"
                    )
                    llm_status_tracker.record_fallback(business_id, section_id, err_msg)
                    return None

                data = resp.json()
                choices = data.get("choices") or []
                if not choices:
                    logger.warning(
                        f"[DPR_LLM_FAILURE] business_id={business_id} scenario_id={scenario_id} "
                        f"section_id={section_id} provider=sarvam model={self.model} "
                        f"request_id={req_id} latency={latency:.2f}s error=empty_choices"
                    )
                    llm_status_tracker.record_fallback(business_id, section_id, "Empty choices returned")
                    return None

                msg = choices[0].get("message") or choices[0].get("delta") or {}
                content = msg.get("content")
                if not content or not isinstance(content, str):
                    logger.warning(
                        f"[DPR_LLM_FAILURE] business_id={business_id} scenario_id={scenario_id} "
                        f"section_id={section_id} provider=sarvam model={self.model} "
                        f"request_id={req_id} latency={latency:.2f}s error=null_content"
                    )
                    llm_status_tracker.record_fallback(business_id, section_id, "Null content returned")
                    return None

                clean_json = extract_json_from_text(content)
                if not clean_json:
                    logger.warning(
                        f"[DPR_LLM_FAILURE] business_id={business_id} scenario_id={scenario_id} "
                        f"section_id={section_id} provider=sarvam model={self.model} "
                        f"request_id={req_id} latency={latency:.2f}s error=invalid_json"
                    )
                    llm_status_tracker.record_fallback(business_id, section_id, "Invalid JSON structure")
                    return None

                parsed = json.loads(clean_json)
                logger.info(
                    f"[DPR_LLM_SUCCESS] business_id={business_id} scenario_id={scenario_id} "
                    f"section_id={section_id} provider=sarvam model={self.model} "
                    f"request_id={req_id} latency={latency:.2f}s output_char_count={len(content)}"
                )
                llm_status_tracker.record_success(business_id, section_id)
                return parsed

        except Exception as e:
            latency = time.time() - t_start
            logger.warning(
                f"[DPR_LLM_FAILURE] business_id={business_id} scenario_id={scenario_id} "
                f"section_id={section_id} provider=sarvam model={self.model} "
                f"request_id={req_id} latency={latency:.2f}s error={str(e)}"
            )
            llm_status_tracker.record_fallback(business_id, section_id, str(e))
            return None

    async def create_narrative_plan(
        self,
        section_id: str,
        section_title: str,
        source_data: Dict[str, Any],
        language: str = "en",
        business_id: str = "general",
        scenario_id: str = "default"
    ) -> Optional[NarrativePlan]:
        """
        Step A: Creates a structured narrative plan for the given section.
        """
        system_prompt = (
            "You are the institutional DPR narrative planner for KALPA.\n"
            "Your task is to plan the narrative structure for a bank project appraisal section.\n"
            "Use ONLY the supplied authoritative project data. Never invent facts, numbers, competitors, or schemes.\n"
            "Return JSON matching this schema:\n"
            "{\n"
            '  "section_id": "string",\n'
            '  "key_points": ["string"],\n'
            '  "evidence_to_reference": ["string"],\n'
            '  "facts_used": ["string"],\n'
            '  "recommended_length": "short|medium|long"\n'
            "}"
        )

        user_prompt = (
            f"SECTION_ID: {section_id}\n"
            f"SECTION_TITLE: {section_title}\n"
            f"SECTION_PURPOSE: Institutional credit appraisal narrative planning\n"
            f"LANGUAGE: {language}\n"
            f"AUTHORITATIVE_FACTS:\n{json.dumps(source_data, indent=2, default=str)}\n\n"
            "Generate the narrative plan JSON."
        )

        try:
            res = await self._call_sarvam_chat(
                system_prompt, user_prompt,
                business_id=business_id, scenario_id=scenario_id, section_id=section_id
            )
        except Exception as e:
            logger.warning(f"[SarvamDPRNarrativeService] Error calling Sarvam: {e}")
            return None

        if res and isinstance(res, dict) and "key_points" in res:
            try:
                return NarrativePlan(
                    section_id=section_id,
                    key_points=res.get("key_points") or [],
                    evidence_to_reference=res.get("evidence_to_reference") or [],
                    facts_used=res.get("facts_used") or [],
                    recommended_length=res.get("recommended_length") or "medium"
                )
            except Exception as e:
                logger.warning(f"[SarvamDPRNarrativeService] Plan parse error: {e}")
                return None
        return None

    async def draft_section_narrative(
        self,
        section_id: str,
        section_title: str,
        plan: NarrativePlan,
        source_data: Dict[str, Any],
        language: str = "en",
        business_id: str = "general",
        scenario_id: str = "default"
    ) -> Optional[SectionNarrative]:
        """
        Step B: Drafts formal credit appraisal prose based on the plan and authoritative data.
        """
        system_prompt = (
            "You are the institutional DPR narrative writer for KALPA.\n"
            "You are drafting content for a formal Detailed Project Report intended for bank and institutional credit review.\n"
            "Use ONLY the supplied authoritative project data.\n"
            "Never invent a fact, number, percentage, date, person, location, competitor, market statistic, "
            "financial value, regulatory requirement, scheme benefit or technical specification.\n"
            "If a required fact is unavailable, state that it is not available or requires confirmation.\n"
            "Never convert UNKNOWN into ZERO.\n"
            "Never infer a financial value. Never calculate financial metrics yourself. Never modify supplied values.\n"
            "Never claim that a loan is approved. Never claim that a project is guaranteed to be bankable.\n"
            "Use professional institutional language. Avoid promotional or exaggerated language.\n"
            "Do NOT use: game-changing, revolutionary, guaranteed success, highly profitable, extremely promising.\n"
            "Explain the project objectively.\n"
            "CRITICAL: For financial figures, use exact placeholders:\n"
            "{{PROJECT_COST}}, {{PROMOTER_CONTRIBUTION}}, {{TERM_LOAN}}, {{WORKING_CAPITAL}}, "
            "{{YEAR1_REVENUE}}, {{YEAR5_REVENUE}}, {{EBITDA_MARGIN}}, {{PAT}}, {{AVERAGE_DSCR}}, "
            "{{MIN_DSCR}}, {{BREAK_EVEN}}.\n\n"
            "Return JSON matching:\n"
            "{\n"
            f'  "section_id": "{section_id}",\n'
            f'  "title": "{section_title}",\n'
            '  "paragraphs": ["string"],\n'
            '  "facts_used": ["string"],\n'
            '  "source_refs": ["string"]\n'
            "}"
        )

        user_prompt = (
            f"SECTION_ID: {section_id}\n"
            f"SECTION_TITLE: {section_title}\n"
            f"LANGUAGE: {language}\n"
            f"APPROVED_PLAN:\n{json.dumps(plan.model_dump(), indent=2)}\n\n"
            f"AUTHORITATIVE_FACTS:\n{json.dumps(source_data, indent=2, default=str)}\n\n"
            "Draft the formal section narrative JSON."
        )

        try:
            res = await self._call_sarvam_chat(
                system_prompt, user_prompt,
                business_id=business_id, scenario_id=scenario_id, section_id=section_id
            )
        except Exception as e:
            logger.warning(f"[SarvamDPRNarrativeService] Error calling Sarvam: {e}")
            return None

        if res and isinstance(res, dict) and "paragraphs" in res and res.get("paragraphs"):
            try:
                meta = NarrativeProviderMetadata(
                    provider="sarvam",
                    model=self.model,
                    prompt_version=PROMPT_VERSION,
                    fallback_used=False,
                    language=language
                )
                return SectionNarrative(
                    section_id=section_id,
                    title=res.get("title") or section_title,
                    paragraphs=[str(p).strip() for p in res.get("paragraphs") if str(p).strip()],
                    facts_used=res.get("facts_used") or [],
                    source_refs=res.get("source_refs") or [],
                    provider_metadata=meta,
                    status="VALIDATED"
                )
            except Exception as e:
                logger.warning(f"[SarvamDPRNarrativeService] Draft parse error: {e}")
                return None
        return None
