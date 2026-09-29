filepath = "frontend/src/pages/DPR/DPRPage.jsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

has_crlf = "\r\n" in content
content = content.replace("\r\n", "\n")

# 1. Update isReadyFor14_2 definition
old_ready = "  const isReadyFor14_2 = gapAnalysis?.is_ready_for_stage_14_2 ?? false;"
new_ready = """  const isReadyFor14_2 = Boolean(
    gapAnalysis?.is_ready_for_stage_14_2 ||
    gapAnalysis?.can_proceed_to_dpr ||
    (gapAnalysis && gapAnalysis.blocking_gaps?.length === 0 && (gapAnalysis.user_required === 0 || !gapAnalysis.user_required))
  );"""

if old_ready in content:
    content = content.replace(old_ready, new_ready)
    print("1. isReadyFor14_2 definition patched")
else:
    print("Warning: old_ready not found")

# 2. Add CTA button inside green resolution card
old_card = """              <div className="bg-emerald-950/20 border border-emerald-800/60 rounded-2xl p-6 text-center">
                <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-2" />
                <h3 className="text-lg font-bold text-white">Stage 14.1 Critical Inputs Resolved!</h3>
                <p className="text-sm text-slate-400 max-w-xl mx-auto mt-1">
                  All critical intake gaps have been resolved. You are ready to proceed to Stage 14.2 DPR Enrichment & Deterministic Inference.
                </p>
              </div>"""

new_card = """              <div className="bg-emerald-950/20 border border-emerald-800/60 rounded-2xl p-6 text-center space-y-4">
                <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
                <div>
                  <h3 className="text-lg font-bold text-white">Stage 14.1 Critical Inputs Resolved!</h3>
                  <p className="text-sm text-slate-400 max-w-xl mx-auto mt-1">
                    All critical intake gaps have been resolved. You are ready to proceed to Stage 14.2 DPR Enrichment & Deterministic Inference.
                  </p>
                </div>
                <div className="pt-2">
                  <Button
                    variant="primary"
                    disabled={!isReadyFor14_2}
                    onClick={() => {
                      navigate(`/dpr/enrichment?business_id=${businessId}&scenario_id=${activeScenarioId}`, {
                        state: { businessId, scenarioId: activeScenarioId }
                      });
                    }}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 inline-flex items-center gap-2 font-medium shadow-lg shadow-emerald-900/30"
                  >
                    Continue to DPR Enrichment →
                  </Button>
                </div>
              </div>"""

if old_card in content:
    content = content.replace(old_card, new_card)
    print("2. Green resolution card CTA button added")
else:
    print("Warning: old_card not found")

# 3. Fix object display so empty objects don't show as 'Configured'
old_disp1 = "{typeof fieldRec.value === 'object' ? 'Configured' : fieldRec.value !== null && fieldRec.value !== undefined ? String(fieldRec.value) : 'Not resolved'}"
new_disp1 = "{(typeof fieldRec.value === 'object' && fieldRec.value !== null && Object.keys(fieldRec.value).length > 0) ? 'Verified Schedule' : (fieldRec.value !== null && fieldRec.value !== undefined && typeof fieldRec.value !== 'object') ? String(fieldRec.value) : 'Not resolved'}"

if old_disp1 in content:
    content = content.replace(old_disp1, new_disp1)
    print("3. disp1 patched")

old_disp2 = "{typeof f.value === 'object' ? 'Configured' : f.value !== null && f.value !== undefined ? String(f.value) : 'Not resolved'}"
new_disp2 = "{(typeof f.value === 'object' && f.value !== null && Object.keys(f.value).length > 0) ? 'Verified Schedule' : (f.value !== null && f.value !== undefined && typeof f.value !== 'object') ? String(f.value) : 'Not resolved'}"

if old_disp2 in content:
    content = content.replace(old_disp2, new_disp2)
    print("4. disp2 patched")

if has_crlf:
    content = content.replace("\n", "\r\n")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("DPRPage.jsx successfully updated!")
