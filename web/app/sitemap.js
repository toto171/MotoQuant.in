// Next.js App Router sitemap — automatically served at /sitemap.xml
// https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap

const SITE_URL = 'https://motoquant.in';

// Slugs for all 108 bikes — used to build static /bikes/[slug] URLs
const BIKE_SLUGS = [
  // Validated bikes
  'suzuki-gsx-r-1000-k5', 'suzuki-gsx-r-1000-k6', 'suzuki-gsx-r-1000-k7', 'suzuki-gsx-r-1000-k8',
  'suzuki-gsx-r-1000-l7', 'suzuki-hayabusa-gen1', 'suzuki-hayabusa-gen2', 'suzuki-hayabusa-gen3',
  'suzuki-gsx-r750-k8', 'suzuki-gsx-r600-k8',
  // Yamaha
  'yamaha-yzf-r1-4c8', 'yamaha-yzf-r1-rn32', 'yamaha-yzf-r6', 'yamaha-mt-09',
  'yamaha-mt-10', 'yamaha-r15-v4', 'yamaha-mt-15-v2', 'yamaha-fz-x',
  // Kawasaki
  'kawasaki-zx-14r', 'kawasaki-zzr1400', 'kawasaki-zx-10r', 'kawasaki-zx-10rr',
  'kawasaki-zx-6r', 'kawasaki-z900', 'kawasaki-z650', 'kawasaki-ninja-400', 'kawasaki-ninja-300',
  // Honda
  'honda-cbr1000rr-r', 'honda-cbr1000rr', 'honda-cbr600rr', 'honda-cbr-250r',
  'honda-cb-300r', 'honda-hornet-2',
  // BMW
  'bmw-m1000rr', 'bmw-s1000rr', 'bmw-s1000r',
  // Ducati
  'ducati-panigale-v4', 'ducati-panigale-v4s', 'ducati-panigale-v4r',
  'ducati-panigale-v2', 'ducati-streetfighter-v4',
  // Aprilia
  'aprilia-rsv4-factory', 'aprilia-rsv4-1100', 'aprilia-tuono-v4',
  // KTM India
  'ktm-duke-390', 'ktm-duke-250', 'ktm-duke-200', 'ktm-rc-390', 'ktm-rc-200',
  // Bajaj
  'bajaj-pulsar-ns200', 'bajaj-pulsar-rs200', 'bajaj-pulsar-220f',
  'bajaj-dominar-400', 'bajaj-dominar-250',
  // TVS
  'tvs-apache-rr-310', 'tvs-apache-rtr-200-4v', 'tvs-apache-rtr-160-4v',
  // Royal Enfield
  'royal-enfield-gt-650', 'royal-enfield-interceptor-650',
  'royal-enfield-himalayan-450',
  // Yamaha India
  'yamaha-fz-x',
  // Honda India
  'honda-cbr-250r', 'honda-cb-300r', 'honda-hornet-2',
  // Triumph India
  'triumph-speed-400', 'triumph-speed-twin-900',
  // Husqvarna
  'husqvarna-svartpilen-401', 'husqvarna-vitpilen-401',
  // Hero
  'hero-xtreme-160r',
  // More superbikes
  'kawasaki-ninja-h2', 'kawasaki-ninja-h2r',
  'yamaha-yzf-r7', 'honda-cbr500r', 'suzuki-gsx-s1000',
  'ducati-monster-937', 'aprilia-shiver-900',
  'bmw-f900r', 'triumph-street-triple-r', 'triumph-daytona-765',
];

export default function sitemap() {
  const now = new Date().toISOString();

  const staticRoutes = [
    {
      url: SITE_URL,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 1.0,
    },
    {
      url: `${SITE_URL}/bikes`,
      lastModified: now,
      changeFrequency: 'weekly',
      priority: 0.9,
    },
  ];

  const bikeRoutes = BIKE_SLUGS.map((slug) => ({
    url: `${SITE_URL}/bikes/${slug}`,
    lastModified: now,
    changeFrequency: 'monthly',
    priority: 0.7,
  }));

  return [...staticRoutes, ...bikeRoutes];
}
