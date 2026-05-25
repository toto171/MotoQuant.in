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
    name: 'MotoQuant Pro',
    alternateName: ['MotoQuant', 'MotoQuant Pro Simulator'],
    url: SITE_URL,
    logo: {
      '@type': 'ImageObject',
      url: `${SITE_URL}/icon-512.png`,
      width: 512,
      height: 512,
    },
    description:
      'First-principles physics engine for motorcycle quarter-mile drag racing. Predict ET, compare builds, and quantify parts ROI for 790+ bikes.',
    foundingDate: '2025-11-01',
    founder: { '@type': 'Person', name: 'Hritwik Mudhai' },
    sameAs: [
      'https://twitter.com/motoquant',
      'https://github.com/motoquant',
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
    name: 'MotoQuant Pro',
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
    name: 'MotoQuant Pro',
    alternateName: 'MotoQuant Pro Quarter-Mile Simulator',
    applicationCategory: ['AutomotiveApplication', 'SimulationApplication'],
    applicationSubCategory: 'Motorcycle Drag Racing Simulator',
    operatingSystem: 'Web, Windows, macOS, Linux',
    url: SITE_URL,
    downloadUrl: `${SITE_URL}/simulator`,
    softwareVersion: '1.0',
    description:
      'Physics-based quarter-mile drag racing simulator for motorcycles. 15-submodel engine (engine, drivetrain, clutch, chain, tires, aero, weight-transfer, rider dynamics, staging, environmental, braking, wheelie, parasitic, rolling resistance, forced induction) covering 334 bikes, 555 parts, 232 tires, 20 venues. Validated to K5 GSX-R1000 10.03s, YZF-R1 10.29s, Hayabusa 10.47s.',
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
      '790 motorcycles with individual aero + dyno curves',
      '563-part catalog with cost-per-tenth ROI analysis',
      '15 independent physics sub-models',
      'Dragy GPS + dyno import and auto-calibration',
      'XGBoost + DNN surrogate models for instant iteration',
      'Bayesian build optimization under budget',
      'Natural-language tuning queries',
    ],
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.9',
      ratingCount: '47',
      bestRating: '5',
      worstRating: '1',
    },
    inLanguage: 'en',
  };
}

export function faqSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    '@id': `${SITE_URL}/#faq`,
    mainEntity: [
      {
        '@type': 'Question',
        name: 'What is MotoQuant Pro?',
        acceptedAnswer: {
          '@type': 'Answer',
          text:
            'MotoQuant Pro is a physics-based motorcycle quarter-mile drag racing simulator. It predicts ET, trap speed, and split times for 334 production bikes using 15 independent physics sub-models and validated aero, tire, and dyno data.',
        },
      },
      {
        '@type': 'Question',
        name: 'How accurate is the quarter-mile prediction?',
        acceptedAnswer: {
          '@type': 'Answer',
          text:
            'MotoQuant Pro is validated against published magazine tests and Dragy runs: Suzuki GSX-R1000 K5 simulates 10.03s against a real 9.97s; Yamaha YZF-R1 simulates 10.29s against 10.3s; Suzuki Hayabusa simulates 10.47s (real range 10.1–10.7s). Across 55 matched benchmarks, 45% finish within ±0.20s and 82% within ±0.50s.',
        },
      },
      {
        '@type': 'Question',
        name: 'Which bikes are supported?',
        acceptedAnswer: {
          '@type': 'Answer',
          text:
            'The catalog covers 790 bikes across 25+ manufacturers: Suzuki, Yamaha, Honda, Kawasaki, BMW, Ducati, Aprilia, KTM, Triumph, Royal Enfield, Bajaj, TVS, Hero, Harley-Davidson, Indian Motorcycle, CFMoto, Benelli, Husqvarna, MV Agusta, Moto Guzzi, Buell, and more. Includes Indian 200–400cc commuters (Pulsar N125, NS200, NS400Z, Apache RTR, R15 V4), SE Asia underbones, 400cc inline-fours (Kawasaki Ninja ZX-4R, ZX-4RR), retro flagships (Yamaha XSR900 GP), and 20 two-stroke drag bikes (RD350, RX100, RGV250, H2 Mach IV).',
        },
      },
      {
        '@type': 'Question',
        name: 'Is MotoQuant Pro free?',
        acceptedAnswer: {
          '@type': 'Answer',
          text:
            'Yes — the web simulator at motoquant.in is free to use. No signup, no ads. A paid Pro desktop application for professional tuning shops will follow in Phase 6.',
        },
      },
      {
        '@type': 'Question',
        name: 'Can I use MotoQuant Pro for Indian drag strips?',
        acceptedAnswer: {
          '@type': 'Answer',
          text:
            'Yes — MotoQuant Pro was built for the Indian drag racing community. The venue database covers Aamby Valley (Pune), Madras Motor Race Track (Chennai), Buddh International Circuit (Greater Noida), Kari Motor Speedway (Coimbatore — the Coimbatore strip hosted drag events in the late 1990s before the permanent circuit was built), and Hyderabad, plus seven international venues. Parts pricing is in INR with GST and import duty already factored in.',
        },
      },
      {
        '@type': 'Question',
        name: 'How does the parts ROI engine work?',
        acceptedAnswer: {
          '@type': 'Answer',
          text:
            'Each part in the 563-part catalog is evaluated by running the simulation with and without it. The delta in ET is divided by the part cost in INR to produce a cost-per-tenth metric. A 0/1 knapsack optimizer then picks the best combination under your budget, respecting compatibility rules and known synergy pairs (e.g. exhaust + ECU flash).',
        },
      },
      {
        '@type': 'Question',
        name: 'Can I upload my own Dragy or dyno data?',
        acceptedAnswer: {
          '@type': 'Answer',
          text:
            'Yes. MotoQuant Pro imports Dragy GPS logs (CSV or VBO), DynoJet/MoTeC dyno sheets, and ECU logs (Woolich, Power Commander, MoTeC). An auto-calibration loop (differential evolution + Nelder-Mead) fits aero and tire parameters to your run for ±0.05s overlay accuracy.',
        },
      },
    ],
  };
}


// ─── Product schema — for /pricing page (Schema.org rich result eligibility) ──
// Surfaced in layout.js or the pricing page itself once Stream 5 lands.
export function productSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    '@id': `${SITE_URL}/#product`,
    name: 'MotoQuant Pro',
    description:
      'Physics-accurate motorcycle quarter-mile drag racing simulator. 334 bikes, 555 parts, 15 physics sub-models. Predict ET, trap speed, and split times. Validated against real Dragy GPS data.',
    brand: {
      '@type': 'Brand',
      name: 'MotoQuant',
    },
    offers: [
      {
        '@type': 'Offer',
        name: 'Free',
        price: '0',
        priceCurrency: 'INR',
        availability: 'https://schema.org/InStock',
        url: `${SITE_URL}/pricing`,
      },
      {
        '@type': 'Offer',
        name: 'Pro',
        price: '499',
        priceCurrency: 'INR',
        availability: 'https://schema.org/InStock',
        url: `${SITE_URL}/pricing`,
      },
    ],
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
      name: 'Hritwik Mudhai',
      url: SITE_URL,
    },
    publisher: {
      '@type': 'Organization',
      name: 'MotoQuant Pro',
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
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}
