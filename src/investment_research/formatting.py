"""Render a company profile (markdown) as a styled, print-ready HTML document."""

import html as html_lib
import re
from datetime import date
from pathlib import Path

import markdown

CSS = """
:root {
  --paper:  #FBFBFA;
  --ink:    #16181D;
  --muted:  #5C6270;
  --faint:  #8B91A0;
  --rule:   #DDDFE3;
  --indep:  #2C5F5A;
  --issued: #8C6D1F;
  --measure: 33rem;
  --rail: 8.5rem;
  --mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, monospace;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Charter, "Iowan Old Style", "Source Serif Pro", Georgia, serif;
  font-size: 16px;
  line-height: 1.62;
  -webkit-font-smoothing: antialiased;
}

.sheet {
  max-width: calc(var(--rail) + var(--measure));
  margin: 0 auto;
  padding: 5rem 2rem 6rem;
}

/* ---- masthead ---- */

.masthead {
  margin-left: var(--rail);
  border-bottom: 2px solid var(--ink);
  padding-bottom: 1.25rem;
  margin-bottom: 0.75rem;
}

.eyebrow {
  font-family: var(--mono);
  font-size: 0.6875rem;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: var(--faint);
  margin: 0 0 0.75rem;
}

.masthead h1 {
  font-size: 2.25rem;
  line-height: 1.1;
  letter-spacing: -0.02em;
  font-weight: 600;
  margin: 0;
}

.meta {
  margin-left: var(--rail);
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  font-family: var(--mono);
  font-size: 0.6875rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
  padding-bottom: 3rem;
  border-bottom: 1px solid var(--rule);
  margin-bottom: 3rem;
}

.meta b { font-weight: 400; color: var(--faint); }

/* ---- section headings ---- */

h2 {
  position: relative;
  margin: 3rem 0 1.25rem calc(-1 * var(--rail));
  padding-left: var(--rail);
  font-size: 0.75rem;
  font-family: var(--mono);
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink);
}

h2::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.55em;
  width: calc(var(--rail) - 1.5rem);
  border-top: 1px solid var(--ink);
}

p { margin: 0 0 1rem var(--rail); max-width: var(--measure); }

/* ---- field grid: the summary block ---- */

.fields {
  margin-left: var(--rail);
  max-width: var(--measure);
  display: grid;
  grid-template-columns: 11rem 1fr;
  column-gap: 1.5rem;
  border-top: 1px solid var(--rule);
}

.fields dt {
  font-family: var(--mono);
  font-size: 0.625rem;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--faint);
  padding: 0.6rem 0 0.6rem 0;
  border-bottom: 1px solid var(--rule);
  line-height: 1.5;
}

.fields dd {
  margin: 0;
  padding: 0.55rem 0;
  font-size: 0.9375rem;
  border-bottom: 1px solid var(--rule);
  line-height: 1.5;
}

.fields dd.unknown {
  font-family: var(--mono);
  font-size: 0.625rem;
  letter-spacing: 0.09em;
  color: var(--faint);
  padding-top: 0.75rem;
}

/* ---- findings with provenance rail ---- */

.finding {
  position: relative;
  margin: 0 0 1.5rem var(--rail);
  max-width: var(--measure);
}

.finding p { margin: 0; }

.tag {
  position: absolute;
  left: calc(-1 * var(--rail));
  top: 0.3em;
  width: calc(var(--rail) - 1.5rem);
  font-family: var(--mono);
  font-size: 0.625rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  line-height: 1.4;
  text-align: right;
  padding-right: 0.5rem;
  border-right: 2px solid currentColor;
}

.tag.independent { color: var(--indep); }
.tag.issued      { color: var(--issued); }

/* ---- footnotes and sources ---- */

sup.fn {
  font-family: var(--mono);
  font-size: 0.625rem;
  color: var(--indep);
  padding-left: 0.1em;
}

.sources { margin-top: 4rem; padding-top: 1.5rem; border-top: 1px solid var(--rule); }
.sources ol { margin-left: var(--rail); padding: 0; list-style: none; counter-reset: src; }

.sources li {
  counter-increment: src;
  position: relative;
  padding-left: 2rem;
  font-size: 0.75rem;
  line-height: 1.5;
  color: var(--muted);
  word-break: break-all;
  margin-bottom: 0.5rem;
}

.sources li::before {
  content: counter(src);
  position: absolute;
  left: 0;
  top: 0.15em;
  font-family: var(--mono);
  font-size: 0.625rem;
  color: var(--faint);
}

/* ---- gaps ---- */

.gaps { margin-left: var(--rail); max-width: var(--measure); padding: 0; list-style: none; }

.gaps li {
  position: relative;
  padding-left: 1.1rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: var(--muted);
}

.gaps li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.72em;
  width: 5px;
  height: 1px;
  background: var(--faint);
}

.disclaimer {
  margin: 3rem 0 0 var(--rail);
  font-size: 0.6875rem;
  line-height: 1.5;
  color: var(--faint);
  max-width: var(--measure);
}

/* ---- narrow screens ---- */

@media (max-width: 42rem) {
  :root { --rail: 0rem; }
  .sheet { padding: 2.5rem 1.25rem 4rem; }
  .masthead h1 { font-size: 1.75rem; }
  h2 { margin-left: 0; padding-left: 0; }
  h2::before { display: none; }
  .fields { grid-template-columns: 1fr; }
  .fields dt { border-bottom: none; padding-bottom: 0; }
  .fields dd { padding-top: 0.15rem; }
  .tag {
    position: static;
    display: inline-block;
    width: auto;
    text-align: left;
    border-right: none;
    border-left: 2px solid currentColor;
    padding: 0 0 0 0.5rem;
    margin-bottom: 0.4rem;
  }
  .meta { gap: 1rem; }
}

@media print {
  :root { --paper: #fff; }
  .sheet { padding: 0; max-width: none; }
  h2 { break-after: avoid; }
  .finding, .fields dt, .fields dd { break-inside: avoid; }
  .sources { break-before: page; }
}
"""

