import { Inter, Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '../components/AuthProvider';
import StructuredData, {
  organizationSchema,
  websiteSchema,
  softwareApplicationSchema,
  faqSchema,
  SITE_URL,
} from './StructuredData';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
  display: 'swap',
  weight: ['400', '500', '600', '700'],
});

const spaceGrotesk = Space_Grotesk({
  variable: '--font-space-grotesk',
  subsets: ['latin'],
  display: 'swap',
  weight: ['500', '600', '700'],
});

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-jetbrains-mono',
  subsets: ['latin'],
  display: 'swap',
  weight: ['400', '500', '700'],
});

export const viewport = {
  themeColor: '#000000',
  width: 'device-width',
  initialScale: 1,
  // Allow zoom — Lighthouse flags "user-scalable=no" as an accessibility failure
  // and accessibility score is a Core Web Vitals ranking input.
  maximumScale: 5,
};

// ──────────────────────────────────────────────────────────────────────────
// SEO strategy
// ──────────────────────────────────────────────────────────────────────────
// Targets grouped by intent:
//   - Brand: "motoquant", "moto quant pro"
//   - Product category: "motorcycle drag simulator", "quarter mile calculator"
//   - Bike-specific long tail: "hayabusa quarter mile time", "zx-10r 1/4 mile"
//   - Geographic: "drag racing india", "aamby valley drag strip", "kari speedway"
//   - Use-case: "best mods for hayabusa", "motorcycle parts roi"
//   - Tool queries: "dragy data analysis", "motorcycle dyno simulator"
//   - Physics / academic: "motorcycle physics simulation", "tire slip model"
// We don't stuff keywords in body copy — Google's modern ranking signals are
// earned through page metadata, structured data, content freshness, and
// internal linking. This file handles the first three.

const DESCRIPTION =
  'Free physics-based motorcycle quarter-mile drag racing simulator — not a power-to-weight formula. Predict ET, trap speed, 60-ft split for 342+ bikes including Hayabusa, ZX-14R, R15 V4, KTM Duke 390, Pulsar NS200. Compare builds, quantify parts ROI in INR, upload Dragy runs for auto-calibration. Built for the Indian drag racing community — Aamby Valley, MMRT, BIC, Kari.';

