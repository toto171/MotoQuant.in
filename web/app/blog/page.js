import { Suspense } from "react";
import Link from "next/link";
import SiteNav from "../../components/SiteNav";
import SiteFooter from "../../components/SiteFooter";
import EndOfBlogIndexCta from "./EndOfBlogIndexCta";

export const metadata = {
  title:
    "MotoQuant Blog — Motorcycle Drag Racing Physics & Indian Bike Breakdowns",
  description:
    "Physics-based quarter-mile breakdowns for Indian and global motorcycles: Triumph Street Triple 765 R, KTM 890 Duke R India grey-market deep-dive, best mods for KTM RC 390 ranked by cost-per-tenth, Kawasaki Ninja 400 vs ZX-4R, MMRT Chennai venue tuning, Yamaha XSR900 GP vs MT-09, Kawasaki Ninja ZX-4R, Yamaha MT-125 vs XSR125, CFMoto 800NK, KTM Duke 390 vs RC 390, Pulsar NS400Z, RE Continental GT 650, Pulsar NS200 vs Apache RTR 200 4V, Hayabusa vs ZX-14R, KTM 1390 Super Duke R EVO, Hero Xtreme 200S 4V, R15 V4, plus 2-stroke expansion chamber theory and Aamby Valley November tuning.",
  keywords: [
    "motorcycle drag racing blog",
    "aprilia tuono 660 factory quarter mile",
    "tuono 660 factory drag time india",
    "tuono 660 factory vs base tuono",
    "tuono 660 factory vs rs 660",
    "tuono 660 factory price india",
    "triumph street triple 765r quarter mile",
    "street triple 765 r india drag race",
    "triumph 765 india price",
    "indian motorcycle quarter mile",
    "best mods for ktm rc 390 india",
    "rc 390 cost per tenth",
    "rc 390 ecu flash price india",
    "rc 390 performance upgrade cost",
    "ktm 390 powertronic stage 1",
    "mmrt chennai drag racing motorcycle",
    "madras motor race track quarter mile",
    "how to tune for mmrt chennai",
    "mmrt vs aamby valley",
    "kari motor speedway drag racing",
    "yamaha xsr900 gp vs mt-09",
    "xsr900 gp quarter mile",
    "mt-09 quarter mile time",
    "yamaha cp3 triple drag",
    "kawasaki ninja zx-4r quarter mile",
    "zx-4r vs zx-4rr",
    "zx-4r india price",
    "yamaha mt-125 quarter mile",
    "yamaha xsr125 quarter mile",
    "mt-125 vs xsr125",
    "cfmoto 800nk quarter mile",
    "cfmoto 800nk india price",
    "ktm duke 390 vs rc 390",
    "pulsar ns400z vs rc 390",
    "continental gt 650 drag",
    "ns200 vs apache rtr 200",
    "hayabusa vs zx-14r india",
    "r15 v4 quarter mile time",
    "ktm 1390 super duke",
    "yezdi roadster quarter mile",
    "yezdi roadster drag time",
    "yezdi 334 platform",
    "2 stroke expansion chamber",
    "aamby valley tuning",
    "cfmoto 800nk vs ktm 790 duke",
    "pulsar n250 vs apache rtr 200 4v",
    "hayabusa 2026 gen 3 quarter mile india",
    "ktm 890 duke quarter mile",
    "ktm 890 duke r drag time india",
    "ktm 890 duke r quarter mile india",
    "ktm 890 duke r grey market india",
    "ktm 890 duke vs 890 duke r",
    "ktm 890 duke vs mt-09",
    "suzuki gsx-s750 quarter mile",
    "gsx-s750 drag time india",
    "honda cb500x quarter mile",
    "cb500x adventure drag time",
    "kawasaki ninja 400 quarter mile india",
    "ninja 400 vs zx-4r which is faster",
    "ninja 400 drag time india",
    "kawasaki zx-4r vs ninja 400",
    "kawasaki z900rs quarter mile",
    "z900rs india price",
    "z900rs vs z900",
    "z900rs vs xsr900",
    "z900rs cost per tenth",
  ],
  alternates: { canonical: "https://motoquant.in/blog" },
};

