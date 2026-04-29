#!/usr/bin/env node
/**
 * verify-web.mjs — pre-build sanity sweep for the MotoQuant web/ tree.
 *
 * Catches the three failure modes we have hit repeatedly this session:
 *
 *   1. NULL BYTES in source files. Caused by FUSE mount tail-padding.
 *      SWC rejects these as garbage but the error message is opaque.
 *      We catch them up-front with a clean message naming the file.
 *
 *   2. MID-TOKEN TRUNCATION. The Cowork Write/Edit tool occasionally
 *      truncates files at ~5-6 KB when rewriting. The result is a file
 *      whose last non-whitespace character is mid-attribute or mid-tag.
 *      Every JS module ends with } or ) — anything else means truncation.
 *
 *   3. BRACE IMBALANCE >4. Crude regex-strips strings/comments and
 *      counts {}, [], (). Real JSX with className interpolation can
 *      drift by 1–2 from naive counting, so we only flag stark
 *      imbalances.
 *
 * Designed to run in <500 ms on the full app/ + components/ tree.
 *
 * Exit codes:
 *   0  every file is structurally sound
 *   1  one or more files failed validation
 *
 * Run: npm run verify
 *
 * Wired in two places:
 *   - prebuild  (runs before every `next build`)
 *   - .github/workflows/web-verify.yml  (CI gate on every PR)
 *
 * No external dependencies — pure Node.js stdlib so it cannot itself
 * be broken by a half-installed node_modules.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import process from 'node:process';

const CYAN  = '\x1b[36m';
const RED   = '\x1b[31m';
const GREEN = '\x1b[32m';
const DIM   = '\x1b[2m';
const RESET = '\x1b[0m';

const ROOT = process.cwd();
const SCAN_ROOTS = ['app', 'components', 'lib'];
const JS_EXT = /\.(jsx?|tsx?|mjs|cjs)$/;
const ALLOW_OTHER_ENDING = new Set([]);

function walk(dir, out) {
  out = out || [];
  let entries;
  try {
    entries = readdirSync(dir);
  } catch (e) {
    return out;
  }
  for (const name of entries) {
    if (name === 'node_modules' || name === '.next' || name.startsWith('.')) continue;
    const full = join(dir, name);
    let st;
    try { st = statSync(full); } catch (e) { continue; }
    if (st.isDirectory()) walk(full, out);
    else if (JS_EXT.test(name)) out.push(full);
  }
  return out;
}

function stripComments(s) {
  s = s.replace(/\/\/[^\n]*/g, '');
  s = s.replace(/\/\*[\s\S]*?\*\//g, '');
  s = s.replace(/`(?:[^`\\]|\\.)*`/g, '""');
  s = s.replace(/'(?:[^'\\]|\\.)*'/g, '""');
  s = s.replace(/"(?:[^"\\]|\\.)*"/g, '""');
  return s;
}

function checkFile(path) {
  let raw;
  try {
    raw = readFileSync(path);
  } catch (e) {
    return { ok: false, reason: 'READ FAIL: ' + e.message };
  }

  if (raw.indexOf(0) !== -1) {
    return {
      ok: false,
      reason: 'contains NULL bytes (FUSE / file-write corruption). Rewrite from a clean source.',
    };
  }

  const text = raw.toString('utf8').replace(/\s+$/, '');
  if (text.length === 0) {
    return { ok: false, reason: 'empty file' };
  }
  const lastChar = text[text.length - 1];
  if (lastChar !== '}' && lastChar !== ')' && lastChar !== ';') {
    if (!ALLOW_OTHER_ENDING.has(relative(ROOT, path))) {
      const tail = text.slice(-50).replace(/\n/g, '\\n');
      return {
        ok: false,
        reason: 'TRUNCATED — ends with ' + JSON.stringify(lastChar) +
                '; tail: ' + JSON.stringify(tail),
      };
    }
  }

  const stripped = stripComments(text);
  const counts = { '{': 0, '}': 0, '[': 0, ']': 0, '(': 0, ')': 0 };
  for (const ch of stripped) {
    if (ch in counts) counts[ch]++;
  }
  const skewC = counts['{'] - counts['}'];
  const skewS = counts['['] - counts[']'];
  const skewP = counts['('] - counts[')'];
  if (Math.abs(skewC) > 4 || Math.abs(skewS) > 4 || Math.abs(skewP) > 4) {
    return {
      ok: false,
      reason: 'brace imbalance: { skew=' + skewC + ', [ skew=' + skewS + ', ( skew=' + skewP,
    };
  }

  return { ok: true };
}

function main() {
  const startedAt = Date.now();
  const allFiles = [];
  for (const root of SCAN_ROOTS) {
    const abs = join(ROOT, root);
    try {
      if (statSync(abs).isDirectory()) walk(abs, allFiles);
    } catch (e) {}
  }

  if (allFiles.length === 0) {
    console.error(RED + 'verify-web: no source files found under ' + SCAN_ROOTS.join(', ') + RESET);
    process.exit(2);
  }

  let failed = 0;
  const problems = [];
  for (const f of allFiles) {
    const result = checkFile(f);
    if (!result.ok) {
      failed++;
      problems.push({ path: relative(ROOT, f), reason: result.reason });
    }
  }

  const ms = Date.now() - startedAt;
  if (failed === 0) {
    console.log(GREEN + 'verify-web: all ' + allFiles.length +
                ' files clean ' + DIM + '(' + ms + 'ms)' + RESET);
    process.exit(0);
  }

  console.error(RED + 'verify-web: ' + failed + ' file(s) failed integrity check' + RESET + '\n');
  for (const p of problems) {
    console.error('  ' + RED + 'X' + RESET + ' ' + CYAN + p.path + RESET);
    console.error('      ' + p.reason);
  }

  const reasons = problems.map(function (p) { return p.reason; }).join(' | ');
  if (reasons.indexOf('NULL') !== -1) {
    console.error('\n' + DIM + 'Hint: null bytes are FUSE-mount artefacts. ' +
                  'Re-write the affected file from a clean source.' + RESET);
  }
  if (reasons.indexOf('TRUNCATED') !== -1) {
    console.error('\n' + DIM + 'Hint: file got truncated by the Cowork Write/Edit tool. ' +
                  'Rewrite via bash heredoc or Python instead.' + RESET);
  }
  console.error(DIM + '\nThis check ran in ' + ms +
                'ms. Catching these locally is ~10000x cheaper than a failed Vercel deploy.' + RESET);
  process.exit(1);
}

main();
