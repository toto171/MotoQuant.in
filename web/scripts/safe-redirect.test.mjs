// Unit test for lib/safeRedirect.js — run: node web/scripts/safe-redirect.test.mjs
import { readFileSync } from 'node:fs';
const src = readFileSync(new URL('../lib/safeRedirect.js', import.meta.url), 'utf8');
const { safeNextPath } = await import('data:text/javascript;base64,' + Buffer.from(src).toString('base64'));
const O = 'https://www.motoquant.in';
let bad = 0;
const must = (name, cond) => { if (!cond) { bad++; console.log('FAIL', name); } };
const hostile = ['/\t/evil.com', '/\n/evil.com', '/\r/evil.com', '//evil.com', '/\\evil.com', 'https://evil.com',
  'javascript:alert(1)', '/%2F%2Fevil.com', '', '/' + 'a'.repeat(5000), '/\u0000/evil.com', '/ /evil.com', 'evil.com', '/\\/evil.com', '/%09/evil.com'];
for (const h of hostile) {
  const r = safeNextPath(h, O, '/account');
  const ok = (r === '/account' || (r.startsWith('/') && !r.startsWith('//') && new URL(r, O).origin === O));
  must('hostile ' + JSON.stringify(h.slice(0, 30)) + ' -> ' + r, ok && new URL(r, O).origin === O);
  console.log(JSON.stringify(h.slice(0, 24)).padEnd(28), '->', r.slice(0, 40));
}
must('keeps good path', safeNextPath('/ok?x=1#h', O) === '/ok?x=1#h');
must('keeps simulator link', safeNextPath('/simulator?bike_id=3', O) === '/simulator?bike_id=3');
must('non-string', safeNextPath(null, O) === '/account');
// The three from the finding must hit the fallback specifically.
for (const h of ['/\t/evil.com', '/\n/evil.com', '/\r/evil.com']) must('fallback ' + h, safeNextPath(h, O) === '/account');
// /%2F%2Fevil.com stays a same-origin path (percent-encoded slashes are not host separators).
must('encoded slashes stay local', new URL(safeNextPath('/%2F%2Fevil.com', O), O).origin === O);
console.log(bad ? `${bad} FAILED` : 'ALL OK'); process.exit(bad ? 1 : 0);
