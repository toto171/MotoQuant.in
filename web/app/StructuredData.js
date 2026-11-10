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
      'First-principles physics engine for motorcycle quarter-mile drag racing. Predict ET, compare builds and see what each part costs per tenth of a second, for 534+ bikes.',
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
      'Motorcycle quarter-mile simulator: predict ET, plan a build and find the parts worth buying.',
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
    applicationSubCategory: 'Motorcycle drag racing simulator',
    operatingSystem: 'Web',
    isAccessibleForFree: true,
    license: 'https://www.apache.org/licenses/LICENSE-2.0',
    url: SITE_URL,
    downloadUrl: `${SITE_URL}/simulator`,
    softwareVersion: '1.0',
    description:
      'Physics-based quarter-mile drag racing simulator for motorcycles. 15-submodel engine (engine, drivetrain, clutch, chain, tires, aero, weight-transfer, rider dynamics, staging, environmental, braking, wheelie, parasitic, rolling resistance, forced induction) covering 534 bikes, 546 parts, 254 tires, 20 venues. Reference bikes, simulated at sea level: GSX-R1000 K5 10.04 s (9.97 s published), YZF-R1 10.11 s (10.30 s), Hayabusa 10.11 s (10.40 s).',
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
      'Quarter-mile time, finish-line speed and top speed for 534 motorcycles',
      'Each bike with its own gearing, weight, aerodynamics and power curve',
      '546-part catalog with the cost of each tenth of a second',
      '15 independent physics sub-models',
      'Dragy GPS and dyno import, lined up against the simulation',
      'Instant estimates computed in the browser',
      'Best parts for your budget',
      'Tuning questions in plain language',
    ],
    inLanguage: 'en',
  };
}

// Single source for the landing-page FAQ: the visible accordion (app/page.js)
// and the FAQPage JSON-LD below render the SAME questions and answers.
export const FAQ_ITEMS = [
  {
    q: 'What is MotoQuant?',
    a: 'MotoQuant is a free simulator that predicts how fast a motorcycle runs the quarter mile. Pick one of 534 bikes and it shows the time, the speed at the finish line and the splits. The physics is checked against published tests.',
  },
  {
    q: 'How accurate is the quarter-mile prediction?',
    a: 'Across 263 matches with published magazine tests and Dragy runs, the simulated time is off by 0.25 s on average (weighted by how trustworthy each source is), and 130 land within 0.20 s of the published time. Sport bikes do best; small bikes are less well covered by published tests and carry a wider margin. The three reference bikes, simulated at sea level: Suzuki GSX-R1000 K5 10.04 s against 9.97 s in Cycle World; Yamaha YZF-R1 10.11 s against 10.30 s in Sport Rider; Suzuki Hayabusa 10.11 s against 10.40 s in Cycle World.',
  },
  {
    q: 'Which bikes are included?',
    a: 'The catalog covers 534 bikes from 33 makers: Suzuki, Yamaha, Honda, Kawasaki, BMW, Ducati, Aprilia, KTM, Triumph, Royal Enfield, Bajaj, TVS, Hero, Harley-Davidson, Indian, CFMoto, Benelli, Husqvarna, MV Agusta, Moto Guzzi, Buell and more. That includes Indian 200–400 cc bikes (Pulsar, Apache, R15 V4), South-East Asian underbones, 400 cc four-cylinder bikes, retro flagships and 21 two-strokes (RD350, RX100, RGV250, H2 Mach IV). Missing yours? Suggest it from the bike list.',
  },
  {
    q: 'Is MotoQuant free?',
    a: 'Yes. MotoQuant is free and open source under the Apache License 2.0. There is no account to create: saved runs stay in your browser. motoquant.in is a free public copy of the project, and you can also run your own from the GitHub repository.',
  },
  {
    q: 'Can I use it for Indian drag strips?',
    a: 'Yes. MotoQuant was built for the Indian drag racing community. It knows Aamby Valley (Pune), Madras Motor Race Track (Chennai), Buddh International Circuit (Greater Noida), Kari Motor Speedway (Coimbatore) and Hyderabad, plus 15 venues abroad, and adjusts for each place\u2019s altitude and weather. Parts prices are in rupees with GST and import duty already included.',
  },
  {
    q: 'How does it decide which parts are worth buying?',
    a: 'Each part in the 546-part catalog is tested by running the simulation with and without it. The change in quarter-mile time is divided by the part\u2019s price to get the cost of each tenth of a second. The best-parts tool then picks the combination that gains the most within your budget, following the compatibility rules and known pairings such as exhaust plus ECU flash.',
  },
  {
    q: 'Who answers chat questions, and can I use my own key?',
    a: 'The chat assistant is Claude, made by Anthropic, so your questions are sent to Anthropic. Pick the mechanic (Claude Sonnet 5.5) for quick answers or the doctor (Claude Opus 5.5) to dig deeper. Asking is free up to a daily limit. You can also add your own Anthropic API key under \u201cUse your own key\u201d: it stays in your browser, is sent with your questions to answer them, and is never stored on our server.',
  },
  {
    q: 'Can I upload my own Dragy or dyno data?',
    a: 'Yes. MotoQuant reads Dragy GPS logs (CSV or VBO) and DynoJet or MoTeC dyno sheets, corrects dyno numbers for the day\u2019s air, and lines your real run up against the simulation: finish time, finish-line speed and split-by-split differences for your own bike. The file is read, compared and deleted; nothing is kept.',
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
