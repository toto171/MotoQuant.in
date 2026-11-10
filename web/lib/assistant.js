// Assistant choice and the visitor's own Anthropic key, kept in the browser.
//
// The chat has two assistants (the server maps the id to a Claude model; the
// browser never sends a model id). A visitor may also bring their own
// Anthropic API key. It is kept only in this browser: sessionStorage by
// default, localStorage only when "Remember on this device" is ticked. It is
// sent as the X-Anthropic-Key header on the request that starts a chat, and
// the server uses it for that one request and never stores or logs it.
//
// This module imports nothing so the unit tests in scripts/lib.test.mjs can
// load it from its source text. Every storage call is wrapped in try/catch:
// private windows and blocked site data make storage throw or come back empty.

export const ASSISTANT_STORAGE_KEY = 'mq.assistant.v1';
export const KEY_STORAGE_KEY = 'mq.anthropic-key.v1';
export const ASSISTANT_EVENT = 'mq-assistant-changed';
export const KEY_HEADER = 'X-Anthropic-Key';
export const CONSOLE_KEYS_URL = 'https://console.anthropic.com/settings/keys';

export const DEFAULT_ASSISTANT = 'mechanic';

// Order is the order in the dropdown.
export const ASSISTANTS = [
  {
    id: 'doctor',
    label: '1. The doctor',
    name: 'The doctor',
    description: 'Claude Opus 5.5. Slower, digs deeper.',
  },
  {
    id: 'mechanic',
    label: '2. The mechanic',
    name: 'The mechanic',
    description: 'Claude Sonnet 5.5. Quick, practical answers.',
  },
];

export function normalizeAssistant(id) {
  return ASSISTANTS.some((a) => a.id === id) ? id : DEFAULT_ASSISTANT;
}

export function assistantInfo(id) {
  return ASSISTANTS.find((a) => a.id === normalizeAssistant(id));
}

// ── browser storage ──────────────────────────────────────────────────────────

// Returns {local, session}; either may be null when storage is unavailable.
export function browserStores() {
  const pick = (name) => {
    try {
      return typeof window !== 'undefined' && window[name] ? window[name] : null;
    } catch {
      return null;
    }
  };
  return { local: pick('localStorage'), session: pick('sessionStorage') };
}

function get(store, key) {
  try {
    return store ? store.getItem(key) : null;
  } catch {
    return null;
  }
}

