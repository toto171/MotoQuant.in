// Shared JSON-LD structured-data blocks.
// Dropped into <head> (or top of <body>) via <Script type="application/ld+json"> so
// Google / Bing / Yandex get strongly-typed signals about:
//   - Who runs the site (Organization)
//   - What the site is (WebSite + SearchAction)
//   - What the product is (SoftwareApplication, free, browser-based)
//   - What questions it answers (FAQPage — rich-result eligible)
//
// Each helper returns a plain object; use <StructuredData data={...} /> to render.
// We intentionally keep all URLs absolute (https://motoquant.in/...) because Google
// treats absolute @id values as canonical and collapses duplicates across crawls.

export const SITE_URL = 'https://motoquant.in';

export function organizationSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    '@id': `${SITE_URL}/#organization`,
    name: 'MotoQuant',
    alternateName: ['MotoQuant', 'MotoQuant Simulator'],
    url: SITE_URL,
    logo: {
      '@type': 'ImageObject',
      url: `${SITE_URL}/icon-512.png`,
      width: 512,
      height: 512,
    },
    description:
      'First-principles physics engine for motorcycle quarter-mile drag racing. Predict ET, compare builds, and quantify parts ROI for 534+ bikes.',
    foundingDate: '2025-11-01',
    founder: [
      { '@type': 'Person', name: 'Arya Desai' },
      { '@type': 'Person', name: 'Ritwik Singh' },
      { '@type': 'Person', name: 'Sahil Shetye' },
    ],
    sameAs: [
      'https://twitter.com/motoquant',
      'https://github.com/toto171/MotoQuant.in',
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      contactType: 'customer support',
      email: 'motoquant@gmail.com',
      areaServed: ['IN', 'MY', 'TH', 'ID', 'PH', 'AE', 'US', 'GB'],
      availableLanguage: ['English'],
    },
    areaServed: { '@type': 'Country', name: 'India' },
  };
}

export function websiteSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    '@id': `${SITE_URL}/#website`,
    url: SITE_URL,
    name: 'MotoQuant',
    description:
      'Motorcycle drag racing quarter-mile simulator — ET prediction, build optimization, parts ROI.',
    inLanguage: 'en-IN',
    publisher: { '@id': `${SITE_URL}/#organization` },
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${SITE_URL}/bikes?search={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  };
}

export function softwareApplicationSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    '@id': `${SITE_URL}/#software`,
    name: 'MotoQuant',
    alternateName: 'MotoQuant Quarter-Mile Simulator',
    applicationCategory: ['AutomotiveApplication', 'SimulationApplication'],
    applicationSubCategory: 'Motorcycle Drag Racing Simulator',
    operatingSystem: 'Web',
    isAccessibleForFree: true,
    license: 'https://opensource.org/licenses/MIT',
    url: SITE_URL,
    downloadUrl: `${SITE_URL}/simulator`,
    softwareVersion: '1.0',
    description:
      'Physics-based quarter-mile drag racing simulator for motorcycles. 15-submodel engine (engine, drivetrain, clutch, chain, tires, aero, weight-transfer, rider dynamics, staging, environmental, braking, wheelie, parasitic, rolling resistance, forced induction) covering 534 bikes, 546 parts, 254 tires, 20 venues. Validated to K5 GSX-R1000 9.93s, YZF-R1 10.14s, Hayabusa 10.36s.',
    publisher: { '@id': `${SITE_URL}/#organization` },
    author: { '@id': `${SITE_URL}/#organization` },
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'INR',
      availability: 'https://schema.org/InStock',
      url: `${SITE_URL}/simulator`,
    },
    featureList: [
      'Quarter-mile ET prediction to ±0.2s',
      '534 motorcycles with individual aero + dyno curves',
      '546-part catalog with cost-per-tenth ROI analysis',
      '15 independent physics sub-models',
      'Dragy GPS + dyno import with sim overlay',
      'Calibrated surrogate model for instant iteration',
      'Budget-aware build optimization',
      'Natural-language tuning queries',
    ],
    inLanguage: 'en',
  };
}

