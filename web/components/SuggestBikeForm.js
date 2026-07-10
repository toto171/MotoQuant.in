'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { X, Check, AlertCircle, Info } from 'lucide-react';
import { API_URL } from '../lib/api';
import useAsyncTask from '../lib/useAsyncTask';
import ActionButton from './ActionButton';

const EMPTY_FORM = {
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
};

/**
 * Modal form for submitting a "please add this bike" request.
 * POSTs to /api/bikes/suggest; handles plausibility-flag responses gracefully.
 * Submission runs through useAsyncTask + ActionButton (staged progress —
 * the button is the bar) per the progress doctrine.
 */
export default function SuggestBikeForm({ onClose }) {
  const [form, setForm] = useState(EMPTY_FORM);

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

  const submitTask = useAsyncTask(async (signal) => {
    if (!form.make.trim() || !form.model.trim()) {
      throw new Error('Make and model are required.');
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

    const res = await fetch(`${API_URL}/api/bikes/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
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
    return res.json(); // {id, flagged_out_of_bounds, issues}
  });

  const result = submitTask.result;

  function handleSubmit(e) {
    e?.preventDefault?.();
    if (!submitTask.active) submitTask.run();
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 bg-asphalt-0/85 backdrop-blur-sm z-[100] flex items-start justify-center p-4 overflow-y-auto"
    >
      <motion.div
        initial={{ scale: 0.95, y: 20, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.95, y: 20, opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={e => e.stopPropagation()}
        className="card w-full max-w-xl rounded-2xl bg-asphalt-1 p-6 sm:p-8 my-10"
      >
        <div className="flex items-start justify-between mb-5">
          <div>
            <h2 className="font-display font-bold uppercase leading-[0.95] tracking-[-0.01em] text-2xl text-white">
              Suggest a bike
            </h2>
            <p className="text-sm text-white/65 mt-2">
              Don&apos;t see your bike? Tell us what to add next. Required fields marked *.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 -mt-1 -mr-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-white/60 hover:text-white transition-colors"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {result ? (
          <div className="py-2">
            <div className="card border-signal-go/30 bg-signal-go/[0.06] p-4 flex items-start gap-3">
              <Check className="text-signal-go shrink-0 mt-0.5" size={20} />
              <div>
                <p className="font-semibold text-signal-go">
                  Submission <span className="font-mono tabular-nums">#{result.id}</span> received.
                </p>
                <p className="text-sm text-white/65 mt-1">
                  Thanks — we&apos;ll review and add it to the catalog soon.
                </p>
                {result.flagged_out_of_bounds && result.issues?.length > 0 && (
                  <div className="card border-signal-stage/30 bg-signal-stage/[0.08] mt-3 p-3 text-xs font-mono text-signal-stage">
                    <p className="flex items-center gap-1 mb-1 font-semibold">
                      <Info size={14} /> Flagged for manual review
                    </p>
                    <ul className="list-disc list-inside space-y-0.5 text-signal-stage/80">
                      {result.issues.map((msg, i) => <li key={i}>{msg}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-3 justify-end mt-6">
              <button
                type="button"
                onClick={() => { submitTask.reset(); setForm(EMPTY_FORM); }}
                className="btn-ghost"
              >
                Submit another
              </button>
              <button
                type="button"
                onClick={onClose}
                className="btn-primary"
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

            {submitTask.error && (
              <div className="card border-signal-foul/40 bg-signal-foul/[0.08] p-3 text-signal-foul text-sm flex items-center gap-2">
                <AlertCircle size={16} className="shrink-0" /> {submitTask.error}
              </div>
            )}

            {/* Hidden sentinel keeps Enter-in-field implicit submission working
                even though the visible submit control is an ActionButton. */}
            <button type="submit" className="hidden" tabIndex={-1} aria-hidden="true" />

            <div className="flex gap-3 justify-end pt-2">
              <button
                type="button"
                onClick={onClose}
                className="btn-ghost"
              >
                Cancel
              </button>
              <ActionButton
                task={submitTask}
                onRun={handleSubmit}
                label="Submit suggestion"
                runningLabel="Submitting"
              />
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
      <span className="label-mono block mb-1.5">
        {label}
      </span>
      <Common
        value={value}
        onChange={e => onChange(e.target.value)}
        {...(as === 'textarea' ? { rows } : {})}
        className={`input-base font-mono ${as === 'textarea' ? 'h-auto py-2.5' : ''}`}
        {...rest}
      />
    </label>
  );
}
