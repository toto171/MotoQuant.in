// Dynamic per-bike metadata. This is the single highest-leverage SEO change
// in the project: every one of the 501 bike detail pages now gets a unique
// title, description, keyword set, Open Graph, and rich-result-eligible
// Vehicle/Product schema — so search queries like "Hayabusa quarter mile
// time" or "Pulsar NS200 drag simulator" can land directly on the right
// detail page instead of the homepage.
//
// The page body (page.js) is a 'use client' component; it re-fetches the
// bike at render time. This server layout fetches the *same* bike so the
// <head> metadata is server-rendered and visible to crawlers.

import StructuredData, { SITE_URL } from '../../StructuredData';

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.MOTOQUANT_INTERNAL_API_URL ||
  SITE_URL; // Same-origin via Vercel rewrite in production

async function fetchBike(id) {
  // Give the Render backend a longer rope for SSR: its free tier can cold-
  // start at 10-30s. Vercel's default fetch has no explicit timeout, but we
  // add our own AbortController so generateMetadata doesn't hang a render
  // if Render is genuinely down. 20s is safe — Vercel caps function
  // execution at 60s on hobby plans, 300s on pro, so 20s leaves headroom.
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20_000);
  try {
    const res = await fetch(`${API_BASE}/api/bikes/${id}`, {
      // Revalidate every 24h — bike specs don't churn; cheap to keep fresh.
      next: { revalidate: 86400 },
      signal: controller.signal,
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

function displayName(bike) {
  const parts = [bike.manufacturer, bike.model, bike.year].filter(Boolean);
  return parts.join(' ');
}

function short(bike) {
  // "Suzuki GSX-R 1000 K5" — stripped of year for headline cases.
  return [bike.manufacturer, bike.model].filter(Boolean).join(' ');
}

export async function generateMetadata({ params }) {
  const { id } = await params;
  const bike = await fetchBike(id);

  if (!bike) {
    // The API fetch failed — most likely the Render backend is on a cold
    // start (free tier sleeps after inactivity) and Vercel's SSR fetch
    // timed out. We have NO WAY to distinguish "bike doesn't exist" from
    // "backend momentarily unreachable" at this layer, and the client-side
    // page.js will re-fetch and render the bike correctly once the backend
    // wakes up.
    //
    // DO NOT emit noindex here — an API hiccup at Googlebot crawl time
    // would permanently mark the page non-indexable and we'd lose 501
    // URLs from the index. Emit neutral-but-indexable metadata instead;
    // Google re-crawls periodically and will pick up the full metadata
    // once the API is responsive again.
    const fallbackTitle =
      'Motorcycle Quarter-Mile Drag Simulator — MotoQuant Pro';
    const fallbackDesc =
      'Physics-based quarter-mile drag-racing simulator for this motorcycle. 501 bikes in the catalog. Free and in-browser.';
    return {
      title: fallbackTitle,
      description: fallbackDesc,
      alternates: { canonical: `/bikes/${id}` },
      openGraph: {
        title: fallbackTitle,
        description: fallbackDesc,
        url: `${SITE_URL}/bikes/${id}`,
        type: 'website',
      },
      robots: { index: true, follow: true },
    };
  }

  const name = displayName(bike);
  const nameShort = short(bike);
  const category = bike.category || 'motorcycle';
  const power = bike.peak_power_hp ? `${Math.round(bike.peak_power_hp)} hp` : null;
  const disp = bike.displacement_cc ? `${Math.round(bike.displacement_cc)}cc` : null;
  const mass = bike.dry_mass_kg ? `${Math.round(bike.dry_mass_kg)} kg` : null;

  // Compose the title around the three highest-intent queries for a given bike:
  //   "<bike name> quarter mile time"
  //   "<bike name> drag simulator"
  //   "<bike name> specs"
  const title = `${name} — Quarter-Mile ET, Drag Simulator & Full Specs`;

  const descParts = [
    `Simulate ${name} quarter-mile drag times with MotoQuant Pro.`,
    disp && power && mass
      ? `${disp} · ${power} · ${mass} dry.`
      : [disp, power, mass].filter(Boolean).join(' · '),
    `Full physics-based ET prediction, individual aero (Cd ${bike.cd?.toFixed?.(2) || '—'}, frontal area ${bike.frontal_area_m2?.toFixed?.(2) || '—'} m²), gear ratios, and OEM tire fitments.`,
    'Free and in-browser — no signup.',
  ]
    .filter(Boolean)
    .join(' ');

  const keywords = [
    `${name} quarter mile`,
    `${name} quarter mile time`,
    `${name} 1/4 mile`,
    `${name} drag simulator`,
    `${name} drag racing`,
    `${name} ET`,
    `${name} trap speed`,
    `${name} specs`,
    `${name} specifications`,
    `${name} power`,
    `${name} dyno`,
    `${name} acceleration`,
    `${nameShort} quarter mile time`,
    `${nameShort} drag`,
    `${nameShort} specs`,
    `${nameShort} simulator`,
    bike.manufacturer && `${bike.manufacturer} drag racing`,
    bike.manufacturer && `${bike.manufacturer} motorcycle simulator`,
    category && `${category} drag racing`,
    category && `fastest ${category} motorcycle`,
  ].filter(Boolean);

  const canonical = `/bikes/${bike.id}`;

  return {
    title,
    description: descParts,
    alternates: { canonical },
    keywords,
    openGraph: {
      title: `${name} — Quarter-Mile Drag Simulator & Specs`,
      description: descParts,
      url: `${SITE_URL}${canonical}`,
      type: 'website',
      images: [
        {
          url: `${SITE_URL}/og-image.png`,
          width: 1200,
          height: 630,
          alt: `${name} — quarter-mile drag simulation data on MotoQuant Pro`,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: `${name} — Quarter-Mile Drag Simulator`,
      description: descParts,
    },
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        'max-image-preview': 'large',
        'max-snippet': -1,
      },
    },
  };
}

// ──────────────────────────────────────────────────────────────────────────
// Structured-data: Vehicle + Product + BreadcrumbList
// ──────────────────────────────────────────────────────────────────────────
// The Vehicle type is what Google actually uses to enrich motorcycle SERPs
// (displacement, power, model year badges). Product gives us price=0 /
// InStock signals so the page doesn't get demoted as "low-value" thin copy.

function vehicleSchema(bike) {
  const name = displayName(bike);
  return {
    '@context': 'https://schema.org',
    '@type': ['Vehicle', 'Product'],
    '@id': `${SITE_URL}/bikes/${bike.id}#vehicle`,
    name,
    alternateName: [short(bike), bike.model].filter(Boolean),
    brand: bike.manufacturer
      ? { '@type': 'Brand', name: bike.manufacturer }
      : undefined,
    manufacturer: bike.manufacturer
      ? { '@type': 'Organization', name: bike.manufacturer }
      : undefined,
    model: bike.model,
    modelDate: bike.year ? String(bike.year) : undefined,
    productionDate: bike.year ? String(bike.year) : undefined,
    vehicleModelDate: bike.year ? String(bike.year) : undefined,
    category: bike.category || 'Motorcycle',
    bodyType: 'Motorcycle',
    vehicleConfiguration: bike.cylinder_config,
    fuelType: bike.stroke_type === 2 ? 'Two-stroke gasoline' : 'Gasoline',
    numberOfForwardGears: Array.isArray(bike.gear_ratios)
      ? bike.gear_ratios.length
      : undefined,
    weight:
      bike.dry_mass_kg != null
        ? {
            '@type': 'QuantitativeValue',
            value: Math.round(bike.dry_mass_kg),
            unitCode: 'KGM',
          }
        : undefined,
    vehicleEngine:
      bike.displacement_cc || bike.peak_power_hp
        ? {
            '@type': 'EngineSpecification',
            name: [
              bike.displacement_cc && `${Math.round(bike.displacement_cc)}cc`,
              bike.cylinder_config,
              bike.stroke_type === 2 ? '2-stroke' : '4-stroke',
            ]
              .filter(Boolean)
              .join(' '),
            engineDisplacement:
              bike.displacement_cc != null
                ? {
                    '@type': 'QuantitativeValue',
                    value: Math.round(bike.displacement_cc),
                    unitCode: 'CMQ', // cubic centimetre
                  }
                : undefined,
            enginePower:
              bike.peak_power_hp != null
                ? {
                    '@type': 'QuantitativeValue',
                    value: Math.round(bike.peak_power_hp),
                    unitCode: 'BHP',
                  }
                : undefined,
            torque:
              bike.peak_torque_nm != null
                ? {
                    '@type': 'QuantitativeValue',
                    value: Math.round(bike.peak_torque_nm),
                    unitCode: 'NU', // Newton-metre
                  }
                : undefined,
          }
        : undefined,
    url: `${SITE_URL}/bikes/${bike.id}`,
    image: `${SITE_URL}/og-image.png`,
    description: `Full physics-based quarter-mile drag simulation data for the ${name} on MotoQuant Pro.`,
    offers: {
      '@type': 'Offer',
      url: `${SITE_URL}/simulator?bike_id=${bike.id}`,
      priceCurrency: 'INR',
      price: '0',
      availability: 'https://schema.org/InStock',
      itemCondition: 'https://schema.org/NewCondition',
      description: 'Free quarter-mile simulation for this motorcycle on MotoQuant Pro.',
    },
  };
}

function breadcrumbSchema(bike) {
  const name = displayName(bike);
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Bikes', item: `${SITE_URL}/bikes` },
      {
        '@type': 'ListItem',
        position: 3,
        name,
        item: `${SITE_URL}/bikes/${bike.id}`,
      },
    ],
  };
}

export default async function BikeDetailLayout({ children, params }) {
  const { id } = await params;
  const bike = await fetchBike(id);

  return (
    <>
      {bike && (
        <>
          <StructuredData data={vehicleSchema(bike)} />
          <StructuredData data={breadcrumbSchema(bike)} />
        </>
      )}
      {children}
    </>
  );
}
