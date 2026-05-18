import Link from "next/link";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";

export const metadata = {
  title: "MotoQuant Blog — Motorcycle Drag Racing Physics & Indian Bike Breakdowns",
  description:
    "Physics-based quarter-mile breakdowns for Indian and global motorcycles: KTM Duke 390 vs RC 390, Pulsar NS400Z vs RC 390, RE Continental GT 650, Pulsar NS200 vs Apache RTR 200 4V, Hayabusa vs ZX-14R, KTM 1390 Super Duke R EVO, Hero Xtreme 200S 4V, R15 V4, plus 2-stroke expansion chamber theory and Aamby Valley November tuning.",
  keywords: [
    "motorcycle drag racing blog",
    "indian motorcycle quarter mile",
    "ktm duke 390 vs rc 390",
    "pulsar ns400z vs rc 390",
    "continental gt 650 drag",
    "ns200 vs apache rtr 200",
    "hayabusa vs zx-14r india",
    "r15 v4 quarter mile time",
    "ktm 1390 super duke",
    "2 stroke expansion chamber",
    "aamby valley tuning",
  ],
  alternates: { canonical: "https://motoquant.in/blog" },
};

const POSTS = [
  {
    slug: "ktm-duke-390-vs-rc-390-quarter-mile-physics",
    title: "KTM Duke 390 vs RC 390: Quarter-Mile Physics at Aamby Valley",
    date: "2026-05-18",
    readTime: "12 min",
    tags: ["KTM", "Duke 390", "RC 390", "Indian 400cc", "comparison"],
    excerpt:
      "MotoQuant simulates the RC 390 at ~13.5s and 166 km/h trap, the Duke 390 at ~13.7s and 162 km/h at Aamby Valley. Same engine, two tenths apart — almost all of it aerodynamic. Plus four cost-per-tenth mods under ₹25,000 and a look at the Fast Track Racing 11.342s record.",
  },
  {
    slug: "pulsar-ns400z-quarter-mile-physics",
    title: "Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)",
    date: "2026-05-18",
    readTime: "12 min",
    tags: ["Bajaj", "Pulsar NS400Z", "KTM RC 390", "Indian 400cc", "physics"],
    excerpt:
      "MotoQuant simulates the Pulsar NS400Z at ~13.8s and 158 km/h trap at Aamby Valley. A stock RC 390 still beats it by 0.3s. Physics-based explanation of the 23 kg, the gearing, and the Cd that the press release glossed over — plus three cost-per-tenth mods under ₹22,000.",
  },
  {
    slug: "re-continental-gt-650-quarter-mile-physics",
    title: "Royal Enfield Continental GT 650 Quarter-Mile Physics",
    date: "2026-05-18",
    readTime: "10 min",
    tags: ["Royal Enfield", "Continental GT 650", "Indian 650cc", "cafe racer"],
    excerpt:
      "MotoQuant simulates the RE Continental GT 650 at ~14.1s and 158 km/h trap. Why the 47 hp / 52 Nm air/oil-cooled twin is rev-limited rather than power-limited — and the ₹7,800 sprocket-and-tire combo that closes most of the gap.",
  },
  {
    slug: "pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics",
    title: "Pulsar NS200 vs Apache RTR 200 4V: Which Wins the Quarter Mile?",
    date: "2026-05-18",
    readTime: "11 min",
    tags: [
      "Bajaj",
      "Pulsar NS200",
      "TVS",
      "Apache RTR 200 4V",
      "Indian 200cc",
      "comparison",
    ],
    excerpt:
      "MotoQuant simulates the NS200 at ~15.9s and the Apache RTR 200 4V at ~16.4s under matched Aamby Valley conditions. Spec-by-spec physics breakdown plus the top three cost-per-tenth mods under ₹15,000 for each.",
  },
  {
    slug: "how-a-2-stroke-expansion-chamber-actually-works",
    title: "How a 2-Stroke Expansion Chamber Actually Works",
    date: "2026-05-08",
    readTime: "11 min",
    tags: ["2-stroke", "expansion chamber", "physics", "RX100", "RD350"],
    excerpt:
      "A pressure wave at 500 m/s, a tuned-RPM peak about 1,500 rpm wide, and a +0.494 s simulator bias on the 2T cluster. Why the pipe IS the engine on an RX100, RD350, or RGV250 — and what that means for cost-per-tenth at an Indian drag strip.",
  },
  {
    slug: "hayabusa-vs-zx-14r-which-is-faster",
    title: "Hayabusa vs ZX-14R: Which Is Faster Off the Line?",
    date: "2026-05-08",
    readTime: "11 min",
    tags: [
      "Suzuki",
      "Hayabusa",
      "Kawasaki",
      "ZX-14R",
      "hyper sport",
      "comparison",
    ],
    excerpt:
      "MotoQuant simulates the Hayabusa Gen1 reference at 10.471s and pegs the ZX-14R 2012 with a slim ~0.12 second ET advantage under matched conditions. Spec-by-spec breakdown of the two flagship hyper-bikes — where each one wins, and why.",
  },
  {
    slug: "hero-xtreme-200s-4v-quarter-mile-physics",
    title: "Hero Xtreme 200S 4V Quarter-Mile Physics: 200cc Commuter Drag",
    date: "2026-05-08",
    readTime: "9 min",
    tags: ["Hero", "Xtreme 200S 4V", "Indian 200cc", "commuter sport"],
    excerpt:
      "MotoQuant simulates the Hero Xtreme 200S 4V at 17.40s and 125 km/h trap. Why the 19.1 hp / 17.35 Nm 4-valve oil-cooled single is gearing-limited, not power-limited — and the two ₹3,600 mods that close most of the gap.",
  },
  {
    slug: "ktm-1390-super-duke-r-evo-quarter-mile-physics",
    title: "KTM 1390 Super Duke R EVO Quarter-Mile Physics Breakdown",
    date: "2026-05-08",
    readTime: "9 min",
    tags: ["KTM", "1390 Super Duke R", "physics", "litre naked"],
    excerpt:
      "MotoQuant simulates the 2024 KTM 1390 Super Duke R EVO at 10.225s and 237 km/h trap. MCN clocked stock test bikes at 9.95s. Here is exactly what the 0.275s gap is — and what actually limits the bike at the strip.",
  },
  {
    slug: "how-the-motoquant-physics-engine-works",
    title: "How the MotoQuant Physics Engine Works",
    date: "2026-04-27",
    readTime: "14 min",
    tags: ["physics", "engine", "validation", "methodology"],
    excerpt:
      "A first-principles tour of the 15-sub-model RK4 physics engine. Engine torque curves, Pacejka tires, clutch slip dynamics, weight transfer — what we simulate, what we validate against, and what the residual error actually means.",
  },
  {
    slug: "the-physics-of-a-perfect-launch",
    title: "The Physics of a Perfect Launch",
    date: "2026-04-24",
    readTime: "8 min",
    tags: ["physics", "launch control", "clutch"],
    excerpt:
      "Clutch engagement RPM, tire slip ratio, and weight transfer work together in the first 0.4 seconds. Getting any one wrong costs you tenths. Here is what the math says.",
  },
  {
    slug: "why-your-r15-wont-hit-14s",
    title: "Why Your R15 Won't Hit 14s (And What Will Actually Help)",
    date: "2026-04-24",
    readTime: "10 min",
    tags: ["small-cc", "Yamaha R15", "Indian bikes", "tuning"],
    excerpt:
      "The Yamaha YZF-R15 V3 should run ~14.5s based on factory power. Most stock bikes run 15.5–16s. The gap is not about engine power — it is about gearing, clutch slip, and traction. We break down every second.",
  },
  {
    slug: "how-to-tune-for-aamby-valley-in-november",
    title: "How to Tune for Aamby Valley in November",
    date: "2026-04-24",
    readTime: "6 min",
    tags: ["venue", "Aamby Valley", "weather", "conditions"],
    excerpt:
      "November at Aamby Valley means density altitude around 1100 m, 18–24°C, and concrete with a good grip coefficient. Every one of these numbers changes your optimal tune. Here is the MotoQuant venue analysis.",
  },
];

function PostCard({ post }) {
  return (
    <Link href={`/blog/${post.slug}`} className="block group">
      <article className="h-full glass rounded-xl border border-white/10 p-6 hover:border-brand-orange/40 transition-colors">
        <div className="flex flex-wrap gap-1.5 mb-4">
          {post.tags.map((t) => (
            <span
              key={t}
              className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
            >
              {t}
            </span>
          ))}
        </div>
        <h2 className="font-display font-bold text-xl text-white mb-3 group-hover:text-brand-orange transition-colors leading-snug">
          {post.title}
        </h2>
        <p className="text-white/60 text-sm leading-relaxed mb-4">
          {post.excerpt}
        </p>
        <div className="flex items-center justify-between">
          <div className="font-mono text-[10px] text-white/40 uppercase tracking-wide">
            {new Date(post.date).toLocaleDateString("en-IN", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}{" "}
            · {post.readTime} read
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
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

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
              Technical deep-dives on motorcycle physics, tuning strategy, and
              data analysis. Written for the Indian drag racing community.
            </p>
          </header>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {POSTS.map((post) => (
              <PostCard key={post.slug} post={post} />
            ))}
          </div>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
