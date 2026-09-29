import sys
import os
sys.path.insert(0, r"c:\Users\shriy\OneDrive\Documents\KALPA SIH\ai-service")
from app.database.session import SessionLocal
from app.database.models.profile import StructuredBusinessProfile
from app.database.models.intake import IntakeSession
from app.database.models.finance import FinancialProfile
from app.database.models.feasibility import FeasibilityResult
from app.database.models.swot import SwotResult
from app.database.models.entrepreneur import EntrepreneurProfile

db = SessionLocal()
sb_list = db.query(StructuredBusinessProfile).all()
print(f"Found {len(sb_list)} StructuredBusinessProfiles:")
for sb in sb_list:
    print(f"  ID: {sb.id}")
    print(f"  session_id: {sb.session_id}")
    print(f"  biz: {sb.specific_business}")
    print(f"  nic: {sb.nic_code}")
    print(f"  state: {sb.state}, dist: {sb.district}")
    if sb.profile_json:
        pj = sb.profile_json
        print(f"    keys in profile_json: {list(pj.keys())}")
        for k in ["business_profile", "location_profile", "entrepreneur_readiness", "entrepreneur_profile", "financial_analysis", "market_evidence"]:
            if pj.get(k):
                print(f"    {k}: {pj[k]}")

intakes = db.query(IntakeSession).all()
print(f"\nFound {len(intakes)} IntakeSessions:")
for it in intakes:
    print(f"  ID: {it.id}, profile: {it.structured_profile}")

fps = db.query(FinancialProfile).all()
print(f"\nFound {len(fps)} FinancialProfiles:")
for fp in fps:
    print(f"  ID: {fp.id}, biz_id: {fp.business_id}, cost: {fp.total_project_cost}, loan: {fp.bank_loan_requirement}, promoter: {fp.promoter_contribution}, dscr: {fp.debt_service_coverage_ratio}, bep: {fp.break_even_percentage}")

feas_list = db.query(FeasibilityResult).all()
print(f"\nFound {len(feas_list)} FeasibilityResults:")
for f in feas_list:
    print(f"  ID: {f.id}, biz_id: {f.business_id}, score: {f.overall_feasibility_score}, status: {f.viability_status}")

swots = db.query(SwotResult).all()
print(f"\nFound {len(swots)} SwotResults:")
for sw in swots:
    print(f"  ID: {sw.id}, biz_id: {sw.business_id}, swot_keys: {list(sw.swot_json.keys()) if sw.swot_json else None}")
