import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import DocsSidebarNav from './DocsSidebarNav';
import DocsMobileNav from './DocsMobileNav';

const DOC_PAGES = [
  { href: '/docs/getting-started', label: 'Getting Started' },
  { href: '/docs/physics',         label: 'Physics Whitepaper' },
  { href: '/docs/validation',      label: 'Validation Data' },
  { href: '/whitepaper',           label: 'MotoQuant Whitepaper' },
];

export const metadata = {
  title:    { template: '%s — MotoQuant Docs', default: 'MotoQuant Docs — Motorcycle Drag Racing Physics Documentation' },
  description: 'Documentation for the MotoQuant Pro motorcycle quarter-mile simulator — getting started, physics whitepaper (RK4 integrator + Pacejka tire model + SAE J1349 dyno correction), and validation data covering 74 published timeslips. Indian drag racing reference for Aamby Valley, MMRT, BIC, and Kari.',
  keywords: [
    'motoquant docs',
    'motorcycle drag racing documentation',
    'motorcycle physics simulator guide',
    'pacejka tire model documentation',
    'rk4 motorcycle simulator docs',
    'motorcycle quarter mile physics reference',
    'drag racing simulator validation',
    'aamby valley drag setup guide',
    'mmrt motorcycle tuning guide',
    'indian drag racing physics reference',
  ],
  alternates: { canonical: 'https://motoquant.in/docs' },
};

export default function DocsLayout({ children }) {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />

      <div className="flex pt-16 min-h-[calc(100vh-4rem)]">
        {/* Sidebar */}
        <aside className="hidden md:block w-60 shrink-0 border-r border-white/5 pt-12 px-4 sticky top-16 self-start h-[calc(100vh-4rem)] overflow-y-auto">
          <div className="label-mono mb-4 px-3">
            Documentation
          </div>
          <DocsSidebarNav pages={DOC_PAGES} />
          <div className="mt-10 px-3">
            <div className="label-mono mb-3">
              Reference baselines
            </div>
            <div className="card p-3">
              <ul className="space-y-2 text-[11px] font-mono tabular-nums">
                <li className="text-white/55 flex justify-between"><span>K5</span><span className="text-white/85">9.9331s</span></li>
                <li className="text-white/55 flex justify-between"><span>R1 4C8</span><span className="text-white/85">10.1436s</span></li>
                <li className="text-white/55 flex justify-between"><span>Hayabusa</span><span className="text-white/85">10.3633s</span></li>
              </ul>
              <div className="mt-3 text-[10px] font-mono text-signal-go">Δ ±0.0000 since Jul 13 2026</div>
            </div>
          </div>
        </aside>

        <main className="flex-1 min-w-0 px-6 sm:px-10 py-12 max-w-4xl">
          {/* Mobile docs nav — the sidebar is hidden below md, so phones get
              a collapsible section list above the content instead. */}
          <DocsMobileNav pages={DOC_PAGES} />
          {children}
        </main>
      </div>

      <SiteFooter />
    </div>
  );
}
