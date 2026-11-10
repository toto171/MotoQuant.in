'use client';

/**
 * ConditionsLine — the ONE place that words "what air was this computed in?".
 *
 * Every result on the site (landing widget, simulator Simple + Advanced,
 * Upgrades, Race-day setup, bike pages) renders its conditions from the
 * `environment` block the server echoes with each result:
 *   { name, is_default, source: 'default'|'manual'|'venue', altitude_m,
 *     ambient_temp_c, track_temp_c, humidity_pct, pressure_hpa, headwind_kmh,
 *     track_surface }
 * so the pages can never disagree with what the engine really ran.
 *
 * Instant estimates computed in the browser have no server block: pass
 * `estimate={{ venueName, altitudeM }}` instead. The in-browser model knows
 * altitude only (a venue's, else the default site's) and was trained at the
 * server's default air temperature — weather is NOT part of it — so the line
 * says exactly that and never prints a temperature it did not use.
 */

// The server's default conditions (api.DEFAULT_CONDITIONS_NAME) — used ONLY to
// describe what the in-browser estimate assumes. Server results always carry
// their own numbers.
export const DEFAULT_ALTITUDE_M = 679;
export const DEFAULT_TEMP_C = 22;

const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
const rnd = (v) => Math.round(v);

/** Plain-words conditions for a server `environment` block (no "Conditions:" prefix). */
export function describeEnvironment(env, { placeLabel = null } = {}) {
  if (!env) return '';
  const alt = isNum(env.altitude_m) ? `${rnd(env.altitude_m)} m` : null;
  const tc = isNum(env.ambient_temp_c) ? env.ambient_temp_c : env.temperature_c; // autotune keeps its older key
  const temp = isNum(tc) ? `${rnd(tc)} °C` : null;
  const hum = isNum(env.humidity_pct) ? `${rnd(env.humidity_pct)} % humidity` : null;
  const wind =
    isNum(env.headwind_kmh) && Math.abs(env.headwind_kmh) >= 0.5
      ? `${Math.abs(rnd(env.headwind_kmh))} km/h ${env.headwind_kmh > 0 ? 'headwind' : 'tailwind'}`
      : null;

  if (env.is_default || env.source === 'default') {
    return `default (${[alt && `${alt} altitude`, temp].filter(Boolean).join(', ')})`;
  }
  if (env.source === 'venue') {
    // A venue sets altitude and surface; the numbers below are what the server ran.
    return `${env.name || 'your venue'} (${[alt && `${alt} altitude`, temp].filter(Boolean).join(', ')})`;
  }
  // manual
  if (placeLabel) {
    // The echoed block is what the engine ran: name the place and its altitude.
    return `${placeLabel} (${[alt && `${alt} altitude`, temp, hum, wind].filter(Boolean).join(', ')})`;
  }
  return `your custom values (${[alt && `${alt} altitude`, temp, hum, wind].filter(Boolean).join(', ')})`;
}

/** Plain words for what an in-browser instant estimate assumes. */
export function describeEstimate({ venueName = null, altitudeM = null } = {}) {
  if (venueName) {
    const alt = isNum(altitudeM) ? `, ${rnd(altitudeM)} m altitude` : '';
    return `${venueName}${alt} (the instant estimate uses the altitude only, not the weather)`;
  }
  return `default, ${DEFAULT_ALTITUDE_M} m altitude, ${DEFAULT_TEMP_C} °C (the instant estimate uses these defaults)`;
}

/**
 * Renders "Conditions: …" plus an optional "Change location" button.
 * Props: env | estimate | unreported, placeLabel, onChange, className, as ('p'|'span').
 */
export default function ConditionsLine({
  env = null,
  estimate = null,
  unreported = false,
  placeLabel = null,
  onChange = null,
  changeLabel = 'Change location',
  className = 'text-sm text-white/65',
  as: Tag = 'p',
}) {
  const text = env ? describeEnvironment(env, { placeLabel }) : estimate ? describeEstimate(estimate) : '';
  // An exact result whose response carried no conditions block: say so rather
  // than assert defaults the run may not have used.
  if (!text && unreported) {
    return <Tag className={className} data-conditions="unreported">Conditions not reported.</Tag>;
  }
  if (!text) return null;
  const isDefault = !!env?.is_default || (!env && !estimate?.venueName);
  return (
    <Tag className={className} data-conditions={isDefault ? 'default' : 'chosen'}>
      Conditions: {text}.
      {onChange && (
        <>
          {' '}
          <button
            type="button"
            onClick={onChange}
            className="font-medium text-accent underline underline-offset-2 hover:text-accent-bright"
          >
            {changeLabel}
          </button>
        </>
      )}
    </Tag>
  );
}
