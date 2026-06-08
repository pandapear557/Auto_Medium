# CLAUDE.md

Guidance for AI assistants (and humans) working in this repository.

## What this project is

**Auto_Medium** is a blog-collection automation pipeline built around the
**Medium Daily Digest** newsletter. Given the plain-text body of a digest email,
it extracts each linked article, reconstructs the canonical article URL,
crawls the page, and returns the title + body text as JSON — optionally saving
each result into a **Notion database** (`notion_DB.txt` holds the target DB URL).

The architecture follows a **local-test → AWS-deploy** strategy: the crawling
core lives in the reusable `auto_medium/` package, and two thin entry points
share it — `run_local.py` for local runs and `lambda_function.py` for AWS
Lambda (`lambda_handler`, results shaped as `{ "statusCode", "headers", "body" }`).

> Comments and docstrings are in Korean. The original exploratory code lives in
> `test/` (notebook + early `.py` drafts) and is kept only as reference — the
> `auto_medium/` package is the canonical, working implementation.

## Communication language

- **Reply to the user in Korean (한국어).** The maintainer prefers Korean for
  all chat responses, explanations, and summaries.
- Internal reasoning may be in English, but every user-facing message —
  including status updates, error explanations, and questions — must be written
  in Korean.
- Code, identifiers, and commit messages stay in English; only the conversational
  response language is Korean. Existing in-code comments remain Korean as before.

## Repository layout

```
.
├── auto_medium/            # Canonical reusable package (shared by both entry points)
│   ├── __init__.py
│   ├── utils.py            # url_tuples, convert_text, make_url, merge_json
│   ├── crawler.py          # MailCrawler: fetch + parse (logging, timeout, fallback)
│   ├── notion_store.py     # NotionStore: save results to a Notion DB
│   └── pipeline.py         # run(): mail → crawl → (optional) Notion. Shared core.
├── run_local.py            # Local entry point — reads mail.json, prints JSON
├── lambda_function.py      # AWS Lambda entry point — lambda_handler(event, context)
├── requirements.txt        # beautifulsoup4, notion-client
├── .env.example            # NOTION_TOKEN / NOTION_DB_ID / property-name overrides
├── .gitignore              # .env, mail.txt, __pycache__, venvs
├── mail.json               # Sample input ({ "text", "index" })
├── notion_DB.txt           # Target Notion database URL (personal)
├── README.md               # One-line project description (Korean)
└── test/                   # Reference-only scratch area (NOT a test suite)
    ├── parser.ipynb        # Original dev notebook — working end-to-end exploration
    ├── mail_crawler.py     # Early draft crawler
    ├── utils.py            # Early draft utils
    └── paragraph.json      # Sample crawled output
```

`test/` is **not** a unit-test suite — it holds the original exploration the
package was derived from. Don't import from it; treat the notebook as historical
reference for the crawling algorithm.

## How the pipeline works

`pipeline.run(mail_text, index=None, save_to_notion=False)` is the single shared
entry point. Both `run_local.py` and `lambda_function.py` call it.

1. **Input** — the body text of a Medium Daily Digest email (see `mail.json`,
   key `"text"`). An optional `"index"` selects a single article; omit it to
   crawl all.
2. **Parse to tuples** (`Utils.url_tuples`) — regex
   `(.*)\((https?://[^\s)]+)\)\n\n(.*)` splits each entry into
   `(author_name, base_url, article_title)`.
3. **Reconstruct the article URL** (`Utils.make_url(author, base_url, title)`) —
   digest links point at a `?source=...reader-...` redirect, not the real
   article. `make_url` slugifies the title via `convert_text` (lowercase,
   spaces→`-`, strip non-alphanumeric) and splices in the article hash pulled
   from the `.reader-<x>-<hash>----` token in the query string to build the
   canonical `medium.com/<pub>/<slug>-<hash>` URL.
