# RallyOnly website

Public static website for RallyOnly, an iPhone tennis-video editing app. The iOS app is maintained in a separate private repository.

- [English homepage](https://rallyonly.app/), [Español](https://rallyonly.app/es/), [中文](https://rallyonly.app/zh/)
- [RallyOnly vs SwingVision](https://rallyonly.app/rallyonly-vs-swingvision.html)
- [Automatic trimming tutorial](https://rallyonly.app/how-to-automatically-trim-tennis-match-videos.html)
- [Filming guide](https://rallyonly.app/how-to-film-tennis-match-iphone.html)
- [Privacy policy](https://rallyonly.app/privacy.html) and [support](https://rallyonly.app/support.html)

Article URLs above become available after this branch is deployed. The comparison and trimming tutorial are English articles; they are not represented as Spanish/Chinese translations. App languages and website languages are different scopes.

## Preview and checks

Python 3 standard library; no package install or build step:

```sh
python3 -m http.server 8765 --bind 127.0.0.1
python3 tools/validate_site.py
python3 -m unittest discover -s tests -v
git diff --check
```

Open `http://127.0.0.1:8765/`. The static checker covers canonical URLs, homepage language reciprocity, local links/assets for both domain root and project-prefix layouts, sitemap membership, robots rules, truthful app-schema invariants and basic accessibility. It does not establish indexing, real bot access or Google rich-result eligibility.

## Hosting and crawler scope

`CNAME` selects `rallyonly.app`. Canonicals and the sitemap use that domain; legacy project URLs redirect there. Effective robots rules are at `https://rallyonly.app/robots.txt`. A file at `github.io/rallyonly/robots.txt` does not control `github.io/`; robots scope is the scheme, host and port, with the file at that origin's root. The existing allow-all rules permit OAI-SearchBot, Googlebot and Bingbot and are preserved.

## SEO audit and AI visibility observations

- [Before-change audit](docs/seo-audit-before-2026-11-15.md)
- [Final audit and manual follow-ups](docs/seo-audit-2026-11-15.md)
- [Validation summary](docs/seo-validation-2026-11-15.json)
- [AI observation protocol and metrics](tools/ai-search/README.md)

Open `/tools/ai-search/` on the local server to copy the fixed questions, record actual answers and export JSONL. This tool has `noindex,follow` and is excluded from the public sitemap. It calls no AI service. Browser records remain on the same origin/profile; exporting is required for backup. If the browser blocks clipboard access, select/copy the visible questions or use `prompts.json`. Keep real answers, screenshots and traffic exports in the ignored `tools/ai-search/private/` directory, never in this public repository. No analytics collection is installed by this change.

The 2026-11-15 US prices are dated observations, not permanent offers. Recheck primary listings and purchase terms before changing comparison copy. Never invent ratings or reviews to satisfy a rich-results validator.

Contact: rallyonly.feedback@gmail.com
