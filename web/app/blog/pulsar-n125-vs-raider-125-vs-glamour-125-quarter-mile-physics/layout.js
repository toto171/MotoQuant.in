// Layout for /blog/pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics
// — owns the breadcrumb structured-data block. Article-level structured data
// (the articleSchema JSON-LD) is injected from page.js where the title and
// description live alongside the post content.

import StructuredData, { SITE_URL } from "../../StructuredData";

const SLUG = "pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics";
const TITLE =
  "Pulsar N125 vs Raider 125 vs Glamour 125: 125cc Drag";

function breadcrumbs() {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE_URL },
      { "@type": "ListItem", position: 2, name: "Blog", item: `${SITE_URL}/blog` },
      { "@type": "ListItem", position: 3, name: TITLE, item: `${SITE_URL}/blog/${SLUG}` },
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