4. **Filter noise** — entries whose author is in `EXCEPT_LIST` (`·Member`,
   `Edit who you follow`, `Control your recommendations`, `·Terms of service`)
   are Medium nav/footer links and are skipped.
5. **Crawl** (`MailCrawler`) — `urllib.request` with browser-like headers and a
   timeout, parsed by **BeautifulSoup** (`html.parser`). Title =
   `soup.select_one("h1")`; body = joined `.pw-post-body-paragraph` text, with a
   fallback to the `<article>` element when that selector is empty.
6. **Output / store** — returns a list of `{ url, title, text }`. When
   `save_to_notion=True`, `NotionStore.save_many` creates one Notion page per
   result.

## Running locally

```bash
pip install -r requirements.txt          # beautifulsoup4, notion-client

python run_local.py                       # crawl mail.json, print JSON to stdout
SAVE_TO_NOTION=1 python run_local.py      # also write results to Notion
```

`run_local.py` reads `mail.json` (`text` + optional `index`). Python 3.11+.

For Notion saving, copy `.env.example` → `.env` and fill in `NOTION_TOKEN` and
`NOTION_DB_ID` (and `NOTION_TITLE_PROP` / `NOTION_URL_PROP` if your DB's column
names differ from `Name` / `URL`). The integration must be shared with the DB
in Notion. `run_local.py` reads these from the environment; load `.env` via your
shell or `python-dotenv` as preferred.

## Deploying to AWS Lambda

- Handler: `lambda_function.lambda_handler`.
- Package `auto_medium/` + `lambda_function.py` + dependencies (a layer or a zip
  with `beautifulsoup4` and, if Notion saving is used, `notion-client`).
- Event: `{ "text": "<mail body>", "index": <optional int>, "save_to_notion": <optional bool> }`.
  When invoked behind API Gateway, the handler also accepts the body as a JSON
  string in `event["body"]`.
- Set `NOTION_*` as Lambda environment variables when `save_to_notion` is used.

## Conventions

- **Comments and docstrings are in Korean.** Match the surrounding language when
  editing existing code.
- **Shared core, thin entry points:** put logic in `auto_medium/`; keep
  `run_local.py` / `lambda_function.py` as thin wrappers over `pipeline.run`.
- **Lambda shape:** `lambda_handler(event, context)` returns
  `{ "statusCode", "headers", "body" }` with `body` a JSON string
  (`ensure_ascii=False` to preserve non-ASCII titles).
- **Secrets via environment only** — never hardcode Notion tokens; read from
  `os.environ`. `notion-client` is imported lazily so local crawl-only runs
  don't require it installed.
- Crawl extraction depends on Medium's `.pw-post-body-paragraph` class and the
  `h1` title (with an `<article>` fallback) — brittle against Medium markup
  changes; verify selectors if extraction returns "No Paragraph Found".

## Known limitations

- **Medium anti-bot (HTTP 403):** Medium frequently blocks server-side requests.
  Crawling works from some networks and 403s from others (e.g. cloud/CI IPs).
  The crawler logs the 403 and skips the article rather than crashing. If you
  hit consistent 403s, the fix is at the fetch layer (session cookies, a
  different network, or a rendering/reader approach) — not the parsing logic,
  which is verified correct.
- **Notion DB schema:** `NotionStore` assumes a title property (default `Name`)
  and an optional URL property (default `URL`). Override via `NOTION_TITLE_PROP`
  / `NOTION_URL_PROP` to match the actual database, or the page create will fail.

## Git workflow

- Active development branch for this work: `claude/claude-md-docs-jf33se`.
- Default branch: `main`.
- Push with `git push -u origin <branch>`; do not push to `main` without
  explicit permission, and do not open a PR unless asked.

## Secrets / privacy

`notion_DB.txt` and the sample digest in `mail.json` contain a personal Notion
workspace URL and personal Medium account references. Avoid leaking these into
logs or external services. `.env`, `mail.txt`, and real email dumps are
gitignored — keep real credentials and inboxes out of commits.
