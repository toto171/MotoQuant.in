import './globals.css';

export const metadata = {
  title: 'MotoQuant Pro — The Physics of Faster',
  description: 'First-principles physics simulation for quarter-mile drag racing. Predict ET, optimize builds, and understand what actually moves the needle on the strip.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
