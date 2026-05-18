// Layout for /blog/how-to-tune-for-mmrt-chennai — owns the breadcrumb
// structured-data block. Article-level structured data (articleSchema JSON-LD)
// is injected from page.js where the title/description live alongside the
// post content.

import StructuredData, { SITE_URL } from '../../StructuredData';

const SLUG = 'how-to-tune-for-mmrt-chennai';
const TITLE = 'How to Tune for MMRT Chennai: Sea-Level, Humid, Hot Track';

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
