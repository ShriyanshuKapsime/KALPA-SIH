/**
 * Canonical Business Context Adapter (Frontend)
 * Normalizes diverse upstream profile shapes (Stage 1 Intake, Stage 2 Classification,
 * Stage 3 Canonical Profile) into one authoritative business identity contract.
 * Strictly eliminates all hardcoded business fallbacks ('saree_retail', '47711', etc.).
 */

export function extractCanonicalBusinessContext(profile, fallbackState = {}) {
  if (!profile && !fallbackState) return null;
  const p = profile || {};
  const root = p.profile || p.data || p;
  const bizProfile = root.business_profile || root.business_context || root;
  const nicObj = bizProfile.nic || root.nic || {};
  const locObj = root.location_profile || root.location || {};
  const finObj = root.financial_profile || root.financial_analysis || {};
  const provObj = root.provenance || {};

  // Extract Business ID (authoritative hierarchy)
  const businessId =
    bizProfile.business_id ||
    bizProfile.business_node_id ||
    provObj.classification_id ||
    root.business_id ||
    root.analysis_id ||
    fallbackState.businessId ||
    null;

  // Extract Session ID
  const sessionId =
    root.session_id ||
    provObj.stage_1_session_id ||
    fallbackState.sessionId ||
    null;

  // Extract Business Name / Specific Business / Activity
  const businessName =
    bizProfile.specific_business ||
    bizProfile.business_name ||
    bizProfile.original_concept ||
    root.specific_business ||
    fallbackState.businessName ||
    null;

  // Extract NIC code
  const nicCode =
    (typeof nicObj === 'object' ? nicObj.code : nicObj) ||
    bizProfile.nic_code ||
    root.nic_code ||
    null;

  const nicDescription =
    (typeof nicObj === 'object' ? (nicObj.description || nicObj.title) : null) ||
    bizProfile.nic_title ||
    null;

  // Sector, Category, Subcategory
  const sector = bizProfile.sector || root.sector || null;
  const category = bizProfile.category || root.category || null;
  const subcategory =
    bizProfile.sub_category ||
    bizProfile.subcategory ||
    root.subcategory ||
    null;

  const archetype =
    bizProfile.archetype ||
    root.archetype ||
    category ||
    null;

  // Location
  const locProposed = root.proposed_location || root.profile?.proposed_location;
  const resolvedDistrict =
    typeof locObj.district === 'string'
      ? locObj.district
      : (typeof locProposed === 'object' ? locProposed?.district : (typeof locProposed === 'string' ? locProposed : (fallbackState.district || null)));
  
  const resolvedState =
    typeof locObj.state === 'string'
      ? locObj.state
      : (typeof locProposed === 'object' ? locProposed?.state : (fallbackState.state || null));

  // Legal Constitution
  const legalConstitution =
    bizProfile.constitution ||
    bizProfile.legal_constitution ||
    root.legal_constitution ||
    null;

  // Financial margin and preferred cost
  const availableMarginCapital =
    finObj.available_margin_capital ||
    finObj.available_capital ||
    fallbackState.availableMarginCapital ||
    null;

  const preferredProjectCost =
    finObj.preferred_project_cost ? parseFloat(finObj.preferred_project_cost) : null;

  return {
    business_id: businessId,
    session_id: sessionId,
    scenario_id: fallbackState.scenarioId || (businessId ? `DPR-${String(businessId).slice(0, 8)}` : (sessionId ? `DPR-${String(sessionId).slice(0, 8)}` : 'default')),
    enterprise_name: businessName,
    business_activity: businessName,
    specific_business: businessName,
    business_node_id: businessId,
    archetype: archetype,
    sector: sector,
    category: category,
    subcategory: subcategory,
    nic_code: nicCode,
    nic_description: nicDescription,
    district: resolvedDistrict,
    state: resolvedState,
    legal_constitution: legalConstitution,
    available_margin_capital: availableMarginCapital,
    preferred_project_cost: preferredProjectCost,
    is_valid: Boolean(businessName || nicCode || businessId)
  };
}
