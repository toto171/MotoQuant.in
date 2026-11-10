'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { MessageSquare } from 'lucide-react';
import { API_URL } from '../../lib/api';

// The chat (and its block renderers) loads only once someone opens it (F10).
const ChatPanel = dynamic(() => import('../ChatPanel'), {
  ssr: false,
  loading: () => <div aria-hidden="true" className="skeleton mt-3 h-24 w-full" />,
});

/**
 * AskPanel — "Ask in plain English": collapsed to a single input-looking row
 * under the page header; expands in place to the full chat when used.
 */
export default function AskPanel() {
  const [open, setOpen] = useState(false);
  return (
    <section className="card" aria-label="Ask in plain English">
      {!open ? (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-expanded="false"
          className="flex min-h-12 w-full items-center gap-3 rounded-2xl px-4 py-3 text-left hover:bg-white/[0.03]"
        >
          <MessageSquare size={18} aria-hidden="true" className="shrink-0 text-accent" />
          <span className="min-w-0">
            <span className="block text-sm font-semibold text-white">Ask in plain English</span>
            <span className="block truncate text-sm text-white/60">
              Ask anything, e.g. “How fast is a Duke 390 at Aamby Valley?”
            </span>
          </span>
        </button>
      ) : (
        <div className="p-4 md:p-5">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="flex items-center gap-2 font-display text-lg font-semibold text-white">
              <MessageSquare size={18} aria-hidden="true" className="text-accent" />
              Ask in plain English
            </h2>
            <button type="button" onClick={() => setOpen(false)} className="btn-ghost btn-sm">Close</button>
          </div>
          <ChatPanel apiUrl={API_URL} />
        </div>
      )}
    </section>
  );
}
