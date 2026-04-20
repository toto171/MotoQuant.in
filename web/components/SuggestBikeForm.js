'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Check, AlertCircle, Info } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://motoquant-api.railway.app';

/**
 * Modal form for submitting a "please add this bike" request.
 * POSTs to /api/bikes/suggest; handles plausibility-flag responses gracefully.
 */
export default function SuggestBikeForm({ onClose }) {
  const [form, setForm] = useState({
    make: '',
    model: '',
    year: '',
    displacement_cc: '',
    peak_power_hp: '',
    dry_mass_kg: '',
    category: '',
    notes: '',
    submitter_email: '',
    source_url: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null); // {id, flagged_out_of_bounds, issues}
  const [error, setError] = useState(null);

  // Close on ESC
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  function update(k, v) {
    setForm(f => ({ ...f, [k]: v }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!form.make.trim() || !form.model.trim()) {
      setError('Make and model are required.');
      return;
    }

    const body = {
      make: form.make.trim(),
      model: form.model.trim(),
    };
    // Only include optional fields if user filled them in
    const num = (k) => {
      const v = form[k];
      if (v === '' || v === null || v === undefined) return undefined;
      const n = Number(v);
      return Number.isFinite(n) ? n : undefined;
    };
    const str = (k) => {
      const v = form[k];
      return v && v.trim() ? v.trim() : undefined;
    };

    const year = num('year');
    if (year !== undefined) body.year = year;
    const disp = num('displacement_cc');
    if (disp !== undefined) body.displacement_cc = disp;
    const pwr = num('peak_power_hp');
    if (pwr !== undefined) body.peak_power_hp = pwr;
    const mass = num('dry_mass_kg');
    if (mass !== undefined) body.dry_mass_kg = mass;
    const cat = str('category');
    if (cat) body.category = cat;
    const notes = str('notes');
    if (notes) body.notes = notes;
    const email = str('submitter_email');
    if (email) body.submitter_email = email;
    const url = str('source_url');
    if (url) body.source_url = url;

    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/api/bikes/suggest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        let msg = `API error ${res.status}`;
        try {
          const j = await res.json();
          if (j?.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
        } catch {
          try { msg = await res.text(); } catch {}
        }
        throw new Error(msg);
      }
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(e.message || 'Failed to submit');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-start justify-center p-4 overflow-y-auto"
    >
      <motion.div
        initial={{ scale: 0.95, y: 20, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.95, y: 20, opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={e => e.stopPropagation()}
        className="w-full max-w-xl glass border border-brand-orange/30 rounded-2xl p-6 sm:p-8 my-10 bg-ink-0/95"
      >
        <div className="flex items-start justify-between mb-5">
          <div>
            <h2 className="font-display font-bold text-2xl text-white">Suggest a Bike</h2>
            <p className="text-sm text-white/60 mt-1">
              Don't see your bike? Tell us what to add next. Required fields marked *.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 -mt-1 -mr-2 text-white/60 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {result ? (
          <div className="py-4">
            <div className="flex items-start gap-3 p-4 rounded-lg bg-brand-accent/10 border border-brand-accent/30">
              <Check className="text-brand-accent shrink-0 mt-0.5" size={20} />
              <div>
                <p className="font-display font-semibold text-brand-accent">
                  Submission #{result.id} received.
                </p>
                <p className="text-sm text-white/70 mt-1">
                  Thanks — we'll review and add it to the catalog soon.
                </p>
                {result.flagged_out_of_bounds && result.issues?.length > 0 && (
                  <div className="mt-3 p-3 rounded bg-amber-500/10 border border-amber-500/30 text-xs font-mono text-amber-200">
                    <p className="flex items-center gap-1 mb-1 font-semibold">
                      <Info size={14} /> Flagged for manual review
                    </p>
                    <ul className="list-disc list-inside space-y-0.5 text-amber-200/80">
                      {result.issues.map((msg, i) => <li key={i}>{msg}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-3 justify-end mt-6">
              <button
                onClick={() => { setResult(null); setForm({
                  make: '', model: '', year: '', displacement_cc: '', peak_power_hp: '',
                  dry_mass_kg: '', category: '', notes: '', submitter_email: '', source_url: '',
                }); }}
                className="px-4 py-2 border border-white/15 hover:border-white/40 rounded-lg text-sm text-white/80 font-mono transition-colors"
              >
                Submit another
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-brand-orange hover:bg-brand-orangeLight text-black rounded-lg font-display font-semibold text-sm transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Field
                label="Make *"
                value={form.make}
                onChange={v => update('make', v)}
                placeholder="e.g. Suzuki"
                required
                maxLength={60}
              />
              <Field
                label="Model *"
                value={form.model}
                onChange={v => update('model', v)}
                placeholder="e.g. GSX-R 1000 K9"
                required
                maxLength={80}
              />
              <Field
                label="Year"
                value={form.year}
                onChange={v => update('year', v)}
                placeholder="e.g. 2009"
                type="number"
                min={1960} max={2099}
              />
              <Field
                label="Displacement (cc)"
                value={form.displacement_cc}
                onChange={v => update('displacement_cc', v)}
                placeholder="e.g. 999"
                type="number"
                step="any"
                min={0}
              />
              <Field
                label="Peak Power (hp)"
                value={form.peak_power_hp}
                onChange={v => update('peak_power_hp', v)}
                placeholder="e.g. 185"
                type="number"
                step="any"
                min={0}
              />
              <Field
                label="Dry Mass (kg)"
                value={form.dry_mass_kg}
                onChange={v => update('dry_mass_kg', v)}
                placeholder="e.g. 172"
                type="number"
                step="any"
                min={0}
              />
            </div>

            <Field
              label="Category"
              value={form.category}
              onChange={v => update('category', v)}
              placeholder="sport, naked, cruiser, adventure…"
              maxLength={40}
            />

            <Field
              label="Notes"
              value={form.notes}
              onChange={v => update('notes', v)}
              placeholder="Anything else we should know (special tune, spec variant, etc.)"
              as="textarea"
              rows={3}
              maxLength={1000}
            />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field
                label="Your email (optional)"
                value={form.submitter_email}
                onChange={v => update('submitter_email', v)}
                placeholder="So we can follow up"
                type="email"
                maxLength={200}
              />
              <Field
                label="Source URL (optional)"
                value={form.source_url}
                onChange={v => update('source_url', v)}
                placeholder="Link to specs"
                type="url"
                maxLength={500}
              />
            </div>

            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center gap-2">
                <AlertCircle size={16} /> {error}
              </div>
            )}

            <div className="flex gap-3 justify-end pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-white/15 hover:border-white/40 rounded-lg text-sm text-white/80 font-mono transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-5 py-2 bg-brand-orange hover:bg-brand-orangeLight disabled:opacity-50 disabled:cursor-not-allowed text-black rounded-lg font-display font-semibold text-sm transition-colors"
              >
                {submitting ? 'Submitting…' : 'Submit suggestion'}
              </button>
            </div>
          </form>
        )}
      </motion.div>
    </motion.div>
  );
}

function Field({ label, value, onChange, as = 'input', rows = 3, ...rest }) {
  const Common = as === 'textarea' ? 'textarea' : 'input';
  return (
    <label className="block">
      <span className="block text-[11px] font-mono text-white/60 uppercase tracking-wider mb-1.5">
        {label}
      </span>
      <Common
        value={value}
        onChange={e => onChange(e.target.value)}
        {...(as === 'textarea' ? { rows } : {})}
        className="w-full px-3 py-2 bg-black/40 border border-white/10 rounded-lg text-sm text-white placeholder:text-white/30 focus:border-brand-orange focus:outline-none font-mono"
        {...rest}
      />
    </label>
  );
}
