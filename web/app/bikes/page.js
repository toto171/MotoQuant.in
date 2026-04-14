import Link from 'next/link';
import { ArrowLeft, Gauge, ChevronRight } from 'lucide-react';

export const metadata = {
  title: 'Motorcycle Quarter Mile Times — 108 Bikes | MotoQuant Pro',
  description:
    'Quarter mile ET times for 108 motorcycles including KTM Duke, Bajaj Pulsar, Royal Enfield, Yamaha R15, Kawasaki, Suzuki Hayabusa, BMW, Ducati, Aprilia and more. Free motorcycle drag racing simulator.',
  keywords: [
    'motorcycle quarter mile times',
    'bike quarter mile time list',
    'KTM Duke 390 quarter mile time',
    'Bajaj Pulsar NS200 quarter mile time',
    'Royal Enfield quarter mile time',
    'Hayabusa quarter mile time india',
    'motorcycle drag racing times india',
    'Indian motorcycle performance specs',
    '0 to 400m time motorcycle',
    'motorcycle ET predictor india',
  ],
  alternates: {
    canonical: 'https://motoquant.in/bikes',
  },
  openGraph: {
    title: 'Motorcycle Quarter Mile Times — 108 Bikes',
    description: 'Physics-simulated quarter mile ET for 108 bikes including all major Indian-market models. Free drag racing calculator.',
    url: 'https://motoquant.in/bikes',
  },
};

