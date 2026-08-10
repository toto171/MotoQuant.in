// Owns the breadcrumb structured data for /contact. The page is a server
// component and exports its own `metadata`; this layout adds the JSON-LD
// trail so the contact surface is discoverable the same way /terms is.

import StructuredData, { SITE_URL } from '../StructuredData';

function breadcrumbs() {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Contact', item: `${SITE_URL}/contact` },
    ],
  };
}

export default function ContactLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