// Single source for the landing-page FAQ: the visible accordion (app/page.js)
// and the FAQPage JSON-LD below render the SAME questions and answers.
export const FAQ_ITEMS = [
  {
    q: 'What is MotoQuant?',
    a: 'MotoQuant is a free simulator that predicts how fast a motorcycle runs the quarter mile. Pick a bike and it shows the time, the speed at the finish line and the splits for 534 bikes, using physics that is checked against real published tests.',
  },
  {
    q: 'How accurate is the quarter-mile prediction?',
    a: 'Checked against published magazine tests and Dragy runs: the Suzuki GSX-R1000 K5 simulates 9.93 s against a real 9.97 s; the Yamaha YZF-R1 simulates 10.14 s against 10.3 s; the Suzuki Hayabusa simulates 10.36 s (real range 10.1–10.7 s). The November 2026 check covers 250 published benchmarks (273 matched to catalog bikes) with a weighted mean bias of +0.009 s; 137 of 273 land within ±0.20 s of the published time. Small bikes are less well covered by published tests, so expect a wider margin there.',
  },
  {
    q: 'Which bikes are included?',
    a: 'The catalog covers 534 bikes across 25+ makers: Suzuki, Yamaha, Honda, Kawasaki, BMW, Ducati, Aprilia, KTM, Triumph, Royal Enfield, Bajaj, TVS, Hero, Harley-Davidson, Indian Motorcycle, CFMoto, Benelli, Husqvarna, MV Agusta, Moto Guzzi, Buell and more. That includes Indian 200–400 cc bikes (Pulsar, Apache, R15 V4), South-East Asian underbones, 400 cc four-cylinder bikes, retro flagships and 20 two-stroke drag bikes (RD350, RX100, RGV250, H2 Mach IV). Missing yours? You can ask for it to be added.',
  },
  {
    q: 'Is MotoQuant free?',
    a: 'Yes. MotoQuant is free and open source under the MIT License. You do not need an account to run simulations; an optional free account just lets you save runs. motoquant.in is a free public copy of the open-source project, and you can also run it yourself from the GitHub repository.',
  },
  {
    q: 'Can I use it for Indian drag strips?',
    a: 'Yes. MotoQuant was built for the Indian drag racing community. It knows Aamby Valley (Pune), Madras Motor Race Track (Chennai), Buddh International Circuit (Greater Noida), Kari Motor Speedway (Coimbatore) and Hyderabad, plus seven international venues, and adjusts for each place\u2019s altitude and weather. Parts prices are in rupees with GST and import duty already included.',
  },
  {
    q: 'How does it decide which parts are worth buying?',
    a: 'Each part in the 546-part catalog is tested by running the simulation with and without it. The change in quarter-mile time is divided by the part\u2019s price to get the cost of each tenth of a second. The best-parts tool then picks the combination that gains the most within your budget, respecting compatibility rules and known pairings such as exhaust plus ECU flash.',
  },
  {
    q: 'Can I upload my own Dragy or dyno data?',
    a: 'Yes. MotoQuant reads Dragy GPS logs (CSV or VBO) and DynoJet or MoTeC dyno sheets, corrects dyno numbers for the day\u2019s air, and lines your real run up against the simulation: finish time, finish-line speed and split-by-split differences for your own bike.',
  },
];

export function faqSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    '@id': `${SITE_URL}/#faq`,
    mainEntity: FAQ_ITEMS.map(({ q, a }) => ({
      '@type': 'Question',
      name: q,
      acceptedAnswer: { '@type': 'Answer', text: a },
    })),
  };
}


// ─── Article schema — for /blog posts (NewsArticle-compatible) ──
export function articleSchema({ title, description, slug, datePublished, dateModified }) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    '@id': `${SITE_URL}/blog/${slug}#article`,
    headline: title,
    description,
    url: `${SITE_URL}/blog/${slug}`,
    datePublished,
    dateModified: dateModified || datePublished,
    author: {
      '@type': 'Person',
      name: 'Ritwik Singh',
      url: SITE_URL,
    },
    publisher: {
      '@type': 'Organization',
      name: 'MotoQuant',
      url: SITE_URL,
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `${SITE_URL}/blog/${slug}`,
    },
  };
}

export default function StructuredData({ data }) {
  // Injected via a plain <script> tag — crawlers parse this even though React
  // normally reserves <script> for client-side execution. Next.js is happy to
  // serialise it as-is because we're passing JSON through dangerouslySetInnerHTML.
  // "<" is escaped to \u003c (identical once JSON-parsed) so a "</script>"
  // inside any data value can never terminate the tag early (XSS hardening).
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, '\\u003c') }}
    />
  );
}
