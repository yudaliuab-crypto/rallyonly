# RallyOnly SEO/GEO audit — before changes

Audit date: 2026-11-15 (Europe/Madrid). Baseline commit: `87261835f91882e8aea27f5ef0bba5e1f67fdfe7`.

This record was written before changing public website files. Scope: the existing public website only; no iOS application code, DNS or account settings.

## Direct observations

GET requests with TLS verification enabled, following redirects:

| URL | Observed response |
| --- | --- |
| `https://rallyonly.app/` | 200, HTML |
| `https://yudaliuab-crypto.github.io/rallyonly/` | 301 to `https://rallyonly.app/`, then 200 |
| `https://rallyonly.app/robots.txt` | 200, `User-agent: *`, `Allow: /`, canonical sitemap |
| `https://yudaliuab-crypto.github.io/rallyonly/robots.txt` | 301 to custom-domain `/robots.txt`, then 200 |
| `https://yudaliuab-crypto.github.io/robots.txt` | 404 |
| `https://rallyonly.app/sitemap.xml` | 200, XML, five URLs |
| `https://rallyonly.app/es/` | 200, Spanish server-rendered HTML |
| `https://rallyonly.app/zh/` | 404 |

Raw public HTTP headers/bodies were retained outside this repository in the task's `work/rallyonly-seo-audit-2026-11-15/baseline/` directory. No signed-in browser was used.

## Findings and intended repairs

| ID | Finding before changes | Action |
| --- | --- | --- |
| F01 | Canonical custom domain, English/Spanish alternate links, sitemap and allow-all robots already exist. | Preserve these; do not invent a crawl block. |
| F02 | A project-path `robots.txt` does not govern its parent GitHub host. The effective custom-domain root file works; legacy host root is 404. | Document scheme/host/port scope and the observed redirect. Do not change another repository or claim a 404 is a disallow. |
| F03 | Chinese homepage is missing. Only English and Spanish homepage alternates are declared. | Add an original Chinese translation with reciprocal `en`, `es`, `zh-Hans`, `x-default`, self-canonical and visible language links. |
| F04 | Homepages already contain SoftwareApplication, but lack explicit iPhone-only device scope and a qualified free-tier offer. | Use the supported MobileApplication subtype, stable app identity and truthful free-tier offer. Never invent ratings/reviews. |
| F05 | Home FAQ markup has a comparison question not rendered as a matching FAQ; Android headings also differ. | Generate FAQ markup from the visible FAQ questions/answers. |
| F06 | US and Spanish comparison snippets mix dated store offers without direct source links; US yearly SwingVision quote is $95.99. | Replace unsupported current-plan claims with dated, sourced public descriptions. Distinguish annual equivalent from monthly billing and disclose checkout uncertainty. |
| F07 | No independent comparison or automatic-trimming tutorial exists. | Add two distinct English articles with actual existing workflows, limitations, sources and navigation. |
| F08 | Numeric processing-speed claims are not supported by a retained device/version/codec benchmark in this website. | Replace the unconditional timing estimate with device/recording-dependent wording. Retain real demo content without claiming exhaustive detection recall. |
| F09 | Text is server-rendered; images have alt text. Navigation lacks a skip link and tables lack captions/scope. | Add keyboard skip links, semantic table headers, accessible video text and narrowly scoped CSS fixes. Measure contrast before changing a color. |
| F10 | `llms.txt`, Google verification file, Bing meta and IndexNow key file already exist. | Keep useful existing files; do not claim verification, submission, indexing or AI ranking from their presence. |
| F11 | No reproducible AI mention/citation measurement workflow exists. | Add 10 fixed questions, local capture/export, evidence fields and a denominator-aware summarizer; do not fabricate live AI results. |

## Outside direct verification

Search Console/Bing ownership, submitted sitemap status, Google-selected canonical, actual indexing, crawl requests from verified crawler IPs, AI citation history, campaign download counts and live Google Rich Results Test output are not established by repository files or public curl requests. These must remain explicitly unverified.

## Source checks

- [OpenAI crawler controls](https://developers.openai.com/api/docs/bots): OAI-SearchBot search discovery is separate from GPTBot training.
- [Google AI features](https://developers.google.com/search/docs/appearance/ai-features): ordinary indexing and snippet eligibility; no special AI markup requirement.
- [Google software app structured data](https://developers.google.com/search/docs/appearance/structured-data/software-app): MobileApplication is supported. Software-app rich results additionally require a real rating or review; none will be fabricated.
- [Google robots specification](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec): root URL and host scope; 404 is not a disallow.
- [Google localized pages](https://developers.google.com/search/docs/specialty/international/localized-versions): reciprocal alternates and separate URLs.
- [SwingVision US App Store](https://apps.apple.com/us/app/swingvision-tennis-pickleball/id989461317): public description states US$179.99/year and US$14.99/month wording; the latter is approximately the annual equivalent and is not independently confirmed as a monthly-billed checkout plan.
- [RallyOnly US App Store](https://apps.apple.com/us/app/rallyonly-tennis-highlights/id6813940884): fetched public listing confirms Monthly US$4.99 and Yearly US$34.99.

No promise of indexing, citations, ranking or traffic is made.
