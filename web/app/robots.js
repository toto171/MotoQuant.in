/**
 * MotoQuant Pro — robots.txt route
 * =================================
 * Generates /robots.txt via Next.js metadata convention. Returned as a
 * MetadataRoute.Robots object.
 */

export const dynamic = 'force-static';

// Next.js App Router requires `default export` for convention files. Return
// a minimal policy that matches /public/robots.txt so there's no divergence
// if the static file is ever removed.
export default function robots() {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        // Block private user pages and server internals.
        // /api/ excluded so bots don't hammer the backend.
        disallow: ['/account', '/login', '/signup', '/api/'],
      },
    ],
    // Apex domain — every canonical URL + SITE_URL on the site uses the apex
    // (https://motoquant.in); the old www values here were the odd ones out.
    sitemap: 'https://motoquant.in/sitemap.xml',
    host: 'https://motoquant.in',
  };
}
