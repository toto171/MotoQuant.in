# Writing for MotoQuant

Most readers are riders and tuners in India, many reading in a second
language, so every word on the site and in the docs should be plain and
specific. These rules apply to anything a visitor or contributor reads:
page text, labels, error messages, blog posts, README and docs.
`tests/test_site_copy_style.py` enforces the first two rules for the site.

## Rules

1. No em dashes. Use a comma, a colon, brackets or a new sentence.
2. The product is MotoQuant. Never "MotoQuant Pro".
3. Lead with the point. The first sentence says the result, the time, or
   what the reader can do.
4. Give the number and its unit: "13.30 s", "162 km/h", "₹4,800",
   "679 m". Write the figure as it appears in the source; never round a
   benchmark or a simulated time differently from the data.
5. Never state a fact the data does not support. A simulated time says it is
   simulated; a published time names its source.
6. Short common words: "use", "about", "help", "start". Avoid hype
   ("game-changing", "seamless", "cutting-edge", "unlock") and filler ("it's
   worth noting", "in this article", "let's dive in").
7. Sentence case for headings and buttons: "Find the best parts", not "Find
   The Best Parts".
8. Keep labels short. A button or menu item names the action in two or
   three words.
9. Do not end a section by summarising it or telling the reader what it
   means. Stop when the point is made.
10. Prefer British spelling (tyre, colour, optimise), which Indian readers
    expect. Older pages still mix in US spelling; fix it when you edit them.
11. No emoji and no exclamation marks.

## Before you open a pull request

- Read your text aloud once. If a sentence needs a breath in the middle,
  split it.
- Run `python -m pytest tests/test_site_copy_style.py -q` if you changed site
  text.
- Numbers on the accuracy pages and in the README are checked by
  `make audit`; run it if you touched them.
