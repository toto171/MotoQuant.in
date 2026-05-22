// Layout for /blog/ktm-890-duke-r-quarter-mile-india — owns the breadcrumb
// structured-data block. Article-level structured data (the articleSchema
// JSON-LD) is injected from page.js where the title/description live alongside
// the post content.

import StructuredData, { SITE_URL } from '../../StructuredData';

const SLUG = 'ktm-890-duke-r-quarter-mile-india';
const TITLE = 'KTM 890 Duke R Quarter-Mile in India: 11.07s on the Grey Market';

function breadcrumbs() {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Blog', item: `${SITE_URL}/blog` },
      { '@type': 'ListItem', position: 3, name: TITLE, item: `${SITE_URL}/blog/${SLUG}` },
    ],
  };
}

export default function PostLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
