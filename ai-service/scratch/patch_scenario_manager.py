filepath = "ai-service/app/services/dpr_stage1/dpr_scenario_manager.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

old_code = """        target_cost = user_cost or safe_float(prev_fin.get("project_cost", {}).get("total_project_cost"))
        scheme_margin_pct = safe_float(prev_context.get("scheme_context", {}).get("promoter_margin_pct"))
        target_margin = user_margin or ((target_cost * (scheme_margin_pct / 100.0)) if (target_cost is not None and scheme_margin_pct is not None) else None)"""

new_code = """        target_cost = (
            user_cost
            or safe_float(prev_fin.get("project_cost", {}).get("total_project_cost"))
            or safe_float(prev_fin.get("total_project_cost"))
            or safe_float(prev_fields.get("total_project_cost", {}).get("value"))
        )
        if target_cost is None:
            from app.services.financial_engine.benchmark_adapter import financial_benchmark_adapter
            b_obj = financial_benchmark_adapter.get_benchmark_data(
                business_id=business_id,
                specific_business=bp.get("business_name") or bp.get("activity"),
                category=bp.get("archetype"),
                nic_code=bp.get("nic_code")
            )
            if b_obj and b_obj.typical_capex:
                target_cost = float(b_obj.typical_capex)

        scheme_margin_pct = safe_float(prev_context.get("scheme_context", {}).get("promoter_margin_pct")) or 10.0
        target_margin = user_margin or ((target_cost * (scheme_margin_pct / 100.0)) if target_cost is not None else None)"""

if old_code in content:
    content = content.replace(old_code, new_code)
    if has_crlf:
        content = content.replace("\n", "\r\n")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("dpr_scenario_manager.py patched successfully!")
else:
    print("ERROR: old_code in dpr_scenario_manager.py not matched")
