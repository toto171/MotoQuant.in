import Link from 'next/link';

const DOC_PAGES = [
  { href: '/docs/getting-started', label: 'Getting Started' },
  { href: '/docs/physics', label: 'Physics Whitepaper' },
  { href: '/docs/validation', label: 'Validation Data' },
];

export const metadata = {
  title: { template: '%s — MotoQuant Docs', default: 'MotoQuant Docs' },
};

export default function DocsLayout({ children }) {
  return (
    <div className="min-h-screen bg-ink-0 text-white">
      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 h-16 backdrop-blur bg-black/80 border-b border-brand-orange/10 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="text-xl font-display font-bold tracking-tight">
              <span className="text-gradient-orange">Moto</span><span>Quant</span>
            </div>
            <div className="ml-2 px-2 py-1 rounded text-xs font-mono font-semibold text-brand-accent border border-brand-accent/30 bg-brand-accent/5">Pro</div>
          </Link>
          <div className="hidden md:flex gap-6 items-center text-sm font-mono">
            <Link href="/simulator" className="text-white/60 hover:text-white transition-colors">Simulator</Link>
            <Link href="/features" className="text-white/60 hover:text-white transition-colors">Features</Link>
            <Link href="/docs/getting-started" className="text-brand-orange">Docs</Link>
            <Link href="/blog" className="text-white/60 hover:text-white transition-colors">Blog</Link>
          </div>
          <Link href="/simulator" className="px-4 py-2 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">
            Try free
          </Link>
        </div>
      </nav>

      <div className="flex pt-16 min-h-screen">
        {/* Sidebar */}
        <aside className="hidden md:block w-56 shrink-0 border-r border-brand-orange/10 pt-10 px-4 sticky top-16 self-start h-[calc(100vh-4rem)] overflow-y-auto">
          <div className="text-[10px] font-mono text-white/40 uppercase tracking-widest mb-4">Documentation</div>
          <nav className="space-y-1">
            {DOC_PAGES.map(p => (
              <Link
                key={p.href}
                href={p.href}
                className="block px-3 py-2 rounded-lg text-sm font-mono text-white/60 hover:text-white hover:bg-white/5 transition-colors"
              >
                {p.label}
              </Link>
            ))}
          </nav>
          <div className="mt-8 pt-8 border-t border-brand-orange/10">
            <div className="text-[10px] font-mono text-white/40 uppercase tracking-widest mb-3">Also see</div>
            <nav className="space-y-1">
              {[
                { href: '/features', label: 'Features' },
                { href: '/blog', label: 'Blog' },
                { href: '/about', label: 'About' },
              ].map(p => (
                <Link key={p.href} href={p.href} className="block px-3 py-2 rounded-lg text-xs font-mono text-white/40 hover:text-white/70 hover:bg-white/5 transition-colors">
                  {p.label}
                </Link>
              ))}
            </nav>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 min-w-0 pt-8 pb-24 px-6 md:px-12 max-w-3xl">
          {children}
        </main>
      </div>

      <footer className="border-t border-brand-orange/10 py-8 px-6 text-center text-white/40 text-xs font-mono">
        <p>© {new Date().getFullYear()} MotoQuant Pro · <Link href="/" className="hover:text-brand-orange transition-colors">motoquant.in</Link></p>
      </footer>
    </div>
  );
}
