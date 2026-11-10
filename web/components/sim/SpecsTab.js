'use client';

import { PANEL } from './controls';
import { bikeName, isNum } from './format';
import { describeEstimate } from '../ConditionsLine';

function Rows({ rows }) {
  return (
    <div>
      {rows.filter((r) => r[1] != null && r[1] !== '').map(([k, v]) => (
        <div className="stat-row" key={k}><span>{k}</span><span>{v}</span></div>
      ))}
    </div>
  );
}

export default function SpecsTab({ sim }) {
  const {
    bike, headline, fullRes, riderKg, powerBoost, massChange, frontTire, rearTire, selectedParts,
  } = sim;
  // The conditions the latest result was REALLY computed under (server echo).
  const env = (fullRes || headline)?.environment ?? null;
  const cfg = fullRes?.config;
  const hp = cfg?.peak_power_hp ?? headline?.peak_power_hp;
  const mass = cfg?.total_mass_kg ?? headline?.total_mass_kg;

  if (!bike || !(cfg || headline)) {
    return <p className="py-8 text-center text-sm text-white/65">Choose a bike to see the numbers behind its result.</p>;
  }

  const tyre = (t) => (t ? `${t.manufacturer} ${t.model}` : 'Original');
  return (
    <div className="space-y-4">
      <div className={PANEL}>
        <h3 className="mb-1 font-display text-base font-semibold text-white">Your setup</h3>
        <Rows
          rows={[
            ['Bike', headline?.bike_name || bikeName(bike)],
            ['Peak power', hp != null ? `${hp.toFixed(1)} hp` : null],
            ['Peak torque', cfg?.peak_torque_nm != null ? `${cfg.peak_torque_nm.toFixed(1)} Nm` : null],
            ['Total weight with rider', mass != null ? `${mass.toFixed(1)} kg` : null],
            ['Engine size', (cfg?.displacement_cc || bike.displacement_cc) ? `${cfg?.displacement_cc || bike.displacement_cc} cc` : null],
            ['Redline', cfg?.redline_rpm != null ? `${cfg.redline_rpm.toFixed(0)} rpm` : null],
            ['Drag coefficient', cfg?.cd != null ? String(cfg.cd) : null],
            ['Rider weight', `${riderKg} kg`],
            ['Engine power change', powerBoost !== 0 ? `${powerBoost > 0 ? '+' : ''}${powerBoost} %` : 'Stock'],
            ['Weight change', massChange !== 0 ? `${massChange > 0 ? '+' : ''}${massChange} kg` : 'Stock'],
            ['Parts added', selectedParts.length ? String(selectedParts.length) : 'None'],
          ]}
        />
      </div>
      <div className={PANEL}>
        <h3 className="mb-1 font-display text-base font-semibold text-white">Conditions</h3>
        <Rows
          rows={[
            ['Place', env ? (env.is_default ? 'Default conditions' : env.name) : headline?.estimateAssumes ? describeEstimate(headline.estimateAssumes) : null],
            ['Altitude', isNum(env?.altitude_m) ? `${Math.round(env.altitude_m)} m` : null],
            ['Air temperature', isNum(env?.ambient_temp_c) ? `${Math.round(env.ambient_temp_c)} °C` : null],
            ['Track temperature', isNum(env?.track_temp_c) ? `${Math.round(env.track_temp_c)} °C` : null],
            ['Humidity', isNum(env?.humidity_pct) ? `${Math.round(env.humidity_pct)} %` : null],
            ['Wind', !env ? null : Math.abs(env.headwind_kmh || 0) < 0.5 ? 'None' : `${env.headwind_kmh > 0 ? 'Headwind' : 'Tailwind'} ${Math.abs(Math.round(env.headwind_kmh))} km/h`],
            ['Front tyre', tyre(frontTire)],
            ['Rear tyre', tyre(rearTire)],
          ]}
        />
      </div>
    </div>
  );
}
