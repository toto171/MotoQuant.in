// Layout for /blog/cfmoto-800nk-quarter-mile-physics — owns the breadcrumb
// structured-data block. Article-level structured data (the articleSchema
// JSON-LD) is injected from page.js where the title/description live alongside
// the post content.

import StructuredData, { SITE_URL } from '../../StructuredData';

const SLUG = 'cfmoto-800nk-quarter-mile-physics';
const TITLE = 'CFMoto 800NK Quarter-Mile Physics: A KTM 790 Duke in Disguise';

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
