"""
Script to apply ontology classification fallback, monotonic previous_fields, and financial reconciliation in dpr_context_builder.py
"""
target_file = r"c:\Users\shriy\OneDrive\Documents\KALPA SIH\ai-service\app\services\dpr_stage1\dpr_context_builder.py"

with open(target_file, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update _resolve_single_field definition and sources to include previous_fields
old_sig = '''    def _resolve_single_field(
        self,
        field_def: DPRFieldDefinition,
        applicable: bool,
        archetype: Optional[str],
        business_profile: Dict[str, Any],
        market_context: Dict[str, Any],
        risk_context: Dict[str, Any],
        swot_context: Dict[str, Any],
        feasibility_context: Dict[str, Any],
        financial_package: Dict[str, Any],
        benchmarks: Dict[str, Any],
        benchmark_status: str,
        documents: Dict[str, Any],
        user_overrides: Dict[str, Any],
        user_answers: Dict[str, Any],
        accepted_benchmarks: Dict[str, Any],
        scenario_id: str,
        entrepreneur_profile: Optional[Dict[str, Any]] = None,
        entrepreneur_readiness: Optional[Dict[str, Any]] = None,
        opportunity_context: Optional[Dict[str, Any]] = None,
        policy_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:'''

new_sig = '''    def _resolve_single_field(
        self,
        field_def: DPRFieldDefinition,
        applicable: bool,
        archetype: Optional[str],
        business_profile: Dict[str, Any],
        market_context: Dict[str, Any],
        risk_context: Dict[str, Any],
        swot_context: Dict[str, Any],
        feasibility_context: Dict[str, Any],
        financial_package: Dict[str, Any],
        benchmarks: Dict[str, Any],
        benchmark_status: str,
        documents: Dict[str, Any],
        user_overrides: Dict[str, Any],
        user_answers: Dict[str, Any],
        accepted_benchmarks: Dict[str, Any],
        scenario_id: str,
        entrepreneur_profile: Optional[Dict[str, Any]] = None,
        entrepreneur_readiness: Optional[Dict[str, Any]] = None,
        opportunity_context: Optional[Dict[str, Any]] = None,
        policy_data: Optional[Dict[str, Any]] = None,
        previous_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:'''

if old_sig in code:
    code = code.replace(old_sig, new_sig)
    print("Replaced _resolve_single_field signature")
else:
    print("WARNING: old_sig not matched!")

# 2. Add previous_fields to sources dict inside _resolve_single_field
old_sources = '''            "benchmarks": benchmarks,
            "policy_data": policy_data or {},
        }

        sem_res = resolve_field_semantically(field_id=fid, sources=sources, archetype=archetype)'''

new_sources = '''            "benchmarks": benchmarks,
            "policy_data": policy_data or {},
            "previous_fields": previous_fields or {},
        }

        sem_res = resolve_field_semantically(field_id=fid, sources=sources, archetype=archetype)'''

if old_sources in code:
    code = code.replace(old_sources, new_sources)
    print("Added previous_fields to sources")
else:
    print("WARNING: old_sources not matched!")

# 3. Add monotonic check and audit logging inside _resolve_single_field
old_val_check = '''        val = sem_res.get("value")
        raw_status = sem_res.get("status")
        source_type = sem_res.get("source_type", "UNKNOWN")'''

new_val_check = '''        val = sem_res.get("value")
        raw_status = sem_res.get("status")
        source_type = sem_res.get("source_type", "UNKNOWN")

        # Monotonic resolution protection: Never lose previously resolved values
        prev_f = (previous_fields or {}).get(fid)
        if prev_f and isinstance(prev_f, dict) and prev_f.get("value") is not None:
            prev_status = str(prev_f.get("status", ""))
            if prev_status.startswith("RESOLVED_") and (val is None or raw_status in ["UNKNOWN", "USER_REQUIRED"]):
                logger.warning(f"[DPRMonotonic] Preserving {fid} previous value {prev_f.get('value')} ({prev_f.get('source_id')}) over None/UNKNOWN")
                val = prev_f["value"]
                raw_status = prev_f.get("status", raw_status)
                source_type = prev_f.get("source_type", source_type)
                source_id = prev_f.get("source_id", "MONOTONIC_PRESERVATION")
                source_ref = prev_f.get("source_reference", "Monotonic Preservation")

        # Context merge audit logging
        logger.debug(f"[DPRContextMerge] field_id={fid}, old_value={prev_f.get('value') if prev_f else None}, old_source={prev_f.get('source_id') if prev_f else None}, new_value={val}, new_source={source_id if 'source_id' in locals() else None}, action={'PRESERVED' if val == (prev_f.get('value') if prev_f else None) else 'UPDATED'}")'''

if old_val_check in code:
    code = code.replace(old_val_check, new_val_check)
    print("Added monotonic check and audit logging")
else:
    print("WARNING: old_val_check not matched!")

# 4. Pass previous_fields in build_context when calling _resolve_single_field
old_call = '''            field_record = self._resolve_single_field(
                field_def=field_def,
                applicable=applicable,
                archetype=authoritative_archetype,
                business_profile=business_profile,
                market_context=market_context,
                risk_context=risk_context,
                swot_context=swot_context,
                feasibility_context=feasibility_context,
                financial_package=financial_package,
                benchmarks=benchmarks,
                benchmark_status=benchmark_status,
                documents=documents,
                user_overrides=overrides,
                user_answers=answers,
                accepted_benchmarks=acc_benchmarks,
                scenario_id=active_scenario_id,
                entrepreneur_profile=upstream_data.get("entrepreneur_profile") or {},
                entrepreneur_readiness=upstream_data.get("entrepreneur_readiness") or {},
                opportunity_context=upstream_data.get("opportunity_context") or {},
                policy_data=upstream_data.get("policy_data") or {},
            )'''

new_call = '''            scen_prev = (getattr(scen, "resolved_fields", {}) if scen else {}) or (getattr(scen, "fields", {}) if scen else {}) or {}
            field_record = self._resolve_single_field(
                field_def=field_def,
                applicable=applicable,
                archetype=authoritative_archetype,
                business_profile=business_profile,
                market_context=market_context,
                risk_context=risk_context,
                swot_context=swot_context,
                feasibility_context=feasibility_context,
                financial_package=financial_package,
                benchmarks=benchmarks,
                benchmark_status=benchmark_status,
                documents=documents,
                user_overrides=overrides,
                user_answers=answers,
                accepted_benchmarks=acc_benchmarks,
                scenario_id=active_scenario_id,
                entrepreneur_profile=upstream_data.get("entrepreneur_profile") or {},
                entrepreneur_readiness=upstream_data.get("entrepreneur_readiness") or {},
                opportunity_context=upstream_data.get("opportunity_context") or {},
                policy_data=upstream_data.get("policy_data") or {},
                previous_fields=scen_prev,
            )'''

if old_call in code:
    code = code.replace(old_call, new_call)
    print("Passed previous_fields in build_context")
else:
    print("WARNING: old_call not matched!")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(code)

print("Finished updating dpr_context_builder.py")