const POSTS = [
  {
    slug: "aprilia-tuono-660-factory-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "12 min",
    tags: ["Aprilia", "Tuono 660 Factory", "middleweight naked", "India", "physics"],
    title:
      "Aprilia Tuono 660 Factory Quarter-Mile Physics: 11.02s on the Strip",
    excerpt:
      "MotoQuant simulates the Aprilia Tuono 660 Factory at 11.02s and 215.7 km/h trap. 5 extra hp, 14 kg less, sharper gearing — where the 0.3s gap over the base Tuono 660 actually lives, and why the Factory trim is the value pick of the Indian middleweight-naked segment at ₹16.15 lakh.",
  },
  {
    slug: "triumph-street-triple-765r-quarter-mile-physics",
    date: "2026-05-24",
    readTime: "12 min",
    tags: ["Triumph", "Street Triple 765 R", "middleweight naked", "physics"],
    title:
      "Triumph Street Triple 765 R Quarter-Mile Physics: 118hp Triple at the Strip",
    excerpt:
      "MotoQuant simulates the Triumph Street Triple 765 R at 10.74s and 213 km/h trap. Cycle World clocked the 2023 model at 10.9s. How a 118hp inline-three beats a 124hp inline-four by 0.44s, why the 765 R is the fastest CBU under ₹12 lakh at the strip, and the ₹2,200 sprocket swap that starts the upgrade ladder.",
  },
  {
    slug: "kawasaki-z900rs-quarter-mile-physics",
    date: "2026-05-22",
    readTime: "10 min",
    tags: ["Kawasaki", "Z900RS", "retro naked", "physics"],
    title: "Kawasaki Z900RS Quarter-Mile Physics: Retro Tax on a 948cc I4",
    excerpt:
      "MotoQuant simulates the Kawasaki Z900RS at 11.18s and 196 km/h trap. MCN clocked 11.4s and 199 km/h on the stock bike. Where the 13 hp detune actually costs you tenths versus a Z900, why the 6,500 rpm torque peak makes the launch easier than most litre nakeds, and the ₹2,800 sprocket swap that buys 0.08 s.",
  },
  {
    slug: "ktm-890-duke-r-quarter-mile-india",
    title: "KTM 890 Duke R Quarter-Mile in India: 11.07s on the Grey Market",
    date: "2026-05-22",
    readTime: "12 min",
    tags: ["KTM", "890 Duke R", "India grey market", "mid-cc naked", "physics"],
    excerpt:
      "MotoQuant simulates the KTM 890 Duke R at 11.07s and 202 km/h trap at Aamby Valley — 0.35s quicker than the standard 890 Duke. Why almost every 890 Duke in India is actually the R variant, where the tenths come from, and the ₹46,400 Tier-1 stack that closes the gap to a stock MT-09.",
  },
  {
    slug: "best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth",
    title: "Best Mods for KTM RC 390 in India: A Cost-Per-Tenth Ladder",
    date: "2026-05-22",
    readTime: "13 min",
    tags: ["KTM", "RC 390", "Duke 390", "cost-per-tenth", "India mods"],
    excerpt:
      "Stock RC 390 runs a 13.5s. Fast Track Racing India ran 11.342s. MotoQuant ranks every mod by ₹/tenth: ₹950 sprocket drops 0.20s, ₹14,500 Powertronic Stage 1 drops 0.22s, full Tier 1-2 build runs a 12.78 for ₹39,100. Where the cheap tenths live and where diminishing returns kick in.",
  },
  {
    slug: "kawasaki-ninja-400-vs-zx-4r-quarter-mile-physics",
    title:
      "Kawasaki Ninja 400 vs ZX-4R: Parallel Twin vs Inline-Four at the Strip",
    date: "2026-05-22",
    readTime: "12 min",
    tags: ["Kawasaki", "Ninja 400", "ZX-4R", "Indian 400cc", "comparison"],
    excerpt:
      "MotoQuant simulates the Ninja 400 at ~13.1s and the ZX-4R at 12.681s and 192.6 km/h trap — same 400cc class, 0.4s apart. Architecture, redline, and the ₹3.7 lakh price gap explain everything. India cost-per-tenth mods for both bikes, and a modded Ninja 400 gets within 0.10s of a stock ZX-4R for ₹21,000.",
  },
  {
    slug: "suzuki-gsx-s750-vs-ktm-890-duke-quarter-mile",
    title: "Suzuki GSX-S750 vs KTM 890 Duke: Quarter-Mile Physics",
    date: "2026-05-18",
    readTime: "11 min",
    tags: [
      "Suzuki",
      "GSX-S750",
      "KTM",
      "890 Duke",
      "comparison",
      "mid-cc naked",
    ],
    excerpt:
      "MotoQuant simulates the GSX-S750 at 11.58s and the 890 Duke at 11.42s. The Duke weighs 27 kg less and wins by 0.16s — but the Suzuki inline-four claws back 3 km/h in trap speed. Physics-based breakdown of where each bike wins and loses, plus sprocket-first tuning strategy for both.",
  },
  {
    slug: "yezdi-roadster-quarter-mile-physics",
    title: "Yezdi Roadster Quarter-Mile Physics: 334cc Neo-Retro at the Strip",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Yezdi", "Roadster 334", "BG6 platform", "Indian retro", "physics"],
    excerpt:
      "MotoQuant simulates the Yezdi Roadster 334 at 15.42s and 138 km/h trap at Aamby Valley. 28.6 hp, 175 kg dry, BG6 platform shared with the Scrambler / Adventure 334 / Jawa 42 Bobber 350. Why the ₹6,500 sprocket swap is the cheapest tenth on the bike, and where the Roadster sits against the Classic 350 and Duke 390.",
  },
  {
    slug: "how-to-tune-for-mmrt-chennai",
    title: "How to Tune for MMRT Chennai: Sea-Level, Humid, Hot Track",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["MMRT", "Chennai", "venue", "tuning", "Tamil Nadu"],
    excerpt:
      "MMRT Chennai sits at 78 m altitude with 80% humidity and 30°C track temperatures most of the year. MotoQuant simulates the same Hayabusa 0.05s quicker at MMRT than Aamby Valley in November, with a higher trap speed but a slightly worse 60-foot. Venue-specific tuning math, month-by-month ET table, and four practical adjustments before you trailer the bike.",
  },
  {
    slug: "yamaha-xsr900-gp-vs-mt-09-quarter-mile-physics",
    title: "Yamaha XSR900 GP vs MT-09: Where the Heritage Tax Is Paid",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Yamaha", "XSR900 GP", "MT-09", "CP3 triple", "comparison"],
    excerpt:
      "MotoQuant simulates the Yamaha XSR900 GP at 10.98s and the MT-09 at 10.86s — same 890cc CP3 triple, same 6-speed cassette, 0.12s apart. Spec-by-spec physics breakdown of where the mass lives, why the fairing pays it back at top speed, and the Indian CBU pricing math.",
  },
  {
    slug: "kawasaki-ninja-zx-4r-quarter-mile-physics",
    title: "Kawasaki Ninja ZX-4R Quarter-Mile Physics: 400cc Inline-Four",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["Kawasaki", "Ninja ZX-4R", "400cc", "inline-four", "physics"],
    excerpt:
      "MotoQuant simulates the 2024 Kawasaki Ninja ZX-4R at 12.681s and 192.6 km/h trap. Why a 76 hp 400cc inline-four runs a 12.6 when every other 400-class bike runs a 13.5 — plus three mods under ₹30,000 that close the gap to the ZX-4RR.",
  },
  {
    slug: "yamaha-mt-125-xsr125-platform-physics",
    title: "Yamaha MT-125 vs XSR125: Same Engine, 0.10s Apart at the Strip",
    date: "2026-05-18",
    readTime: "10 min",
    tags: ["Yamaha", "MT-125", "XSR125", "A1 licence", "platform physics"],
    excerpt:
      "MotoQuant simulates the MT-125 at 19.123s and the XSR125 at 19.222s — same engine, same gearbox, same final drive, 0.10s apart. Where the tenth lives, why the heritage tax is paid in frontal area, and why the YZF-R125 beats both.",
  },
  {
    slug: "cfmoto-800nk-quarter-mile-physics",
    title: "CFMoto 800NK Quarter-Mile Physics: A KTM 790 Duke in Disguise",
    date: "2026-05-18",
    readTime: "11 min",
    tags: ["CFMoto", "800NK", "LC8c", "Indian mid-cc", "physics"],
    excerpt:
      "MotoQuant simulates the CFMoto 800NK at 11.386s and 203.2 km/h trap. The KTM-derived LC8c parallel twin sits at ₹9-12 lakh in India — the cheapest LC8c-engined bike on the market. Physics breakdown of where the tenths live and why a 95 hp parallel twin runs an 11.4.",
  },
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

          {/* GROWTH_EXP_006 — end-of-grid simulator CTA (default OFF, ?variant=B) */}
          <Suspense fallback={null}>
            <EndOfBlogIndexCta />
          </Suspense>
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}
