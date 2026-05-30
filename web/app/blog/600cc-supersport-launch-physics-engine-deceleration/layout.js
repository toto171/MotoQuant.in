// Layout for /blog/600cc-supersport-launch-physics-engine-deceleration — owns
// the breadcrumb structured-data block. Article-level structured data (the
// articleSchema JSON-LD) is injected from page.js where the title/description
// live alongside the post content.

import StructuredData, { SITE_URL } from "../../StructuredData";

const SLUG = "600cc-supersport-launch-physics-engine-deceleration";
const TITLE = "Why 600cc Supersports Were Running 200ms Slow in Our Sim";

function breadcrumbs() {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: SITE_URL },
      {
        "@type": "ListItem",
        position: 2,
        name: "Blog",
        item: `${SITE_URL}/blog`,
      },
      {
        "@type": "ListItem",
        position: 3,
        name: TITLE,
        item: `${SITE_URL}/blog/${SLUG}`,
      },
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
