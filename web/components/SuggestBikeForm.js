'use client';

import { useState, useEffect, useId } from 'react';
import { motion } from 'framer-motion';
import { X, ExternalLink, Mail } from 'lucide-react';

const REPO_URL = 'https://github.com/toto171/MotoQuant.in';
const CONTACT = 'motoquant@gmail.com';

// Field ids match .github/ISSUE_TEMPLATE/suggest-bike.yml, so GitHub fills
// the issue form from the query string.
const EMPTY_FORM = {
  make: '',
  model: '',
  year: '',
  displacement_cc: '',
  peak_power_hp: '',
  dry_mass_kg: '',
  category: '',
  source_url: '',
  notes: '',
};

const LABELS = {
  make: 'Make',
  model: 'Model',
  year: 'Year',
  displacement_cc: 'Engine size (cc)',
  peak_power_hp: 'Peak power (hp)',
  dry_mass_kg: 'Dry weight (kg)',
  category: 'Type of bike',
  source_url: 'Where the figures come from',
  notes: 'Notes',
};

function filled(form) {
  return Object.entries(form)
    .map(([k, v]) => [k, String(v ?? '').trim()])
    .filter(([, v]) => v);
}

/** A prefilled "Suggest a bike" issue on GitHub. */
export function suggestionIssueUrl(form) {
  const p = new URLSearchParams({ template: 'suggest-bike.yml' });
  p.set('title', `Add ${form.make.trim()} ${form.model.trim()}`.trim());
  for (const [k, v] of filled(form)) p.set(k, v);
  return `${REPO_URL}/issues/new?${p.toString()}`;
}

/** The same suggestion as an email, for riders without a GitHub account. */
export function suggestionMailto(form) {
  const body = filled(form)
    .map(([k, v]) => `${LABELS[k]}: ${v}`)
    .join('\n');
  const subject = `Add ${form.make.trim()} ${form.model.trim()} to MotoQuant`;
  return `mailto:${CONTACT}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

/**
 * "Suggest a bike". Suggestions are public GitHub issues, so anyone can see
 * what has been asked for and add sources; nothing is stored on our server.
 * The form only fills in the issue (or an email, for riders without GitHub).
 */
export default function SuggestBikeForm({ onClose }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose?.();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  function update(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
    setReady(false);
  }

  function handleSubmit(e) {
    e?.preventDefault?.();
    if (!form.make.trim() || !form.model.trim()) {
      setError('Make and model are needed.');
      return;
    }
    setError(null);
    setReady(true);
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="suggest-bike-title"
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
            <h2 id="suggest-bike-title" className="font-display font-bold tracking-tight text-2xl text-white">
              Suggest a bike
            </h2>
            <p className="text-sm text-white/65 mt-2">
              Missing your bike? Fill in what you know; only make and model are needed. A
              link to the manufacturer&apos;s specification sheet or a road test helps most.
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

        {ready ? (
          <div className="py-2">
            <p className="text-white/80">
              Suggestions are public issues on GitHub, where anyone can add sources and follow
              progress. Submit it there with a free GitHub account, or send it by email instead.
            </p>
            <div className="mt-6 flex flex-wrap justify-end gap-3">
              <button type="button" onClick={() => setReady(false)} className="btn-ghost">
                Edit
              </button>
              <a href={suggestionMailto(form)} className="btn-ghost">
                <Mail size={15} aria-hidden="true" /> Send by email
              </a>
              <a
                href={suggestionIssueUrl(form)}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary"
              >
                Open on GitHub <ExternalLink size={15} aria-hidden="true" />
              </a>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Field
                label="Make (required)"
                value={form.make}
                onChange={v => update('make', v)}
                placeholder="e.g. Suzuki"
                required
                maxLength={60}
              />
              <Field
                label="Model (required)"
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
                label="Engine size (cc)"
                value={form.displacement_cc}
                onChange={v => update('displacement_cc', v)}
                placeholder="e.g. 999"
                type="number"
                step="any"
                min={0}
              />
              <Field
                label="Peak power (hp)"
                value={form.peak_power_hp}
                onChange={v => update('peak_power_hp', v)}
                placeholder="e.g. 185"
                type="number"
                step="any"
                min={0}
              />
              <Field
                label="Dry weight (kg)"
                value={form.dry_mass_kg}
                onChange={v => update('dry_mass_kg', v)}
                placeholder="e.g. 172"
                type="number"
                step="any"
                min={0}
              />
            </div>

            <Field
              label="Type of bike"
              value={form.category}
              onChange={v => update('category', v)}
              placeholder="Sport, naked, cruiser, adventure…"
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

            <Field
              label="Where the figures come from (optional)"
              value={form.source_url}
              onChange={v => update('source_url', v)}
              placeholder="Link to a spec sheet or road test"
              type="url"
              maxLength={500}
            />

            {error && (
              <p role="alert" className="text-sm text-signal-foul">{error}</p>
            )}

            <div className="flex gap-3 justify-end pt-2">
              <button
                type="button"
                onClick={onClose}
                className="btn-ghost"
              >
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                Next
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
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="field-label">
        {label}
      </label>
      <Common
        id={id}
        value={value}
        onChange={e => onChange(e.target.value)}
        {...(as === 'textarea' ? { rows } : {})}
        className={`input-base ${as === 'textarea' ? 'h-auto py-2.5' : ''}`}
        {...rest}
      />
    </div>
  );
}
