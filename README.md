# Lost Lake Community Thread — Newsletter Archive

Scraped issues of Lost Lake's COVID-era newsletter, intended for printing as a personal cookbook/recipebook.

- `newsletters/` — one markdown file per issue, named `YYYY-MM-DD-vol-XX.md`
- `images/` — locally-cached photos referenced by the markdown
- `cache/` — raw HTML pulled from Mailchimp (re-runs use this; delete to refetch)
- `scrape.py` — the scraper

## Re-running

```sh
./venv/bin/python scrape.py
```

## Notes on volume numbering

The original publication labeled both 04/28/2020 and 04/30/2020 as "Volume 12", and both 04/14/2020 and 04/16/2020 as "Volume 8". Filenames disambiguate with `a`/`b` suffixes; the `# heading` inside each file preserves whatever the original page title said.