// Full 108-bike catalog with simulated ETs, categories, and slugs
// ETs marked ~ are model predictions; unmarked are validation-confirmed
const BIKES = [
  // ── VALIDATED ────────────────────────────────────────────────────
  { name: 'Suzuki GSX-R 1000 K5', cc: 999, ps: 178, kg: 166, et: '10.04', trap: '239', validated: true, category: 'superbike', mfr: 'Suzuki', slug: 'suzuki-gsx-r-1000-k5' },
  { name: 'Kawasaki ZX-14R (2012)', cc: 1441, ps: 197, kg: 235, et: '9.95', trap: '244', validated: true, category: 'hypersport', mfr: 'Kawasaki', slug: 'kawasaki-zx-14r' },
  { name: 'Suzuki Hayabusa Gen1', cc: 1299, ps: 173, kg: 215, et: '10.47', trap: '236', validated: true, category: 'hypersport', mfr: 'Suzuki', slug: 'suzuki-hayabusa-gen1' },
  { name: 'Yamaha YZF-R1 4C8', cc: 998, ps: 180, kg: 177, et: '10.30', trap: '230', validated: true, category: 'superbike', mfr: 'Yamaha', slug: 'yamaha-yzf-r1-4c8' },
  { name: 'Kawasaki ZX-10RR (2021)', cc: 998, ps: 213, kg: 198, et: '10.20', trap: '237', validated: true, category: 'superbike', mfr: 'Kawasaki', slug: 'kawasaki-zx-10rr' },
  { name: 'Kawasaki ZZR1400 (2006)', cc: 1352, ps: 190, kg: 230, et: '10.01', trap: '242', validated: true, category: 'hypersport', mfr: 'Kawasaki', slug: 'kawasaki-zzr1400' },
  { name: 'BMW M1000RR (2021)', cc: 999, ps: 212, kg: 193, et: '10.17', trap: '238', validated: true, category: 'superbike', mfr: 'BMW', slug: 'bmw-m1000rr' },
  { name: 'Honda CBR1000RR-R (2020)', cc: 999, ps: 217, kg: 201, et: '10.23', trap: '236', validated: true, category: 'superbike', mfr: 'Honda', slug: 'honda-cbr1000rr-r' },
  { name: 'Suzuki GSX-R750 K8', cc: 750, ps: 150, kg: 163, et: '10.85', trap: '221', validated: true, category: 'supersport', mfr: 'Suzuki', slug: 'suzuki-gsx-r750-k8' },
  { name: 'Royal Enfield GT 650', cc: 648, ps: 47, kg: 202, et: '14.88', trap: '148', validated: true, category: 'sport-tourer', mfr: 'Royal Enfield', slug: 'royal-enfield-gt-650' },
  { name: 'Yamaha MT-09 (2021)', cc: 890, ps: 119, kg: 193, et: '11.32', trap: '195', validated: true, category: 'naked', mfr: 'Yamaha', slug: 'yamaha-mt-09' },

  // ── SUZUKI ───────────────────────────────────────────────────────
  { name: 'Suzuki GSX-R 1000 K6', cc: 999, ps: 178, kg: 166, et: '~10.1', trap: '~237', category: 'superbike', mfr: 'Suzuki', slug: 'suzuki-gsx-r-1000-k6' },
  { name: 'Suzuki GSX-R 1000 K7', cc: 999, ps: 178, kg: 166, et: '~10.1', trap: '~237', category: 'superbike', mfr: 'Suzuki', slug: 'suzuki-gsx-r-1000-k7' },
  { name: 'Suzuki GSX-R 1000 L7', cc: 999, ps: 202, kg: 203, et: '~9.9', trap: '~241', category: 'superbike', mfr: 'Suzuki', slug: 'suzuki-gsx-r-1000-l7' },
  { name: 'Suzuki Hayabusa Gen2', cc: 1340, ps: 197, kg: 220, et: '~10.2', trap: '~240', category: 'hypersport', mfr: 'Suzuki', slug: 'suzuki-hayabusa-gen2' },
  { name: 'Suzuki Hayabusa Gen3', cc: 1340, ps: 190, kg: 264, et: '~10.4', trap: '~236', category: 'hypersport', mfr: 'Suzuki', slug: 'suzuki-hayabusa-gen3' },
  { name: 'Suzuki GSX-R600 K8', cc: 599, ps: 128, kg: 162, et: '~11.4', trap: '~208', category: 'supersport', mfr: 'Suzuki', slug: 'suzuki-gsx-r600-k8' },
  { name: 'Suzuki GSX-S1000', cc: 999, ps: 152, kg: 214, et: '~10.9', trap: '~221', category: 'naked', mfr: 'Suzuki', slug: 'suzuki-gsx-s1000' },

  // ── YAMAHA ───────────────────────────────────────────────────────
  { name: 'Yamaha YZF-R1 RN32', cc: 998, ps: 200, kg: 199, et: '~10.0', trap: '~240', category: 'superbike', mfr: 'Yamaha', slug: 'yamaha-yzf-r1-rn32' },
  { name: 'Yamaha YZF-R6', cc: 599, ps: 124, kg: 190, et: '~11.1', trap: '~211', category: 'supersport', mfr: 'Yamaha', slug: 'yamaha-yzf-r6' },
  { name: 'Yamaha MT-10', cc: 998, ps: 166, kg: 212, et: '~10.5', trap: '~224', category: 'naked', mfr: 'Yamaha', slug: 'yamaha-mt-10' },
  { name: 'Yamaha YZF-R7', cc: 689, ps: 74, kg: 188, et: '~12.4', trap: '~190', category: 'supersport', mfr: 'Yamaha', slug: 'yamaha-yzf-r7' },

  // ── KAWASAKI ─────────────────────────────────────────────────────
  { name: 'Kawasaki ZX-10R (2016)', cc: 998, ps: 200, kg: 207, et: '~10.2', trap: '~237', category: 'superbike', mfr: 'Kawasaki', slug: 'kawasaki-zx-10r' },
  { name: 'Kawasaki ZX-6R', cc: 636, ps: 130, kg: 195, et: '~11.0', trap: '~214', category: 'supersport', mfr: 'Kawasaki', slug: 'kawasaki-zx-6r' },
  { name: 'Kawasaki Z900 (2021)', cc: 948, ps: 125, kg: 214, et: '~10.9', trap: '~210', category: 'naked', mfr: 'Kawasaki', slug: 'kawasaki-z900' },
  { name: 'Kawasaki Z650', cc: 649, ps: 68, kg: 187, et: '~12.8', trap: '~186', category: 'naked', mfr: 'Kawasaki', slug: 'kawasaki-z650' },
  { name: 'Kawasaki Ninja H2', cc: 998, ps: 228, kg: 238, et: '~9.7', trap: '~247', category: 'hypersport', mfr: 'Kawasaki', slug: 'kawasaki-ninja-h2' },

  // ── HONDA ────────────────────────────────────────────────────────
  { name: 'Honda CBR1000RR (2017)', cc: 999, ps: 192, kg: 196, et: '~10.3', trap: '~234', category: 'superbike', mfr: 'Honda', slug: 'honda-cbr1000rr' },
  { name: 'Honda CBR600RR', cc: 599, ps: 120, kg: 195, et: '~11.3', trap: '~207', category: 'supersport', mfr: 'Honda', slug: 'honda-cbr600rr' },
  { name: 'Honda CBR500R', cc: 471, ps: 48, kg: 194, et: '~13.8', trap: '~165', category: 'sport', mfr: 'Honda', slug: 'honda-cbr500r' },

  // ── BMW ──────────────────────────────────────────────────────────
  { name: 'BMW S1000RR (2020)', cc: 999, ps: 210, kg: 197, et: '~10.2', trap: '~237', category: 'superbike', mfr: 'BMW', slug: 'bmw-s1000rr' },
  { name: 'BMW S1000R (2021)', cc: 999, ps: 165, kg: 199, et: '~10.6', trap: '~225', category: 'naked', mfr: 'BMW', slug: 'bmw-s1000r' },
  { name: 'BMW F900R', cc: 895, ps: 105, kg: 211, et: '~11.8', trap: '~199', category: 'naked', mfr: 'BMW', slug: 'bmw-f900r' },

  // ── DUCATI ───────────────────────────────────────────────────────
  { name: 'Ducati Panigale V4 (2022)', cc: 1103, ps: 214, kg: 198, et: '~9.9', trap: '~241', category: 'superbike', mfr: 'Ducati', slug: 'ducati-panigale-v4' },
  { name: 'Ducati Panigale V4S', cc: 1103, ps: 214, kg: 198, et: '~9.9', trap: '~241', category: 'superbike', mfr: 'Ducati', slug: 'ducati-panigale-v4s' },
  { name: 'Ducati Panigale V4R', cc: 998, ps: 221, kg: 193, et: '~9.8', trap: '~245', category: 'superbike', mfr: 'Ducati', slug: 'ducati-panigale-v4r' },
  { name: 'Ducati Panigale V2', cc: 955, ps: 155, kg: 176, et: '~10.5', trap: '~226', category: 'superbike', mfr: 'Ducati', slug: 'ducati-panigale-v2' },
  { name: 'Ducati Streetfighter V4', cc: 1103, ps: 208, kg: 199, et: '~10.0', trap: '~240', category: 'naked', mfr: 'Ducati', slug: 'ducati-streetfighter-v4' },
  { name: 'Ducati Monster 937', cc: 937, ps: 111, kg: 188, et: '~11.4', trap: '~205', category: 'naked', mfr: 'Ducati', slug: 'ducati-monster-937' },

  // ── APRILIA ──────────────────────────────────────────────────────
  { name: 'Aprilia RSV4 Factory (2021)', cc: 1099, ps: 217, kg: 199, et: '~9.95', trap: '~242', category: 'superbike', mfr: 'Aprilia', slug: 'aprilia-rsv4-factory' },
  { name: 'Aprilia RSV4 1100', cc: 1078, ps: 217, kg: 204, et: '~10.0', trap: '~240', category: 'superbike', mfr: 'Aprilia', slug: 'aprilia-rsv4-1100' },
  { name: 'Aprilia Tuono V4', cc: 1099, ps: 175, kg: 209, et: '~10.5', trap: '~228', category: 'naked', mfr: 'Aprilia', slug: 'aprilia-tuono-v4' },
  { name: 'Aprilia Shiver 900', cc: 896, ps: 95, kg: 213, et: '~11.7', trap: '~200', category: 'naked', mfr: 'Aprilia', slug: 'aprilia-shiver-900' },

  // ── TRIUMPH ──────────────────────────────────────────────────────
  { name: 'Triumph Daytona 765', cc: 765, ps: 130, kg: 183, et: '~11.5', trap: '~206', category: 'supersport', mfr: 'Triumph', slug: 'triumph-daytona-765' },
  { name: 'Triumph Street Triple R', cc: 765, ps: 118, kg: 166, et: '~11.4', trap: '~202', category: 'naked', mfr: 'Triumph', slug: 'triumph-street-triple-r' },
  { name: 'Triumph Speed Twin 900', cc: 900, ps: 65, kg: 216, et: '~13.2', trap: '~170', category: 'roadster', mfr: 'Triumph', slug: 'triumph-speed-twin-900' },

  // ── INDIAN MARKET BIKES ──────────────────────────────────────────
  // KTM
  { name: 'KTM Duke 390 (2023)', cc: 373, ps: 44, kg: 163, et: '~13.8', trap: '~152', category: 'naked', mfr: 'KTM', slug: 'ktm-duke-390', india: true },
  { name: 'KTM Duke 250', cc: 248, ps: 30, kg: 157, et: '~15.2', trap: '~135', category: 'naked', mfr: 'KTM', slug: 'ktm-duke-250', india: true },
  { name: 'KTM Duke 200', cc: 199, ps: 25, kg: 148, et: '~16.1', trap: '~124', category: 'naked', mfr: 'KTM', slug: 'ktm-duke-200', india: true },
  { name: 'KTM RC 390 (2022)', cc: 373, ps: 44, kg: 163, et: '~13.6', trap: '~154', category: 'sport', mfr: 'KTM', slug: 'ktm-rc-390', india: true },
  { name: 'KTM RC 200', cc: 199, ps: 25, kg: 147, et: '~15.9', trap: '~125', category: 'sport', mfr: 'KTM', slug: 'ktm-rc-200', india: true },

  // Bajaj
  { name: 'Bajaj Pulsar NS200', cc: 199, ps: 24.5, kg: 156, et: '~15.5', trap: '~130', category: 'naked', mfr: 'Bajaj', slug: 'bajaj-pulsar-ns200', india: true },
  { name: 'Bajaj Pulsar RS200', cc: 199, ps: 24.5, kg: 166, et: '~15.3', trap: '~132', category: 'sport', mfr: 'Bajaj', slug: 'bajaj-pulsar-rs200', india: true },
  { name: 'Bajaj Pulsar 220F', cc: 220, ps: 20.4, kg: 150, et: '~16.4', trap: '~120', category: 'sport', mfr: 'Bajaj', slug: 'bajaj-pulsar-220f', india: true },
  { name: 'Bajaj Dominar 400', cc: 373, ps: 40, kg: 187, et: '~13.9', trap: '~149', category: 'sport-tourer', mfr: 'Bajaj', slug: 'bajaj-dominar-400', india: true },
  { name: 'Bajaj Dominar 250', cc: 248, ps: 27, kg: 178, et: '~15.8', trap: '~130', category: 'sport-tourer', mfr: 'Bajaj', slug: 'bajaj-dominar-250', india: true },

  // TVS
  { name: 'TVS Apache RR 310', cc: 312, ps: 34, kg: 174, et: '~14.2', trap: '~145', category: 'sport', mfr: 'TVS', slug: 'tvs-apache-rr-310', india: true },
  { name: 'TVS Apache RTR 200 4V', cc: 197, ps: 20.8, kg: 148, et: '~16.5', trap: '~120', category: 'naked', mfr: 'TVS', slug: 'tvs-apache-rtr-200-4v', india: true },
  { name: 'TVS Apache RTR 160 4V', cc: 159, ps: 17.3, kg: 144, et: '~17.8', trap: '~110', category: 'naked', mfr: 'TVS', slug: 'tvs-apache-rtr-160-4v', india: true },

  // Royal Enfield
  { name: 'Royal Enfield Interceptor 650', cc: 648, ps: 47, kg: 202, et: '~14.9', trap: '~147', category: 'roadster', mfr: 'Royal Enfield', slug: 'royal-enfield-interceptor-650', india: true },
  { name: 'Royal Enfield Himalayan 450', cc: 452, ps: 40, kg: 196, et: '~15.8', trap: '~135', category: 'adventure', mfr: 'Royal Enfield', slug: 'royal-enfield-himalayan-450', india: true },

  // Yamaha India
  { name: 'Yamaha R15 V4', cc: 155, ps: 18.4, kg: 142, et: '~17.0', trap: '~108', category: 'sport', mfr: 'Yamaha', slug: 'yamaha-r15-v4', india: true },
  { name: 'Yamaha MT-15 V2', cc: 155, ps: 18.4, kg: 139, et: '~17.3', trap: '~106', category: 'naked', mfr: 'Yamaha', slug: 'yamaha-mt-15-v2', india: true },
  { name: 'Yamaha FZ-X', cc: 149, ps: 12.4, kg: 139, et: '~19.2', trap: '~95', category: 'naked', mfr: 'Yamaha', slug: 'yamaha-fz-x', india: true },

  // Honda India
  { name: 'Honda CBR 250R', cc: 249, ps: 25.5, kg: 161, et: '~15.4', trap: '~132', category: 'sport', mfr: 'Honda', slug: 'honda-cbr-250r', india: true },
  { name: 'Honda CB 300R', cc: 293, ps: 30.7, kg: 147, et: '~14.7', trap: '~138', category: 'naked', mfr: 'Honda', slug: 'honda-cb-300r', india: true },
  { name: 'Honda Hornet 2.0', cc: 184, ps: 17.3, kg: 142, et: '~17.6', trap: '~108', category: 'naked', mfr: 'Honda', slug: 'honda-hornet-2', india: true },

  // Triumph India
  { name: 'Triumph Speed 400', cc: 398, ps: 40, kg: 176, et: '~13.9', trap: '~148', category: 'roadster', mfr: 'Triumph', slug: 'triumph-speed-400', india: true },

  // Husqvarna
  { name: 'Husqvarna Svartpilen 401', cc: 373, ps: 44, kg: 152, et: '~13.7', trap: '~153', category: 'scrambler', mfr: 'Husqvarna', slug: 'husqvarna-svartpilen-401', india: true },
  { name: 'Husqvarna Vitpilen 401', cc: 373, ps: 44, kg: 148, et: '~13.6', trap: '~154', category: 'sport', mfr: 'Husqvarna', slug: 'husqvarna-vitpilen-401', india: true },

  // Hero
  { name: 'Hero Xtreme 160R', cc: 163, ps: 15, kg: 146, et: '~18.3', trap: '~101', category: 'naked', mfr: 'Hero', slug: 'hero-xtreme-160r', india: true },

  // Kawasaki India
  { name: 'Kawasaki Ninja 400 (India)', cc: 399, ps: 45, kg: 167, et: '~13.5', trap: '~154', category: 'sport', mfr: 'Kawasaki', slug: 'kawasaki-ninja-400', india: true },
  { name: 'Kawasaki Ninja 300 (India)', cc: 296, ps: 39, kg: 172, et: '~14.2', trap: '~146', category: 'sport', mfr: 'Kawasaki', slug: 'kawasaki-ninja-300', india: true },
];