function set(store, key, value) {
  try {
    if (!store) return false;
    store.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

function remove(store, key) {
  try {
    if (store) store.removeItem(key);
  } catch {
    /* nothing to do */
  }
}

export function readAssistant(local) {
  return normalizeAssistant(get(local, ASSISTANT_STORAGE_KEY));
}

export function saveAssistant(local, id) {
  return set(local, ASSISTANT_STORAGE_KEY, normalizeAssistant(id));
}

// ── the visitor's key ────────────────────────────────────────────────────────

export function cleanKey(raw) {
  return typeof raw === 'string' ? raw.trim() : '';
}

// The same rule the server applies: starts with sk-ant-, 20 to 300
// characters, every one printable ASCII (codes 33 to 126). That also rules
// out invisible characters a copy can pick up, such as a zero-width space,
// which the browser could not send in a header.
const KEY_RE = /^sk-ant-[\x21-\x7e]{13,293}$/;

export function looksLikeAnthropicKey(raw) {
  return KEY_RE.test(cleanKey(raw));
}

// {key, remember}: a key in localStorage was saved with "Remember on this
// device" ticked. Anything stored that does not look like a key is ignored.
export function readKey({ local, session } = {}) {
  const remembered = get(local, KEY_STORAGE_KEY);
  if (looksLikeAnthropicKey(remembered)) return { key: cleanKey(remembered), remember: true };
  const forSession = get(session, KEY_STORAGE_KEY);
  if (looksLikeAnthropicKey(forSession)) return { key: cleanKey(forSession), remember: false };
  return { key: '', remember: false };
}

// Saves the key in exactly one place and clears the other. Returns false when
// the key does not look valid or the browser refused to store it.
export function saveKey({ local, session } = {}, raw, remember = false) {
  const key = cleanKey(raw);
  if (!looksLikeAnthropicKey(key)) return false;
  if (remember) {
    const ok = set(local, KEY_STORAGE_KEY, key);
    if (ok) remove(session, KEY_STORAGE_KEY);
    return ok;
  }
  const ok = set(session, KEY_STORAGE_KEY, key);
  if (ok) remove(local, KEY_STORAGE_KEY);
  return ok;
}

export function removeKey({ local, session } = {}) {
  remove(local, KEY_STORAGE_KEY);
  remove(session, KEY_STORAGE_KEY);
}

// Headers for the request that starts a chat. Empty when there is no usable key.
export function keyHeaders(raw) {
  return looksLikeAnthropicKey(raw) ? { [KEY_HEADER]: cleanKey(raw) } : {};
}

// "sk-ant-…wxyz" so a visitor can tell which key is saved without showing it.
export function maskKey(raw) {
  const key = cleanKey(raw);
  if (!key) return '';
  return `sk-ant-…${key.slice(-4)}`;
}

// ── server info and errors ───────────────────────────────────────────────────

// Normalises GET /api/assistant. Returns null when the reply is unusable, so
// an older server simply shows no "free assistant" notice.
export function parseAssistantInfo(json) {
  if (!json || typeof json !== 'object' || typeof json.free_available !== 'boolean') return null;
  const limit = Number(json.daily_free_limit);
  return {
    freeAvailable: json.free_available,
    defaultAssistant: normalizeAssistant(json.default),
    dailyFreeLimit: Number.isFinite(limit) && limit > 0 ? limit : null,
  };
}

// Plain words for each error code the chat can return. `offerKey` means the
// banner offers to add (or change) the visitor's own key. `freeAvailable` is
// false when GET /api/assistant said the free assistant is off or resting.
export function chatErrorCopy(code, { ownKey = false, freeAvailable = true } = {}) {
  switch (code) {
    case 'assistant_unavailable':
    case 'llm_not_configured':
      return {
        tone: 'amber',
        offerKey: true,
        text: 'The free assistant is switched off on this server. Add your own Anthropic key to ask questions. The calculator and the other tools still work.',
      };
    case 'free_assistant_resting':
      return {
        tone: 'amber',
        offerKey: true,
        text: 'The free assistant has used up its budget for now. Add your own Anthropic key to keep asking, or try again later.',
      };
    case 'key_rejected':
      return {
        tone: 'red',
        offerKey: true,
        text: freeAvailable
          ? 'Anthropic did not accept your key. Check it in the Anthropic Console, or remove it to use the free assistant.'
          : 'Anthropic did not accept your key. Check it in the Anthropic Console.',
      };
    case 'invalid_key_format':
      return {
        tone: 'red',
        offerKey: true,
        text: 'That does not look like an Anthropic API key. Keys start with sk-ant-.',
      };
    case 'rate_limited':
      return {
        tone: 'amber',
        offerKey: false,
        text: ownKey
          ? 'Anthropic is limiting requests on your key right now. Please try again in a minute.'
          : 'Too many questions at once. Please try again in a minute.',
      };
    case 'refused':
      return {
        tone: 'amber',
        offerKey: false,
        text: 'The assistant would not answer that. Try asking about a bike, a part or a run.',
      };
    case 'agent_failed':
      return {
        tone: 'red',
        offerKey: false,
        text: 'Something went wrong while answering. Please try again.',
      };
    default:
      return null;
  }
}

// Turns a failed request (network error, HTTP 429 from a rate limit, job
// error) into one plain sentence. The daily limit only applies to the free
// assistant, so that message offers the visitor's own key.
export function describeChatFailure(err) {
  const raw = (err && err.message) || '';
  let detail = null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') detail = parsed;
  } catch {
    /* plain-text message */
  }
  if (err && err.status === 429) {
    const retry = Number(detail && detail.retry_after_s);
    const daily = /day/i.test((detail && detail.message) || raw) || retry > 3600;
    if (daily) {
      return {
        text: 'You have used today’s free questions. Add your own Anthropic key to keep asking, or come back tomorrow.',
        offerKey: true,
      };
    }
    if (detail) {
      return { text: 'Too many questions at once. Please try again in a minute.', offerKey: false };
    }
    return { text: raw || 'The server is busy. Please try again in a minute.', offerKey: false };
  }
  if (detail && typeof detail.message === 'string') return { text: detail.message, offerKey: false };
  return { text: raw || 'Request failed. Please try again.', offerKey: false };
}
