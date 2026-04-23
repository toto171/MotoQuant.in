// INTENTIONALLY EMPTY (module export default required by App Router if the
// file exists at all). The real robots policy lives in /public/robots.txt
// which Next.js serves at the same URL and which takes precedence over any
// app/robots.{js,ts} route. The static file was preferred because we can't
// delete files in the Cowork sandbox.
//
// If you ever move robots policy to be dynamic, delete /public/robots.txt
// first, then export a default function from this file returning a
// MetadataRoute.Robots object.

export const dynamic = 'force-static';

// Next.js App Router requires `default export` for convention files. Return
// a minimal policy that matches /public/robots.txt so there's no divergence
// if the static file is ever removed.
export default function robots() {
  return {
    rules: [{ userAgent: '*', allow: '/', disallow: ['/_next/', '/api/'] }],
    sitemap: 'https://motoquant.in/sitemap.xml',
    host: 'https://motoquant.in',
  };
}
