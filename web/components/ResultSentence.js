/**
 * ResultSentence — the plain-language headline of a result (CLARITY v6 rule 5).
 *
 *   <ResultSentence bikeName="Hayabusa" riderKg={75} et={10.36} trapKmh={228} />
 *   -> "A stock Hayabusa with a 75 kg rider runs the quarter mile in about
 *       10.36 s, crossing the line at 228 km/h."
 *
 * Props
 *  - bikeName  : string (required)
 *  - riderKg   : number | null — omitted from the sentence when null
 *  - et        : number (seconds) — nothing is rendered unless it is a finite number
 *  - trapKmh   : number | null — omitted when null
 *  - venueName : string | null — adds "at {venue}"
 *  - estimated : boolean — appends a calm "instant estimate" note with a glossary tip
 *  - build     : 'stock' (default) | 'modified' | any adjective | '' (none)
 *  - className : extra classes on the <p>
 *
 * Never shows a wrong or empty number (rule 7): a missing `et` renders null.
 */

import Term from './Term';

function article(word) {
  return /^[aeiou]/i.test(word) ? 'An' : 'A';
}

export default function ResultSentence({
  bikeName,
  riderKg = null,
  et,
  trapKmh = null,
  venueName = null,
  estimated = false,
  build = 'stock',
  className = '',
}) {
  if (typeof et !== 'number' || !Number.isFinite(et) || !bikeName) return null;

  const lead = build ? `${build} ${bikeName}` : bikeName;
  const art = article(lead);
  const rider =
    typeof riderKg === 'number' && Number.isFinite(riderKg)
      ? ` with a ${Math.round(riderKg)} kg rider`
      : '';
  const place = venueName ? ` at ${venueName}` : '';
  const trap =
    typeof trapKmh === 'number' && Number.isFinite(trapKmh)
      ? `, crossing the line at ${Math.round(trapKmh)} km/h`
      : '';

  return (
    <p className={`text-base leading-relaxed text-white/80 ${className}`}>
      {art} {lead}
      {rider} runs the quarter mile{place} in about{' '}
      <strong className="font-semibold text-white">{et.toFixed(2)} s</strong>
      {trap}.
      {estimated && (
        <>
          {' '}
          {/* one unbreakable unit, so the brackets never split across lines */}
          <span className="whitespace-nowrap text-white/60">
            (<Term k="instant_estimate" />)
          </span>
        </>
      )}
    </p>
  );
}
