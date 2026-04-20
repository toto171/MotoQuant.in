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
  openGraph: {
    title: 'MotoQuant Pro — The Physics of Faster',
    description: 'First-principles physics simulation for quarter-mile drag racing. Predict ET, optimize builds, and understand what actually moves the needle on the strip.',
    url: 'https://motoquant.in',
    siteName: 'MotoQuant Pro',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
      },
    ],
    locale: 'en_IN',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MotoQuant Pro — The Physics of Faster',
    description: 'First-principles physics simulation for quarter-mile drag racing. Predict ET, optimize builds, and understand what actually moves the needle on the strip.',
    images: ['/og-image.png'],
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
