import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata = {
  title: 'MotoQuant Pro — The Physics of Faster',
  description: 'First-principles physics simulation for quarter-mile drag racing. Predict ET, optimise builds, and understand what actually moves the needle on the strip.',
  openGraph: {
    title: 'MotoQuant Pro — The Physics of Faster',
    description: 'First-principles quarter-mile simulation for the Indian drag racing community. Validated at Aamby Valley, MMRT, and beyond.',
    siteName: 'MotoQuant Pro',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