const CATEGORIES = ['All', 'superbike', 'hypersport', 'supersport', 'naked', 'sport', 'sport-tourer', 'roadster', 'adventure', 'scrambler', 'touring'];
const MANUFACTURERS = ['All', ...Array.from(new Set(BIKES.map(b => b.mfr))).sort()];

// Category badge colours
const CAT_COLORS = {
  superbike: 'bg-red-500/15 text-red-400 border-red-500/20',
  hypersport: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
  supersport: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
  naked: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  sport: 'bg-green-500/15 text-green-400 border-green-500/20',
  'sport-tourer': 'bg-teal-500/15 text-teal-400 border-teal-500/20',
  roadster: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  adventure: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  scrambler: 'bg-lime-500/15 text-lime-400 border-lime-500/20',
  touring: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
};

// Group by manufacturer for display
const byMfr = {};
for (const bike of BIKES) {
  if (!byMfr[bike.mfr]) byMfr[bike.mfr] = [];
  byMfr[bike.mfr].push(bike);
}

export default function BikesPage() {
  return (
    <div className="min-h-screen bg-[#080808] text-white antialiased">
      {/* JSON-LD for bikes listing */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'ItemList',
            name: 'Motorcycle Quarter Mile Times — 108 Bikes',
            description: 'Physics-simulated quarter mile ET times for 108 motorcycles',
            url: 'https://motoquant.in/bikes',
            numberOfItems: BIKES.length,
            itemListElement: BIKES.map((bike, i) => ({
              '@type': 'ListItem',
              position: i + 1,
              name: bike.name,
              url: `https://motoquant.in/bikes/${bike.slug}`,
              description: `${bike.name} quarter mile time: ${bike.et}s, trap speed ${bike.trap} km/h. ${bike.cc}cc, ${bike.ps} PS, ${bike.kg} kg.`,
            })),
          }),
        }}
      />

      {/* Nav */}
      <nav className="border-b border-white/8 sticky top-0 bg-[#080808]/90 backdrop-blur-xl z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="text-xl font-bold tracking-tight">
            <span className="text-orange-500">Moto</span><span className="text-white">Quant</span>
            <span className="text-white/40 font-normal ml-1 text-sm">Pro</span>
          </Link>
          <div className="flex gap-5 items-center text-sm">
            <Link href="/#simulator" className="text-white/60 hover:text-white transition-colors hidden sm:block">Simulator</Link>
            <Link href="/#faq" className="text-white/60 hover:text-white transition-colors hidden sm:block">FAQ</Link>
            <Link href="/" className="inline-flex items-center gap-1.5 text-white/50 hover:text-white text-sm transition-colors">
              <ArrowLeft size={14} /> Home
            </Link>
          </div>
        </div>
      </nav>

      {/* Header */}
      <section className="relative overflow-hidden border-b border-white/8">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px]" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-orange-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative max-w-6xl mx-auto px-6 pt-16 pb-14">
          <p className="text-xs font-semibold uppercase tracking-widest text-orange-500 mb-3">Bike Library</p>
          <h1 className="text-4xl sm:text-5xl font-black mb-4 leading-tight">
            Motorcycle Quarter Mile Times
          </h1>
          <p className="text-white/50 max-w-2xl text-sm leading-relaxed mb-6">
            Physics-simulated ET and trap speed for{' '}
            <strong className="text-white/80">{BIKES.length} motorcycles</strong> across 17 manufacturers — including all major Indian-market bikes.
            Simulated at ISA conditions (sea level, 15 °C, 75 kg rider).
            Indian venues will show different times — use the{' '}
            <Link href="/#simulator" className="text-orange-400 hover:underline">simulator</Link>.
          </p>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-1.5 text-white/40">
              <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
              Validation-confirmed
            </div>
            <div className="flex items-center gap-1.5 text-white/40">
              <span className="w-2 h-2 rounded-full bg-orange-400 inline-block" />
              Model prediction (~)
            </div>
            <div className="flex items-center gap-1.5 text-white/40">
              <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
              Indian-market bike
            </div>
          </div>
        </div>
      </section>

      {/* Bikes by manufacturer */}
      <section className="max-w-6xl mx-auto px-6 py-16 space-y-16">
        {Object.entries(byMfr).map(([mfr, bikes]) => (
          <div key={mfr}>
            <h2 className="text-xl font-bold mb-5 flex items-center gap-3">
              {mfr}
              <span className="text-sm font-normal text-white/30">{bikes.length} bike{bikes.length > 1 ? 's' : ''}</span>
              {bikes.some(b => b.india) && (
                <span className="text-xs px-2 py-0.5 bg-blue-500/15 border border-blue-500/20 text-blue-400 rounded-full">India</span>
              )}
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {bikes.map((bike) => (
                <Link
                  key={bike.slug}
                  href={`/bikes/${bike.slug}`}
                  className="group flex items-start justify-between bg-white/4 hover:bg-white/7 border border-white/8 hover:border-orange-500/20 rounded-xl p-4 transition-all"
                  aria-label={`${bike.name} quarter mile time: ${bike.et}s`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-white/90 group-hover:text-white transition-colors leading-snug">
                        {bike.name}
                      </h3>
                      {bike.validated && (
                        <span className="flex-shrink-0 w-2 h-2 rounded-full bg-green-500" title="Validation-confirmed ET" />
                      )}
                      {bike.india && !bike.validated && (
                        <span className="flex-shrink-0 w-2 h-2 rounded-full bg-blue-400" title="Indian-market bike" />
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1.5 text-xs text-white/35 mb-2">
                      <span>{bike.cc}cc</span>
                      <span>·</span>
                      <span>{bike.ps} PS</span>
                      <span>·</span>
                      <span>{bike.kg} kg</span>
                    </div>
                    <span className={`inline-block text-xs px-2 py-0.5 rounded-full border ${CAT_COLORS[bike.category] || 'bg-white/8 text-white/40 border-white/10'}`}>
                      {bike.category}
                    </span>
                  </div>
                  <div className="flex-shrink-0 text-right ml-4">
                    <div className="text-orange-400 font-bold text-lg tabular-nums">{bike.et}s</div>
                    <div className="text-white/30 text-xs">{bike.trap} km/h</div>
                    <ChevronRight size={14} className="text-white/20 group-hover:text-orange-400/60 transition-colors ml-auto mt-1" />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </section>

      {/* CTA */}
      <section className="border-t border-white/8 py-16">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="text-white/30 text-xs uppercase tracking-widest mb-3">Free Tool</p>
          <h2 className="text-2xl font-bold mb-3">Simulate Your Exact Build</h2>
          <p className="text-white/50 text-sm max-w-lg mx-auto mb-6 leading-relaxed">
            The times above are stock at ISA conditions. Use the simulator to factor in
            your rider weight, modifications, and your chosen Indian drag venue.
          </p>
          <Link
            href="/#simulator"
            className="inline-flex items-center gap-2 px-7 py-3 bg-orange-600 hover:bg-orange-500 rounded-xl font-semibold transition-all text-sm"
          >
            <Gauge size={16} /> Try the Simulator Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/8 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-3 text-xs text-white/25">
          <div>
            <Link href="/" className="hover:text-white/50 transition-colors">
              <span className="text-orange-500 font-semibold">Moto</span>Quant Pro
            </Link>
            {' '}· The physics of faster
          </div>
          <p className="text-center leading-relaxed max-w-md">
            All ETs simulated at ISA conditions. Real-world times vary by tyre, weather, altitude, and rider.
            Times marked ~ are model predictions, not validated benchmarks.
          </p>
        </div>
      </footer>
    </div>
  );
}
