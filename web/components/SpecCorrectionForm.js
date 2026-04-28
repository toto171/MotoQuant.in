'use client';

/**
 * SpecCorrectionForm
 * ==================
 * Modal form that lets Indian forum users and verified tuners propose
 * corrections to a single spec field on a bike model.
 *
 * Usage:
 *   <SpecCorrectionForm
 *     bikeId={42}
 *     bikeName="Yamaha YZF-R15 V4"
 *     isOpen={showForm}
 *     onClose={() => setShowForm(false)}
 *     currentValues={{ peak_power_hp: '18.4', dry_mass_kg: '142' }}
 *   />
 */

import { useState, useEffect } from 'react';
import { X, Send, CheckCircle, AlertCircle, ChevronDown } from 'lucide-react';
import { API_URL } from '../lib/api';

// ── Field catalogue (must mirror VALID_CORRECTION_FIELDS in spec_corrections_repo.py)
const FIELD_OPTIONS = [
  { value: 'peak_power_hp',      label: 'Peak Power (hp)' },
  { value: 'peak_torque_nm',     label: 'Peak Torque (Nm)' },
  { value: 'peak_power_rpm',     label: 'Peak Power RPM' },
  { value: 'peak_torque_rpm',    label: 'Peak Torque RPM' },
  { value: 'displacement_cc',    label: 'Displacement (cc)' },
  { value: 'bore_mm',            label: 'Bore (mm)' },
  { value: 'stroke_mm',          label: 'Stroke (mm)' },
  { value: 'compression_ratio',  label: 'Compression Ratio' },
  { value: 'dry_mass_kg',        label: 'Dry Mass (kg)' },
  { value: 'wet_mass_kg',        label: 'Wet Mass (kg)' },
  { value: 'cylinder_count',     label: 'Cylinder Count' },
  { value: 'wheelbase_mm',       label: 'Wheelbase (mm)' },
  { value: 'seat_height_mm',     label: 'Seat Height (mm)' },
  { value: 'fuel_capacity_l',    label: 'Fuel Capacity (L)' },
  { value: 'front_sprocket',     label: 'Front Sprocket (teeth)' },
  { value: 'rear_sprocket',      label: 'Rear Sprocket (teeth)' },
  { value: 'gear_ratios',        label: 'Gear Ratios (JSON list)' },
  { value: 'redline_rpm',        label: 'Redline (rpm)' },
  { value: 'cd',                 label: 'Drag Coefficient (Cd)' },
  { value: 'frontal_area_m2',    label: 'Frontal Area (m²)' },
  { value: 'data_source',        label: 'Data Source' },
];

const DATA_SOURCE_VALUES = [
  'verified_service_manual',
  'magazine_test',
  'estimated',
  'user_submitted_pending',
  'user_submitted_verified',
];

const EMPTY_FORM = {
  field_name: '',
  proposed_value: '',
  source_url: '',
  submitter_email: '',
  notes: '',
};

