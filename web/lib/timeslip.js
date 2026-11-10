/**
 * Plain-language lines for a timeslip: the conditions a run was simulated in
 * and everything that differs from a stock bike. Shared by the on-screen slip,
 * the printed slip and the "Your runs" list, so all three say the same thing.
 */

function fmt(n, digits = 0) {
  return Number(n).toLocaleString('en-IN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/**
 * One line describing the air and track, from the API's ``environment`` echo.
 * Example: "Aamby Valley Airstrip · 679 m · 22 °C air · 29 °C track · 40 % humidity"
 */
export function conditionsSummary(env) {
  if (!env) return 'Conditions were not recorded for this run';
  const bits = [];
  if (env.source === 'venue' && env.name) bits.push(env.name);
  if (Number.isFinite(env.altitude_m)) bits.push(`${fmt(env.altitude_m)} m`);
  if (Number.isFinite(env.ambient_temp_c)) bits.push(`${fmt(env.ambient_temp_c)} °C air`);
  if (Number.isFinite(env.track_temp_c)) bits.push(`${fmt(env.track_temp_c)} °C track`);
  if (Number.isFinite(env.humidity_pct)) bits.push(`${fmt(env.humidity_pct)} % humidity`);
  if (Number.isFinite(env.headwind_kmh) && Math.abs(env.headwind_kmh) >= 0.5) {
    bits.push(
      env.headwind_kmh > 0
        ? `${fmt(env.headwind_kmh)} km/h headwind`
        : `${fmt(-env.headwind_kmh)} km/h tailwind`,
    );
  }
  if (env.track_surface && env.track_surface !== 'asphalt') {
    bits.push(String(env.track_surface).replace(/_/g, ' '));
  }
  return bits.join(' · ');
}

/**
 * Everything that differs from the stock bike, as short lines. Rider weight
 * is not a change to the bike: the slip states it in its headline instead,
 * so a stock bike with a heavier rider is still "stock" everywhere. ``request`` is the body that was simulated; ``result`` is the quick
 * simulation response (its ``parts_applied`` and ``tyres`` name what was
 * actually fitted).
 */
export function changesFromStock(request, result) {
  const out = [];
  const boost = Number(request?.power_boost_pct || 0);
  const mass = Number(request?.mass_delta_kg || 0);
  if (boost) out.push(`Engine power ${boost > 0 ? '+' : '−'}${fmt(Math.abs(boost))} %`);
  if (mass) out.push(`Bike weight ${mass > 0 ? '+' : '−'}${fmt(Math.abs(mass))} kg`);
  for (const p of result?.parts_applied || []) {
    const name = [p.brand, p.name].filter(Boolean).join(' ');
    if (name) out.push(name);
  }
  for (const t of result?.tyres || []) {
    out.push(`${t.position === 'front' ? 'Front' : 'Rear'} tyre: ${t.name}`);
  }
  return out;
}
