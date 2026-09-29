/**
 * Geocoding Service for KALPA Bharat Business Advisory.
 * Resolves GPS coordinates into human-readable Indian administrative hierarchy (Village, District, State).
 */

export async function reverseGeocodeCoords(latitude, longitude) {
  if (!latitude || !longitude) {
    return {
      resolvedName: 'Location coordinates captured',
      details: null,
    };
  }

  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}&zoom=14&addressdetails=1`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4500);

    const resp = await fetch(url, {
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        'User-Agent': 'KALPA-Bharat-Advisory/1.0 (Smart India Hackathon 2026)',
      },
    });
    clearTimeout(timeoutId);

    if (resp.ok) {
      const data = await resp.json();
      const addr = data.address || {};

      const locality =
        addr.village ||
        addr.hamlet ||
        addr.town ||
        addr.city ||
        addr.suburb ||
        addr.neighbourhood ||
        addr.municipality ||
        '';

      const district = addr.state_district || addr.district || addr.county || '';
      const state = addr.state || '';

      const parts = [locality, district, state].filter(Boolean);
      // Remove duplicate consecutive parts
      const uniqueParts = parts.filter((item, pos) => parts.indexOf(item) === pos);
      const formatted = uniqueParts.join(', ');

      return {
        resolvedName: formatted || data.display_name?.split(',').slice(0, 3).join(',').trim() || 'Location coordinates captured',
        details: {
          village: addr.village || addr.hamlet || null,
          town: addr.town || addr.city || null,
          district: district || null,
          state: state || null,
          country: addr.country || 'India',
          postcode: addr.postcode || null,
          latitude,
          longitude,
        },
      };
    }
  } catch (err) {
    console.warn('[REVERSE GEOCODE FALLBACK]', err);
  }

  return {
    resolvedName: 'Location coordinates captured',
    details: {
      latitude,
      longitude,
    },
  };
}

export default {
  reverseGeocodeCoords,
};
