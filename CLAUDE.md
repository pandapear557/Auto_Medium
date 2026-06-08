# CLAUDE.md

Guidance for AI assistants (and humans) working in this repository.

## What this project is

**Auto_Medium** is a blog-collection automation pipeline built around the
**Medium Daily Digest** newsletter. Given the plain-text body of a digest email,
it extracts each linked article, reconstructs the canonical article URL,
crawls the page, and returns the title + body text as JSON. The intent is to
feed that content into a downstream store — a Notion database
(`notion_DB.txt` holds the target Notion DB URL).

The code targets **AWS Lambda** (handlers named `lambda_handler`, results
shaped as `{ "statusCode": ..., "body": ... }`).

> The repository is small, early-stage, and primarily in Korean comments.
> It is a work-in-progress refactor of exploratory notebook code into Lambda
> functions, so the modules are not yet fully consistent (see
> **Known inconsistencies** below). Treat the notebook logic as the
> ground-truth reference for the crawling algorithm.

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
├── README.md                    # One-line project description (Korean)
├── mail_crawler_single_ins.py   # Root Lambda handler (single-article variant)
├── util.py                      # Root Utils helper (convert_text, make_url)
├── mail.json                    # Sample Lambda input event ({ "text", "index" })
├── notion_DB.txt                # Target Notion database URL
└── test/                        # Exploratory / fuller reference implementations
    ├── parser.ipynb             # Dev notebook — working end-to-end exploration
    ├── mail_crawler.py          # Fuller crawler: batch + single-instance methods
    ├── utils.py                 # Fuller Utils: url_tuples, convert_text, make_url, merge_json
    └── paragraph.json           # Sample crawled output
```

`test/` is **not** a unit-test suite — it is a scratch/dev area holding the more
complete implementations and the notebook the `.py` modules were derived from.

## How the pipeline works

1. **Input** — the body text of a Medium Daily Digest email (see `mail.json`,
   key `"text"`). Lambda events also carry an `"index"` selecting one article.
2. **Parse to tuples** (`Utils.url_tuples`, in `test/utils.py`) — regex
   `(.*)\((https?://[^\s)]+)\)\n\n(.*)` splits each entry into
   `(author_name, base_url, article_title)`.
3. **Reconstruct the article URL** (`Utils.make_url`) — the digest links point
   at a `?source=...reader-...` redirect, not the real article. `make_url`
   slugifies the title via `convert_text` (lowercase, spaces→`-`, strip
   non-alphanumeric) and splices in the article hash pulled out of the
   `reader-` token in the query string to build the canonical
   `medium.com/<pub>/<slug>-<hash>` URL.
4. **Filter noise** — entries whose author equals a value in `except_list`
   (`·Member`, `Edit who you follow`, `Control your recommendations`,
   `·Terms of service`) are Medium nav/footer links and are skipped.
5. **Crawl** — `urllib.request` with a `Mozilla/5.0` User-Agent, parsed by
   **BeautifulSoup** (`html.parser`). Title = `soup.select_one("h1")`,
   body = joined text of `.pw-post-body-paragraph` elements.
6. **Output** — JSON. The single-instance path returns one
   `{ url, title, text }`; the batch path (`merge_json`) returns a list of
   `{ title, content }`.

## Running locally

There is no build system, `requirements.txt`, or test runner. Set up manually:

```bash
pip install requests beautifulsoup4   # urllib, re, json are stdlib
```

The `main()` functions in the `.py` modules read a file named **`mail.txt`**,
which is not committed (only `mail.json` is). To run locally you must either
create `mail.txt` from the `"text"` field of `mail.json`, or adapt the loader
to read `mail.json`. The `.ipynb` notebook similarly expects `mail.txt`.

Python 3.11 is available in this environment; the notebook output shows it was
also developed under 3.13.

## Conventions

- **Comments and docstrings are in Korean.** Match the surrounding language
  when editing existing code; new top-level explanation can be bilingual.
- **Lambda shape:** entry points are `lambda_handler(event, context)` and
  return `{ "statusCode", "headers"?, "body" }`. Keep new handlers consistent.
- **Class style:** logic is grouped in a `Mail_Crawler` class with a stateless
  `Utils` helper class instantiated ad-hoc (`Utils().method(...)`).
- HTTP requests always send the `Mozilla/5.0` User-Agent; Medium blocks the
  default urllib agent.
- Crawl extraction depends on Medium's `.pw-post-body-paragraph` CSS class and
  the `h1` title — these are brittle against Medium markup changes; verify
  selectors still match if extraction returns empty.

## Known inconsistencies (read before editing)

The root modules were refactored from `test/` and the wiring drifted. If you
touch this code, expect to fix these:

1. **Import name mismatch:** `mail_crawler_single_ins.py` does
   `from utils import Utils`, but the root helper file is named **`util.py`**
   (singular). As-is this import fails at the root level; it only resolves
   inside `test/` where the file is `utils.py`.
2. **`make_url` signature mismatch:** both `util.py` and `test/utils.py` define
   `make_url(self, author_name, base_url, article_title)` (three args), but the
   crawlers call it as `Utils().make_url(self.origin_url, index)` (two args).
   The **notebook** version `make_url(urls, idx)` is the one that actually
   works — use it as the reference contract.
3. **Missing parse step:** the root `Mail_Crawler.__init__` stores raw `data`
   directly as `self.origin_url`, skipping `Utils().url_tuples(data)`. The
   `test/mail_crawler.py` version correctly parses first.
4. **`mail.txt` vs `mail.json`:** `main()` and the notebook open `mail.txt`,
   which isn't in the repo — only `mail.json` is.

When asked to "make it run," reconcile these against the working notebook logic
rather than assuming the `.py` modules are correct.

## Git workflow

- Active development branch for this work: `claude/claude-md-docs-jf33se`.
- Default branch: `main`.
- Push with `git push -u origin <branch>`; do not push to `main` without
  explicit permission, and do not open a PR unless asked.

## Secrets / privacy

`notion_DB.txt` and the sample digest in `mail.json` contain a personal Notion
workspace URL and personal Medium account references. Avoid leaking these into
logs or external services, and don't commit real email dumps (`mail.txt`).
