# CLAUDE.md — wearcoach wiki schema

This repo can run an **LLM Wiki** ([Karpathy's pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)):
a persistent, compounding knowledge base the LLM maintains so coaching advice
draws on accumulated context (your goals, injuries, races, patterns) instead
of re-deriving everything from raw data every session.

This file is the **schema** — it tells the LLM how the wiki is structured and
how to operate on it. The wiki itself lives in `wiki/`. Start every wiki task
at `wiki/index.md`.

This is optional. `python main.py brief` works fine without ever touching
this file — it's for people who also want to talk to their coach in Claude
Code (or any LLM with file access) and have it remember things between
sessions.

## Three layers

1. **Raw data** (immutable inputs): `data/snapshot-*.json` and
   `data/briefing-*.md` (written by `python main.py fetch` / `brief`). Never
   edit these to "fix" the wiki — they are ground truth from Strava/Oura/Garmin.
2. **The wiki** (`wiki/`): LLM-written markdown — entity pages (you, races,
   gear) and concept pages (recurring patterns, rules you've learned about
   your own training).
3. **The schema** (this file).

## Layout

```
wiki/
  index.md      catalog of every page: link + one-line summary, grouped by category
  log.md        append-only history of wiki operations
  entities/     concrete things: you (the athlete), races, gear
  concepts/     reusable knowledge: what tends to happen when X (patterns, thresholds)
```

## Page format

Every wiki page starts with frontmatter, then prose with cross-links and source citations:

```markdown
---
title: <human title>
slug: <kebab-case>            # used for [[slug]] links
type: entity | concept
updated: YYYY-MM-DD
sources: [data/snapshot-2026-07-20.json, ...]
---

# Title

Body. Link other pages with [[slug]]. Cite raw data files so claims are traceable.

## See also
- [[other-slug]]
```

Conventions:
- **One subject per page.** Split before a page sprawls.
- **Cross-link liberally** with `[[slug]]`. A `[[slug]]` with no page yet marks
  a page worth writing — not an error.
- **Cite sources.** Every quantitative claim names the raw data file it came from.
- Keep this `CLAUDE.md` lean — it loads into every session. Detail belongs in wiki pages.

## Operations

### Ingest (new briefing or a conversation surfaced something durable)
1. Read the new `data/briefing-*.md` or the conversation.
2. Write/extend the relevant entity or concept page (cite the source).
3. Update `wiki/index.md`.
4. Append to `wiki/log.md`.

### Query (you ask a question)
1. Search relevant wiki pages first; fall back to raw `data/` files for gaps.
2. Answer with citations to the pages/files used.
3. If the synthesis was non-trivial and reusable, file it back as a new/updated
   page + log it.

### Lint (periodic health check)
Scan for: contradictions between pages, stale claims (check `updated:` vs
`data/` files), orphan pages, missing cross-references, and `[[slugs]]` with
no page. Report findings; fix the cheap ones; surface the rest.

## log.md format
Append-only, newest at the bottom:
```
## [YYYY-MM-DD] <ingest|query|lint|create> | <short title>
- what changed / what was decided
```
