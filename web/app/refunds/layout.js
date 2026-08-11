// Owns the breadcrumb structured data for /refunds. The page is a server
// component and exports its own `metadata`; this layout adds the JSON-LD
// trail so the policy is discoverable the same way /terms and /privacy are.

import StructuredData, { SITE_URL } from '../StructuredData';

function breadcrumbs() {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Refunds', item: `${SITE_URL}/refunds` },
    ],
  };
}

export default function RefundsLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