export default function SpecCorrectionForm({
  bikeId,
  bikeName,
  isOpen,
  onClose,
  currentValues = {},
}) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [status, setStatus] = useState('idle'); // 'idle' | 'submitting' | 'success' | 'error'
  const [errorMsg, setErrorMsg] = useState('');
  const [successId, setSuccessId] = useState(null);

  // Auto-fill proposed_value with the current value when field_name changes
  useEffect(() => {
    if (form.field_name && currentValues[form.field_name] != null) {
      setForm(f => ({
        ...f,
        proposed_value: String(currentValues[form.field_name]),
      }));
    }
  }, [form.field_name]); // eslint-disable-line react-hooks/exhaustive-deps

  // Reset on open
  useEffect(() => {
    if (isOpen) {
      setForm(EMPTY_FORM);
      setStatus('idle');
      setErrorMsg('');
      setSuccessId(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const set = (key, value) => setForm(f => ({ ...f, [key]: value }));

  const currentValueDisplay =
    form.field_name && currentValues[form.field_name] != null
      ? String(currentValues[form.field_name])
      : null;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.field_name || !form.proposed_value.trim()) return;

    setStatus('submitting');
    setErrorMsg('');

    try {
      const res = await fetch(`${API_URL}/api/specs/correct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bike_id: bikeId,
          field_name: form.field_name,
          proposed_value: form.proposed_value.trim(),
          source_url: form.source_url.trim() || null,
          submitter_email: form.submitter_email.trim() || null,
          notes: form.notes.trim() || null,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
      }

      setSuccessId(data.id);
      setStatus('success');
    } catch (err) {
      setErrorMsg(err.message || 'Failed to submit correction');
      setStatus('error');
    }
  }

  return (
    /* Backdrop */
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="spec-correction-title"
    >
      {/* Dimmer */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div className="relative z-10 w-full max-w-lg bg-[#0e0e0e] border border-white/10 rounded-2xl shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-white/10">
          <div>
            <h2
              id="spec-correction-title"
              className="font-display font-bold text-white text-lg leading-snug"
            >
              Submit a spec correction
            </h2>
            <p className="mt-1 text-xs font-mono text-white/50 truncate">
              {bikeName}
            </p>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5">
          {status === 'success' ? (
            <div className="py-6 flex flex-col items-center text-center gap-3">
              <CheckCircle size={40} className="text-green-400" />
              <p className="font-display font-semibold text-white text-base">
                Correction submitted!
              </p>
              <p className="text-sm text-white/60 font-mono">
                Logged as correction #{successId}. Our team will review it
                before applying it to the catalog.
              </p>
              <button
                onClick={onClose}
                className="mt-2 px-5 py-2 bg-brand-orange text-black font-display font-bold rounded-lg text-sm"
              >
                Close
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              {/* Field selector */}
              <div>
                <label className="block text-xs font-mono text-white/60 mb-1.5">
                  Field to correct <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <select
                    required
                    value={form.field_name}
                    onChange={e => set('field_name', e.target.value)}
                    className="w-full appearance-none bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-white focus:outline-none focus:border-brand-orange/60 pr-8"
                  >
                    <option value="" className="bg-[#0e0e0e]">— choose a field —</option>
                    {FIELD_OPTIONS.map(o => (
                      <option key={o.value} value={o.value} className="bg-[#0e0e0e]">
                        {o.label}
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    size={14}
                    className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-white/40"
                  />
                </div>
                {currentValueDisplay && (
                  <p className="mt-1 text-[11px] font-mono text-white/40">
                    Current value: <span className="text-brand-accent">{currentValueDisplay}</span>
                  </p>
                )}
              </div>

              {/* Proposed value */}
              <div>
                <label className="block text-xs font-mono text-white/60 mb-1.5">
                  Corrected value <span className="text-red-400">*</span>
                </label>
                {form.field_name === 'data_source' ? (
                  <div className="relative">
                    <select
                      required
                      value={form.proposed_value}
                      onChange={e => set('proposed_value', e.target.value)}
                      className="w-full appearance-none bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-white focus:outline-none focus:border-brand-orange/60 pr-8"
                    >
                      <option value="" className="bg-[#0e0e0e]">— choose —</option>
                      {DATA_SOURCE_VALUES.map(v => (
                        <option key={v} value={v} className="bg-[#0e0e0e]">{v}</option>
                      ))}
                    </select>
                    <ChevronDown
                      size={14}
                      className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-white/40"
                    />
                  </div>
                ) : (
                  <input
                    type="text"
                    required
                    placeholder={
                      form.field_name === 'gear_ratios'
                        ? 'e.g. [2.833, 1.875, 1.429, 1.160, 0.963, 0.840]'
                        : 'e.g. 18.4'
                    }
                    value={form.proposed_value}
                    onChange={e => set('proposed_value', e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-white placeholder-white/25 focus:outline-none focus:border-brand-orange/60"
                  />
                )}
              </div>

              {/* Source URL */}
              <div>
                <label className="block text-xs font-mono text-white/60 mb-1.5">
                  Source URL
                  <span className="ml-1 text-white/30">(optional but very helpful)</span>
                </label>
                <input
                  type="url"
                  placeholder="https://indianautomag.com/r15-dyno-test"
                  value={form.source_url}
                  onChange={e => set('source_url', e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-white/80 placeholder-white/25 focus:outline-none focus:border-brand-orange/60"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-mono text-white/60 mb-1.5">
                  Notes <span className="text-white/30">(optional)</span>
                </label>
                <textarea
                  rows={3}
                  placeholder="E.g. Indian Autos Mag wheel-dyno, stock bike, July 2024 issue"
                  value={form.notes}
                  onChange={e => set('notes', e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-white/80 placeholder-white/25 focus:outline-none focus:border-brand-orange/60 resize-none"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-mono text-white/60 mb-1.5">
                  Your email <span className="text-white/30">(optional)</span>
                </label>
                <input
                  type="email"
                  placeholder="rider@example.com"
                  value={form.submitter_email}
                  onChange={e => set('submitter_email', e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm font-mono text-white/80 placeholder-white/25 focus:outline-none focus:border-brand-orange/60"
                />
              </div>

              {/* Error */}
              {status === 'error' && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-xs font-mono">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  {errorMsg}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-1">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 px-4 py-2.5 border border-white/15 hover:border-white/30 text-white/70 hover:text-white font-display font-semibold rounded-lg text-sm transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!form.field_name || !form.proposed_value.trim() || status === 'submitting'}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-orange hover:bg-orange-500 disabled:opacity-40 disabled:cursor-not-allowed text-black font-display font-bold rounded-lg text-sm transition-colors"
                >
                  {status === 'submitting' ? (
                    <>
                      <span className="inline-block w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                      Submitting…
                    </>
                  ) : (
                    <>
                      <Send size={14} />
                      Submit correction
                    </>
                  )}
                </button>
              </div>

              <p className="text-[10px] font-mono text-white/30 leading-relaxed">
                Corrections are stored as pending and reviewed by the MotoQuant team before
                being applied to the live catalog. Please include a source URL where possible.
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
