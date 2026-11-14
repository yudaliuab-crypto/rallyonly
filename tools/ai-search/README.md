# AI search observations

This is a manual evidence-capture workflow, not a ranking simulator or an automated model-calling service. It sends no prompts, installs no app analytics, and creates no fabricated observations. Real answers, screenshots and exports belong in the git-ignored `private/` folder, not a public commit.

## Fixed protocol

1. Serve the repository locally: `python3 -m http.server 8765`. Open `http://localhost:8765/tools/ai-search/`.
2. Use the exact question in a fresh conversation with no RallyOnly background. Disable memory/personalization where possible. Record `unknown` if that cannot be confirmed; the strict headline sample excludes it. Do not follow a brand-specific chat with a test question.
3. Test ChatGPT Search, Google AI Mode, Google AI Overviews and Bing Copilot separately. Perplexity is an optional additional engine. For Google Overviews, record `no_ai_answer` if the overview does not trigger; a normal search result is not an AI answer. Confirm the search mode was active rather than guessing from the product name.
4. Keep country/region, interface language, displayed model/version and settings consistent. Use the same `round_id` for a weekly round, and trials 1–3 in separate conversations for each question. Keep the 10 questions fixed for comparisons. Q01–Q06 are supplied by the user; Q07–Q10 are **proposed completions**, because the original final four were not supplied.
5. Paste the actual answer body. Save a screenshot, export or share link as evidence and enter its path/URL. Do not invent the model name when it is not displayed: write `not shown`.
6. Review the sources panel and open each cited URL. A brand mention, an unclicked suggested link, and a verified source citation are different. Tick `citations reviewed` only after checking the source list (including an empty one). URLs entered in the capture form count as verified only if the verification checkbox is checked.
7. Check statements against current product facts: iPhone only; iOS 17+; local rally detection, downtime trimming and highlights; 4 new matches/month free; watermarked free exports; Pro optional. Prices depend on store/date/offer. Offline analysis does not imply that iCloud downloads, purchases or sharing work without a network. Record inaccurate claims and the comparison source/date. Price truth must be refreshed, not frozen at today's value.
8. Export JSONL. The form keeps entries in this browser's local storage; it does not upload them. Preserve your export before clearing the browser or changing devices. Back up evidence separately. Never submit review content to crawlers as a ranking instruction.

## Calculate

```sh
python3 tools/ai-search/summarize.py tools/ai-search/private/observations.jsonl \
  --traffic tools/ai-search/private/referrals.csv \
  --out tools/ai-search/private/weekly-summary.json
```

- **Mention rate:** eligible generated answers naming RallyOnly / eligible generated answers. Eligible means a fresh conversation, personalization off, search confirmed on. No-AI-answer, blocked and unknown-settings cases are separately counted, not silently turned into negative mentions.
- **Citation rate:** citation-reviewed eligible answers containing at least one opened/verified official website or exact RallyOnly App Store URL / citation-reviewed eligible answers. Both the custom domain and legacy project path are recognized. Third-party citations may be retained in the evidence but do not count as official citations. Unreviewed source lists do not enter the denominator.
- **Correctness:** reviewed, correct brand-mentioned answers / reviewed brand-mentioned answers. Unreviewed claims remain unknown. This is a human check of stated facts, not a model-generated quality score.
- Conditions are grouped separately. Duplicate round/engine/model/region/language/personalization/question/trial records are rejected. Rates without a denominator are `null`, not 0. Small samples and repeated-answer variability must accompany any interpretation; no significance or stable rank is asserted.

## Referral and download evidence

Copy `referrals.csv.example` to `private/referrals.csv`. Leave unknown cells blank. Supply the source report or export in `evidence` and a specific `attribution_level`, such as `identified_referral`, `page_campaign_only`, or `unattributed`.

ChatGPT referral URLs can include `utm_source=chatgpt.com`; preserve observable UTM/referrer information when available. That covers only identifiable visits, not all AI exposure. An existing website campaign or a page-specific App Store campaign does **not** prove the visit came from AI. The new `web_compare`, `web_trim_guide` and `web_zh` campaigns identify landing pages, not AI engines. Source-specific downloads require actual campaign/report evidence; otherwise leave downloads unknown. Do not sum overlapping exports or infer person-level journeys from aggregate daily counts.

No real AI answer collection, Search Console/Bing login, referral analytics setup or App Store download export has been performed by creating this tool. Bing's [AI Performance](https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/) covers supported Microsoft/partner surfaces; it is not all-platform share of voice. See also [OpenAI's publisher FAQ](https://help.openai.com/en/articles/12627856-publishers-and-developers-faq).
