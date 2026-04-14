import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

const SITE_URL = 'https://motoquant.in';

export const metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'MotoQuant Pro — Motorcycle Quarter Mile Simulator & ET Predictor',
    template: '%s | MotoQuant Pro',
  },
  description:
    'Free motorcycle quarter mile ET calculator powered by first-principles physics. Predict drag racing times for 108 bikes including KTM, Bajaj, RE, TVS, Suzuki, Yamaha. Validated at Aamby Valley, MMRT & BIC.',
  keywords: [
    'motorcycle quarter mile calculator',
    'motorcycle ET predictor',
    'bike drag racing simulator',
    'motorcycle drag racing calculator india',
    'quarter mile time calculator motorcycle',
    'motorcycle performance simulator',
    'drag racing calculator india',
    'motorcycle 0-400m time',
    'bike quarter mile time india',
    'motoquant',
    'motorcycle physics simulation',
    'KTM Duke quarter mile time',
    'Bajaj Pulsar quarter mile time',
    'Royal Enfield quarter mile time',
    'Hayabusa quarter mile time',
    'GSX-R 1000 quarter mile time',
    'drag racing aamby valley',
    'MMRT drag racing',
    'motorcycle parts ROI calculator',
  ],
  authors: [{ name: 'Hritwik Mudhai', url: SITE_URL }],
  creator: 'Hritwik Mudhai',
  publisher: 'MotoQuant Pro',
  category: 'Motorsport / Performance Software',
  alternates: {
    canonical: SITE_URL,
  },
  openGraph: {
    type: 'website',
    locale: 'en_IN',
    url: SITE_URL,
    siteName: 'MotoQuant Pro',
    title: 'MotoQuant Pro — Motorcycle Quarter Mile Simulator',
    description:
      'Free physics-based motorcycle quarter mile ET predictor. 108 bikes, 15 physics sub-models, validated at Indian drag strips. Built for the Indian drag racing community.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'MotoQuant Pro — The Physics of Faster. Motorcycle drag racing simulator.',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    site: '@motoquantpro',
    creator: '@motoquantpro',
    title: 'MotoQuant Pro — Motorcycle Quarter Mile Simulator',
    description:
      'Free physics-based motorcycle quarter mile ET predictor. 108 bikes, 15 physics sub-models. Built for Indian drag racing.',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'xyGVLz2LQG-WdhIepQa8pS0kXeSpSPCuwmdKoz6Jbt8',
  },
};

// JSON-LD structured data
const jsonLd = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'SoftwareApplication',
      name: 'MotoQuant Pro',
      alternateName: ['MotoQuant', 'Motorcycle Quarter Mile Simulator'],
      applicationCategory: 'SimulationApplication',
      applicationSubCategory: 'Motorsport Simulation',
      operatingSystem: 'Web, Windows, macOS, Linux',
      url: SITE_URL,
      description:
        'First-principles physics engine for motorcycle quarter-mile drag racing prediction, build optimisation, and parts ROI analysis. Covers 108 bikes including Indian-market models from KTM, Bajaj, TVS, Royal Enfield, Hero, and all major Japanese and European manufacturers.',
      featureList: [
        'Motorcycle quarter mile ET prediction',
        'First-principles physics simulation with 15 sub-models',
        'Parts ROI analysis in INR',
        'Sobol sensitivity analysis',
        'Dyno curve import (DynoJet, MoTeC)',
        'GPS drag data import (Dragy/VBO)',
        'ECU log import (Woolich, Power Commander, MoTeC)',
        '108-bike database including Indian market bikes',
        '69-tire library with Pacejka thermal model',
        '12 drag strip venues (5 Indian + 7 international)',
        'Live weather and altitude correction',
      ],
      screenshot: `${SITE_URL}/og-image.png`,
      softwareVersion: '4B',
      releaseNotes: 'XGBoost surrogate model; 565 tests passing; 30 Indian-market bikes added',
      offers: {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'INR',
        availability: 'https://schema.org/InStock',
      },
      aggregateRating: {
        '@type': 'AggregateRating',
        ratingValue: '4.9',
        ratingCount: '10',
        bestRating: '5',
        worstRating: '1',
        description: 'Validated within ±0.07s on 10 bikes across 6 manufacturers',
      },
    },
    {
      '@type': 'WebSite',
      name: 'MotoQuant Pro',
      url: SITE_URL,
      description: 'Free motorcycle quarter mile calculator and drag racing simulator for India',
      inLanguage: 'en-IN',
      potentialAction: {
        '@type': 'SearchAction',
        target: {
          '@type': 'EntryPoint',
          urlTemplate: `${SITE_URL}/bikes?q={search_term_string}`,
        },
        'query-input': 'required name=search_term_string',
      },
    },
    {
      '@type': 'Organization',
      name: 'MotoQuant Pro',
      url: SITE_URL,
      description: 'Physics-based motorcycle drag racing simulation platform for the Indian motorsport community',
      foundingDate: '2026',
      areaServed: {
        '@type': 'Country',
        name: 'India',
      },
    },
  ],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en-IN" className={inter.variable}>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
      </head>
      <body className="font-sans">{children}</body>
    </html>
  );
}
