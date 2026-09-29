/**
 * Package-level identity validator for DPR Stage 14.1 Context and Stage 14.2 Enrichment.
 * Blocks rendering if any cross-scenario or cross-business contamination is detected.
 */

export const validatePackageIdentity = (pkg, requestedIdentity = {}) => {
  if (!pkg) {
    return { valid: false, reason: 'No DPR package provided' };
  }

  const reqBiz = (requestedIdentity.business_id || '').trim().toLowerCase();
  const reqScen = (requestedIdentity.scenario_id || '').trim().toLowerCase();

  const pkgBiz = (pkg.business_id || '').trim().toLowerCase();
  const pkgScen = (pkg.scenario_id || '').trim().toLowerCase();

  if (pkgBiz && reqBiz && pkgBiz !== reqBiz) {
    console.error(`[DPR_CROSS_SCENARIO_DATA_ERROR]
field=package.business_id
requested_business_id=${requestedIdentity.business_id}
field_business_id=${pkg.business_id}
requested_scenario_id=${requestedIdentity.scenario_id}
field_scenario_id=${pkg.scenario_id}
source=package_root
value=${pkgBiz}`);

    return {
      valid: false,
      reason: `Package business_id mismatch: expected "${requestedIdentity.business_id}", got "${pkg.business_id}"`
    };
  }

  if (pkgScen && reqScen && pkgScen !== reqScen) {
    console.error(`[DPR_CROSS_SCENARIO_DATA_ERROR]
field=package.scenario_id
requested_business_id=${requestedIdentity.business_id}
field_business_id=${pkg.business_id}
requested_scenario_id=${requestedIdentity.scenario_id}
field_scenario_id=${pkg.scenario_id}
source=package_root
value=${pkgScen}`);

    return {
      valid: false,
      reason: `Package scenario_id mismatch: expected "${requestedIdentity.scenario_id}", got "${pkg.scenario_id}"`
    };
  }

  // Validate fields for contamination
  const fields = pkg.fields || {};
  for (const [key, fieldObj] of Object.entries(fields)) {
    if (!fieldObj || typeof fieldObj !== 'object') continue;

    const source = (fieldObj.source || fieldObj.source_type || '').toLowerCase();
    const isUserProvided = source.includes('user') || source.includes('provided') || source.includes('answer') || source.includes('override');

    const fieldBiz = (fieldObj.source_business_id || fieldObj.business_id || '').trim().toLowerCase();
    const fieldScen = (fieldObj.source_scenario_id || fieldObj.scenario_id || '').trim().toLowerCase();
    const valStr = typeof fieldObj.value === 'string' ? fieldObj.value : JSON.stringify(fieldObj.value || '');

    // User-provided fields MUST match requested business_id
    if (isUserProvided && fieldBiz && reqBiz && fieldBiz !== reqBiz) {
      console.error(`[DPR_CROSS_SCENARIO_DATA_ERROR]
field=${key}
requested_business_id=${requestedIdentity.business_id}
field_business_id=${fieldObj.source_business_id || fieldObj.business_id}
requested_scenario_id=${requestedIdentity.scenario_id}
field_scenario_id=${fieldObj.source_scenario_id || fieldObj.scenario_id}
source=${source}
value=${valStr}`);

      return {
        valid: false,
        reason: `Contaminated user field "${key}": belongs to "${fieldBiz}", but requested business is "${reqBiz}"`
      };
    }

    // Scenario-specific fields MUST match requested scenario_id if present
    if (fieldScen && reqScen && fieldScen !== reqScen) {
      console.error(`[DPR_CROSS_SCENARIO_DATA_ERROR]
field=${key}
requested_business_id=${requestedIdentity.business_id}
field_business_id=${fieldObj.source_business_id || fieldObj.business_id}
requested_scenario_id=${requestedIdentity.scenario_id}
field_scenario_id=${fieldObj.source_scenario_id || fieldObj.scenario_id}
source=${source}
value=${valStr}`);

      return {
        valid: false,
        reason: `Scenario mismatch on field "${key}": belongs to "${fieldScen}", but requested scenario is "${reqScen}"`
      };
    }

    // Direct concept conflict check on identity fields (e.g. Dairy showing Kirana/Grocery, or Saree showing Dairy)
    if (key === 'dpr_title' || key === 'business_name' || key === 'business_activity') {
      const lowerVal = valStr.toLowerCase();
      if (reqBiz.includes('dairy') && (lowerVal.includes('kirana') || lowerVal.includes('grocery') || lowerVal.includes('saree'))) {
        console.error(`[DPR_CROSS_SCENARIO_DATA_ERROR]
field=${key}
requested_business_id=${requestedIdentity.business_id}
field_business_id=grocery/saree
requested_scenario_id=${requestedIdentity.scenario_id}
field_scenario_id=${fieldScen || 'unknown'}
source=${source}
value=${valStr}`);

        return {
          valid: false,
          reason: `Cross-business text contamination on "${key}": "${valStr}" contains non-dairy terms for dairy scenario`
        };
      }
      if (reqBiz.includes('saree') && (lowerVal.includes('kirana') || lowerVal.includes('grocery') || lowerVal.includes('dairy'))) {
        console.error(`[DPR_CROSS_SCENARIO_DATA_ERROR]
field=${key}
requested_business_id=${requestedIdentity.business_id}
field_business_id=dairy/grocery
requested_scenario_id=${requestedIdentity.scenario_id}
field_scenario_id=${fieldScen || 'unknown'}
source=${source}
value=${valStr}`);

        return {
          valid: false,
          reason: `Cross-business text contamination on "${key}": "${valStr}" contains non-saree terms for saree scenario`
        };
      }
      if ((reqBiz.includes('grocery') || reqBiz.includes('kirana')) && (lowerVal.includes('dairy') || lowerVal.includes('saree'))) {
        console.error(`[DPR_CROSS_SCENARIO_DATA_ERROR]
field=${key}
requested_business_id=${requestedIdentity.business_id}
field_business_id=dairy/saree
requested_scenario_id=${requestedIdentity.scenario_id}
field_scenario_id=${fieldScen || 'unknown'}
source=${source}
value=${valStr}`);

        return {
          valid: false,
          reason: `Cross-business text contamination on "${key}": "${valStr}" contains non-grocery terms for grocery scenario`
        };
      }
    }
  }

  return { valid: true };
};