FIELD_RE = re.compile(r"^([A-Z][A-Z /()]{2,40}):\s*(.*)$", re.MULTILINE)
URL_RE = re.compile(r"https?://[^\s<>\"')]+")
TAG_RE = re.compile(r"^(COMPANY-ISSUED|INDEPENDENT)\s*$", re.I)


def _split_sections(md: str) -> list[tuple[str, list[str]]]:
    """Break the markdown into (heading, lines) pairs."""
    sections: list[tuple[str, list[str]]] = []
    heading = ""
    buffer: list[str] = []
    for line in md.splitlines():
        if line.startswith("## "):
            sections.append((heading, buffer))
            heading = line[3:].strip()
            buffer = []
        elif line.startswith("# "):
            continue  # title comes from the masthead
        else:
            buffer.append(line)
    sections.append((heading, buffer))
    return sections


def _render_fields(lines: list[str]) -> str:
    rows = []
    for line in lines:
        match = FIELD_RE.match(line.strip())
        if not match:
            continue
        label, value = match.group(1).strip(), match.group(2).strip()
        cls = ' class="unknown"' if value.upper() in {"UNKNOWN", "N/A", ""} else ""
        display = html_lib.escape(value or "UNKNOWN")
        rows.append(f"<dt>{html_lib.escape(label)}</dt><dd{cls}>{display}</dd>")
    return f'<dl class="fields">{"".join(rows)}</dl>' if rows else ""


def _render_findings(lines: list[str], urls: list[str]) -> str:
    blocks, current, tag = [], [], None

    def flush():
        nonlocal current, tag
        text = " ".join(current).strip()
        if text:
            marker = ""
            if tag:
                cls = "issued" if tag.upper().startswith("COMPANY") else "independent"
                marker = f'<span class="tag {cls}">{html_lib.escape(tag.title())}</span>'
            blocks.append(f'<div class="finding">{marker}<p>{text}</p></div>')
        current, tag = [], None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
        elif TAG_RE.match(stripped):
            tag = stripped
            flush()
        else:
            def swap(m):
                url = m.group(0).rstrip(".,;:)")
                if url not in urls:
                    urls.append(url)
                return f'<sup class="fn">{urls.index(url) + 1}</sup>'
            current.append(URL_RE.sub(swap, html_lib.escape(stripped)))
    flush()
    return "".join(blocks)


def _render_gaps(lines: list[str]) -> str:
    items = [
        f"<li>{html_lib.escape(l.strip().lstrip('-* '))}</li>"
        for l in lines
        if l.strip() and not l.strip().startswith("This profile is")
    ]
    return f'<ul class="gaps">{"".join(items)}</ul>' if items else ""


def render(profile_markdown: str, company: str, out_dir: Path = Path("output")) -> Path:
    urls: list[str] = []
    body_parts: list[str] = []

    for heading, lines in _split_sections(profile_markdown):
        text = "\n".join(lines).strip()
        if not text:
            continue

        key = heading.lower()
        if heading:
            body_parts.append(f"<h2>{html_lib.escape(heading)}</h2>")

        if "summary" in key and FIELD_RE.search(text):
            body_parts.append(_render_fields(lines))
        elif "development" in key or "finding" in key:
            body_parts.append(_render_findings(lines, urls))
        elif "could not" in key or "unknown" in key or "determined" in key:
            body_parts.append(_render_gaps(lines))
        else:
            body_parts.append(markdown.markdown(text, extensions=["extra"]))

    sources = ""
    if urls:
        items = "\n".join(f"<li>{html_lib.escape(u)}</li>" for u in urls)
        sources = f'<section class="sources"><ol>{items}</ol></section>'

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html_lib.escape(company)} — Company Profile</title>
<style>{CSS}</style>
</head>
<body>
<article class="sheet">
  <header class="masthead">
    <p class="eyebrow">Company profile</p>
    <h1>{html_lib.escape(company)}</h1>
  </header>
  <div class="meta">
    <span><b>Prepared</b> {date.today().isoformat()}</span>
    <span><b>Sources</b> {len(urls)}</span>
    <span><b>Method</b> Retrieved &amp; verified</span>
  </div>
  {"".join(body_parts)}
  {sources}
  <p class="disclaimer">
    Generated from retrieved sources and machine verification. Findings are labelled by
    provenance; company-issued material has not been independently corroborated.
    Fields marked unknown could not be sourced and have not been inferred.
  </p>
</article>
</body>
</html>"""

    out_dir.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")
    path = out_dir / f"{slug}_profile.html"
    path.write_text(doc, encoding="utf-8")
    return path
