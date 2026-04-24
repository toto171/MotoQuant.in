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
    sitemap: 'https://www.motoquant.in/sitemap.xml',
    host: 'https://www.motoquant.in',
  };
}
