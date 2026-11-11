// lib/blogDates.js feeds the sitemap's lastModified for blog posts. It is a
// copy of the dates each post declares in its Article JSON-LD, so check the
// copy against the source and check that every post is in the sitemap.
// Run (from web/): node --test scripts/*.test.mjs

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';

const APP = new URL('../app/', import.meta.url);
const blogDir = new URL('blog/', APP);

const src = readFileSync(new URL('../lib/blogDates.js', import.meta.url), 'utf8');
const { BLOG_DATES } = await import('data:text/javascript;base64,' + Buffer.from(src).toString('base64'));

const posts = readdirSync(blogDir, { withFileTypes: true })
  .filter((d) => d.isDirectory() && existsSync(new URL(`${d.name}/page.js`, blogDir)))
  .map((d) => d.name)
  .sort();

test('every blog post has dates, and only real posts do', () => {
  assert.deepEqual(Object.keys(BLOG_DATES).sort(), posts);
});

test('the dates match the Article JSON-LD in each post', () => {
  for (const slug of posts) {
    const page = readFileSync(new URL(`${slug}/page.js`, blogDir), 'utf8');
    const call = page.slice(page.indexOf('articleSchema({'));
    assert.ok(page.includes('articleSchema({'), `${slug}: no Article JSON-LD`);
    const pub = call.match(/datePublished: ['"](\d{4}-\d{2}-\d{2})['"]/);
    const mod = call.slice(0, call.indexOf('})')).match(/dateModified: ['"](\d{4}-\d{2}-\d{2})['"]/);
    assert.equal(pub?.[1], BLOG_DATES[slug].published, `${slug}: datePublished`);
    assert.equal(mod?.[1], BLOG_DATES[slug].modified, `${slug}: dateModified`);
  }
});

test('a post that says it was updated declares dateModified', () => {
  for (const slug of posts) {
    const page = readFileSync(new URL(`${slug}/page.js`, blogDir), 'utf8');
    if (page.includes('Updated 10 November 2026')) {
      assert.equal(BLOG_DATES[slug].modified, '2026-11-10', slug);
    }
  }
});

test('every blog post is in the sitemap', () => {
  const sitemap = readFileSync(new URL('sitemap.js', APP), 'utf8');
  for (const slug of posts) {
    assert.ok(sitemap.includes(`/blog/${slug}\``), `${slug} missing from sitemap.js`);
  }
});