export const metadata = {
  title: {
    default:
      'MotoQuant Pro — Motorcycle Quarter-Mile Drag Racing Simulator | ET Predictor & Build Optimizer',
    template: '%s · MotoQuant Pro',
  },
  description: DESCRIPTION,
  metadataBase: new URL(SITE_URL),
  applicationName: 'MotoQuant Pro',
  manifest: '/site.webmanifest',
  alternates: {
    canonical: '/',
    languages: {
      'en-IN': '/',
      'en-US': '/',
      'x-default': '/',
    },
  },
  openGraph: {
    title:
      'MotoQuant Pro — Motorcycle Quarter-Mile Drag Racing Simulator',
    description: DESCRIPTION,
    url: SITE_URL,
    siteName: 'MotoQuant Pro',
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        secureUrl: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'MotoQuant Pro — quarter-mile drag racing simulator covering 501 motorcycles, 563 parts, 232 tires, 20 venues',
        type: 'image/png',
      },
    ],
    locale: 'en_IN',
    alternateLocale: ['en_US', 'en_GB', 'en_AU'],
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title:
      'MotoQuant Pro — Motorcycle Quarter-Mile Drag Racing Simulator',
    description: DESCRIPTION,
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        alt: 'MotoQuant Pro — quarter-mile drag racing simulator covering 501 motorcycles, 563 parts, 232 tires, 20 venues',
      },
    ],
    site: '@motoquant',
    creator: '@motoquant',
  },
  keywords: [
    // Brand
    'motoquant',
    'motoquant pro',
    'motoquant simulator',
    // Primary category
    'motorcycle drag racing simulator',
    'motorcycle quarter mile calculator',
    'motorcycle quarter mile simulator',
    'bike drag simulator',
    '1/4 mile simulator motorcycle',
    'ET predictor motorcycle',
    'drag race simulator bike',
    'motorcycle acceleration simulator',
    // Indian drag racing geo
    'drag racing india',
    'motorcycle drag racing india',
    'indian drag strip',
    'aamby valley drag',
    'aamby valley quarter mile',
    'valley run drag race',
    'valley run quarter mile',
    'valley run 2026',
    'aces of speed drag',
    'kari motor speedway drag',
    'mmrt drag racing',
    'buddh international circuit drag',
    'hyderabad drag strip',
    'pune drag racing',
    // Bike-specific long tail
    'hayabusa quarter mile time',
    'hayabusa drag simulator',
    'suzuki gsx-r1000 drag',
    'gsxr k5 quarter mile',
    'yamaha r1 quarter mile',
    'kawasaki zx-10r drag',
    'zx-14r quarter mile',
    'ninja h2 drag time',
    'panigale v4 quarter mile',
    'bmw s1000rr drag',
    'ktm duke 390 drag',
    'ktm rc 390 quarter mile',
    'pulsar ns200 drag time',
    'r15 v4 quarter mile',
    'apache rr 310 drag',
    'dominar 400 quarter mile',
    'interceptor 650 drag',
    'rx100 quarter mile',
    'rd350 drag simulator',
    // Use-case intent
    'best mods for hayabusa',
    'motorcycle parts roi calculator',
    'motorcycle build optimizer',
    'how much faster with exhaust',
    'cost per tenth motorcycle',
    'motorcycle drag build planner',
    'quarter mile budget build',
    // Physics / academic
    'motorcycle physics simulation',
    'first principles drag racing physics',
    'pacejka tire motorcycle',
    'motorcycle dyno simulator',
    'aerodynamic drag motorcycle',
    'tire slip ratio simulation',
    // Data tools
    'dragy data analysis',
    'dragy quarter mile simulator',
    'motorcycle ecu log analysis',
    'dyno data overlay',
    'woolich racing analysis',
    'power commander log',
    // Competitive alternatives
    'drag sim alternative',
    'motorcycle calculator online',
    'free quarter mile simulator',
  ],
  authors: [{ name: 'Ritwik Singh', url: SITE_URL }],
  creator: 'Ritwik Singh',
  publisher: 'MotoQuant Pro',
  category: 'Automotive Simulation',
  classification: 'Motorcycle Racing Simulation Software',
  robots: {
    index: true,
    follow: true,
    nocache: false,
    googleBot: {
      index: true,
      follow: true,
      noimageindex: false,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  formatDetection: {
    // Prevent iOS Safari from auto-linking phone-number-like strings
    // (e.g. the "1000" in "GSX-R 1000") as dialable telephone links.
    telephone: false,
    email: false,
    address: false,
  },
  verification: {
    // Placeholders — replace with real tokens when DNS-verified.
    // Google: https://search.google.com/search-console
    // Bing:   https://www.bing.com/webmasters
    // Yandex: https://webmaster.yandex.com
    google: process.env.NEXT_PUBLIC_GOOGLE_VERIFICATION || undefined,
    yandex: process.env.NEXT_PUBLIC_YANDEX_VERIFICATION || undefined,
    other: process.env.NEXT_PUBLIC_BING_VERIFICATION
      ? { 'msvalidate.01': process.env.NEXT_PUBLIC_BING_VERIFICATION }
      : undefined,
  },
  other: {
    // Pinterest, Facebook Domain Verification, and misc. validators can be
    // surfaced via NEXT_PUBLIC_* env vars without re-deploying code.
    ...(process.env.NEXT_PUBLIC_FB_DOMAIN_VERIFICATION && {
      'facebook-domain-verification': process.env.NEXT_PUBLIC_FB_DOMAIN_VERIFICATION,
    }),
    ...(process.env.NEXT_PUBLIC_PINTEREST_VERIFICATION && {
      'p:domain_verify': process.env.NEXT_PUBLIC_PINTEREST_VERIFICATION,
    }),
    'geo.region': 'IN',
    'geo.placename': 'Pune, Maharashtra, India',
    'geo.position': '18.5204;73.8567',
    ICBM: '18.5204, 73.8567',
    rating: 'General',
    distribution: 'Global',
    'revisit-after': '7 days',
  },
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={[inter.variable, spaceGrotesk.variable, jetbrainsMono.variable].join(' ')}
    >
      <head>
        {/* Preconnect to the API origin — shaves ~100-300ms off first sim call */}
        <link rel="preconnect" href={SITE_URL} crossOrigin="anonymous" />
        <link rel="dns-prefetch" href={SITE_URL} />
        {/* RSS-style hint for crawlers that the sitemap exists even if they
            don't parse robots.txt (older Yandex / Baidu / Naver behaviour). */}
        <link rel="sitemap" type="application/xml" href="/sitemap.xml" />
      </head>
      <body className="font-sans">
        {/* Three site-wide JSON-LD blocks. Keeping them in <body> (rather than
            <head>) is equivalent per the schema.org + Google guidance, and
            lets us render them as React children without <Script> wrappers. */}
        <StructuredData data={organizationSchema()} />
        <StructuredData data={websiteSchema()} />
        <StructuredData data={softwareApplicationSchema()} />
        <StructuredData data={faqSchema()} />
        <AuthProvider>{children}</AuthProvider>
        <div className="grain" aria-hidden="true" />
      </body>
    </html>
  );
}
