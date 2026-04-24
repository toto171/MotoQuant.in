import Link from 'next/link';

export const metadata = {
  title: 'Blog — MotoQuant Pro',
  description: 'Technical articles on motorcycle drag racing physics, tuning strategy, and data analysis for the Indian racing community.',
  alternates: { canonical: 'https://motoquant.in/blog' },
};

const POSTS = [
  {
    slug: 'the-physics-of-a-perfect-launch',
    title: 'The Physics of a Perfect Launch',
    date: '2026-04-24',
    readTime: '8 min',
    tags: ['physics', 'launch control', 'clutch'],
    excerpt:
      'Clutch engagement RPM, tire slip ratio, and weight transfer work together in the first 0.4 seconds. Getting any one wrong costs you tenths. Here is what the math says.',
  },
  {
    slug: 'why-your-r15-wont-hit-14s',
    title: "Why Your R15 Won't Hit 14s (And What Will Actually Help)",
    date: '2026-04-24',
    readTime: '10 min',
    tags: ['small-cc', 'Yamaha R15', 'Indian bikes', 'tuning'],
    excerpt:
      'The Yamaha YZF-R15 V3 should run ~14.5s based on factory power. Most stock bikes run 15.5–16s. The gap is not about engine power — it is about gearing, clutch slip, and traction. We break down every second.',
  },
  {
    slug: 'how-to-tune-for-aamby-valley-in-november',
    title: 'How to Tune for Aamby Valley in November',
    date: '2026-04-24',
    readTime: '6 min',
    tags: ['venue', 'Aamby Valley', 'weather', 'conditions'],
    excerpt:
      'November at Aamby Valley means density altitude around 1100 m, 18–24°C, and concrete with a good grip coefficient. Every one of these numbers changes your optimal tune. Here is the MotoQuant venue analysis.',
  },
];

function PostCard({ post }) {
  return (
    <Link href={`/blog/${post.slug}`} className="block group">
      <article className="h-full glass rounded-xl border border-white/10 p-6 hover:border-brand-orange/40 transition-colors">
        <div className="flex flex-wrap gap-1.5 mb-4">
          {post.tags.map(t => (
            <span key={t} className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide">
              {t}
            </span>
          ))}
        </div>
        <h2 className="font-display font-bold text-xl text-white mb-3 group-hover:text-brand-orange transition-colors leading-snug">
          {post.title}
        </h2>
        <p className="text-white/60 text-sm leading-relaxed mb-4">{post.excerpt}</p>
        <div className="flex items-center justify-between">
          <div className="font-mono text-[10px] text-white/40 uppercase tracking-wide">
            {new Date(post.date).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })} · {post.readTime} read
          </div>
          <span className="text-brand-accent text-xs font-mono group-hover:text-brand-orange transition-colors">
            Read →
          </span>
        </div>
      </article>
    </Link>
  );
}

export default function BlogIndexPage() {
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
            <Link href="/bikes" className="text-white/60 hover:text-white transition-colors">Bikes</Link>
            <Link href="/features" className="text-white/60 hover:text-white transition-colors">Features</Link>
            <Link href="/blog" className="text-brand-orange">Blog</Link>
            <Link href="/about" className="text-white/60 hover:text-white transition-colors">About</Link>
          </div>
          <Link href="/simulator" className="px-4 py-2 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">
            Try free
          </Link>
        </div>
      </nav>

      <main className="pt-32 pb-24 px-6">
        <div className="max-w-5xl mx-auto">
          <header className="mb-16">
            <div className="mb-4 inline-block px-4 py-1.5 rounded-full border border-brand-orange/40 bg-brand-orange/10 text-xs font-mono text-brand-orange uppercase tracking-widest">
              MotoQuant Blog
            </div>
            <h1 className="font-display font-bold text-5xl md:text-6xl tracking-tighter text-gradient-orange mb-4">
              The physics of drag racing.
            </h1>
            <p className="text-white/60 text-lg max-w-2xl">
              Technical deep-dives on motorcycle physics, tuning strategy, and data analysis.
              Written for the Indian drag racing community.
            </p>
          </header>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {POSTS.map(post => (
              <PostCard key={post.slug} post={post} />
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t border-brand-orange/10 py-8 px-6 text-center text-white/40 text-xs font-mono">
        <p>© {new Date().getFullYear()} MotoQuant Pro · <Link href="/" className="hover:text-brand-orange transition-colors">motoquant.in</Link></p>
      </footer>
    </div>
  );
}
