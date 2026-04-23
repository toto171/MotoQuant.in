import { Inter, Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';

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
};

export const metadata = {
  title: {
    default: 'MotoQuant Pro — The Physics of Faster',
    template: '%s · MotoQuant Pro',
  },
  description: 'First-principles physics simulation for quarter-mile drag racing. Predict ET, optimize builds, and understand what actually moves the needle on the strip.',
  metadataBase: new URL('https://motoquant.in'),
  applicationName: 'MotoQuant Pro',
  manifest: '/site.webmanifest',
  icons: {
    icon: [
      { url: '/favicon.ico', sizes: 'any' },
      { url: '/icon.svg', type: 'image/svg+xml' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-48x48.png', sizes: '48x48', type: 'image/png' },
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    shortcut: ['/favicon.ico'],
  },
  openGraph: {
    title: 'MotoQuant Pro — The Physics of Faster',
    description: 'First-principles physics simulation for quarter-mile drag racing. Predict ET, optimize builds, and understand what actually moves the needle on the strip.',
    url: 'https://motoquant.in',
    siteName: 'MotoQuant Pro',
    images: [
      {
        url: 'https://motoquant.in/og-image.png',
        secureUrl: 'https://motoquant.in/og-image.png',
        width: 1200,
        height: 630,
        alt: 'MotoQuant Pro — quarter-mile simulation covering 287 bikes, 465 parts, 12 venues',
        type: 'image/png',
      },
    ],
    locale: 'en_IN',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MotoQuant Pro — The Physics of Faster',
    description: 'First-principles physics simulation for quarter-mile drag racing. Predict ET, optimize builds, and understand what actually moves the needle on the strip.',
    images: [
      {
        url: 'https://motoquant.in/og-image.png',
        alt: 'MotoQuant Pro — quarter-mile simulation covering 287 bikes, 465 parts, 12 venues',
      },
    ],
    site: '@motoquant',
    creator: '@motoquant',
  },
  keywords: [
    'motorcycle drag racing',
    'quarter mile simulator',
    'ET prediction',
    'motorcycle physics',
    'drag racing India',
    'Aamby Valley drag',
    'Hayabusa drag',
    'GSX-R drag',
    'motorcycle tuning',
    'parts ROI',
  ],
  authors: [{ name: 'Hritwik Mudhai' }],
  creator: 'Hritwik Mudhai',
  publisher: 'MotoQuant Pro',
  category: 'technology',
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

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={[inter.variable, spaceGrotesk.variable, jetbrainsMono.variable].join(' ')}
    >
      <body className="font-sans">
        {children}
        <div className="grain" aria-hidden="true" />
      </body>
    </html>
  );
}
