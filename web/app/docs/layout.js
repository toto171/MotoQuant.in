import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import DocsSidebarNav from './DocsSidebarNav';
import DocsMobileNav from './DocsMobileNav';

const DOC_PAGES = [
  { href: '/docs/getting-started', label: 'Getting started' },
  { href: '/docs/glossary',        label: 'Glossary' },
  { href: '/docs/physics',         label: 'How the physics works' },
  { href: '/docs/validation',      label: 'Accuracy data' },
  { href: '/whitepaper',           label: 'Whitepaper' },
];

export const metadata = {
  title:    { template: '%s — MotoQuant Docs', default: 'MotoQuant Docs — Motorcycle Drag Racing Physics Documentation' },
  description: 'Documentation for the MotoQuant motorcycle quarter-mile simulator — getting started, physics whitepaper (RK4 integrator + Pacejka tire model + SAE J1349 dyno correction), and validation data covering 250 published benchmarks. Indian drag racing reference for Aamby Valley, MMRT, BIC, and Kari.',
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
        <aside className="hidden md:block w-60 shrink-0 border-r border-white/10 pt-12 px-4 sticky top-16 self-start h-[calc(100vh-4rem)] overflow-y-auto">
          <p className="mb-3 px-3 text-sm font-semibold text-white">Learn</p>
          <DocsSidebarNav pages={DOC_PAGES} />
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
