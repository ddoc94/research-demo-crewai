"""Render a company profile (markdown) as a styled, print-ready HTML document.

Tolerant of format drift: accepts summary fields as CAPS lines or markdown bullets,
and provenance as a bare tag line or an inline attribution clause.
"""

import html as html_lib
import re
from datetime import date
from pathlib import Path

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
  padding: 0.65rem 0;
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
  padding-top: 0.8rem;
}

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

.finding .date {
  font-family: var(--mono);
  font-size: 0.625rem;
  letter-spacing: 0.06em;
  color: var(--faint);
  display: block;
  margin-top: 0.35rem;
}

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

# Accepts "COMPANY NAME: x", "- **company_name:** x", "* products_services: x"
FIELD_RE = re.compile(r"^\s*[-*]?\s*([A-Za-z][A-Za-z _/()]{2,45}?)\s*:\s*(.*?)\s*$")
# A trailing attribution clause the writer sometimes appends to a finding.
ATTRIB_TAIL = re.compile(
    r"[\s,.]*(?:The statement is|Reported by|Source[:s]?|According to|Sourced)\b.*$",
    re.I | re.S,
)
PROV_RE = re.compile(r"\b(company[- ]issued|independent)\b", re.I)
BARE_TAG_RE = re.compile(r"^\s*\**(COMPANY[- ]ISSUED|INDEPENDENT)\**\s*\.?\s*$", re.I)
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
UNKNOWNS = {"UNKNOWN", "N/A", "NOT ESTABLISHED", "NONE", ""}

# Section names the writer uses. Matched even when the markdown ## is missing.
KNOWN_HEADINGS = {
    "overview": "Overview",
    "company summary": "Company Summary",
    "summary": "Company Summary",
    "recent developments": "Recent Developments",
    "recent findings": "Recent Developments",
    "findings": "Recent Developments",
    "what could not be determined": "What Could Not Be Determined",
    "could not be determined": "What Could Not Be Determined",
    "what could not be established": "What Could Not Be Determined",
}


def _as_heading(line: str) -> str | None:
    """Return the canonical heading if this line is one, else None."""
    stripped = _strip_md(line).strip()
    if stripped.startswith("##"):
        return stripped.lstrip("#").strip()
    key = stripped.rstrip(":").strip().lower()
    if key in KNOWN_HEADINGS and len(stripped) < 60:
        return KNOWN_HEADINGS[key]
    return None


def _strip_md(text: str) -> str:
    return text.replace("**", "").replace("__", "")


def _prettify_label(label: str) -> str:
    return label.replace("_", " ").replace("/", " / ").upper()


_HEADING_NAMES = (
    r"Overview|Company Summary|Recent Developments|Recent Findings|"
    r"What Could Not Be Determined|Could Not Be Determined"
)
# Break before a heading that is glued to the end of the previous sentence.
_HEADING_BEFORE = re.compile(rf"(?<=[.\)])\s+(?=\b(?:{_HEADING_NAMES})\b)")
# Break after a heading that has body text glued to it on the same line.
_HEADING_AFTER = re.compile(rf"^\s*({_HEADING_NAMES})\s*:?\s+(?=\S)", re.MULTILINE)
_FIELD_SPLIT = re.compile(
    r"\s+(?=\b(?:COMPANY NAME|YEAR FOUNDED|PRIMARY INDUSTRY|HEADQUARTERS COUNTRY|"
    r"HEADQUARTERS|PUBLIC OR PRIVATE|PRODUCTS[ /]?SERVICES|TICKER|PARENT COMPANY|"
    r"EMPLOYEE COUNT|ANNUAL REVENUE|MARKET CAP)\b\s*:)"
)
_TAG_SPLIT = re.compile(r"\s*(?<=[.\)])\s+(COMPANY-ISSUED|INDEPENDENT)\b\s*", re.I)


def _unrun(md: str) -> str:
    """Re-break a profile the writer collapsed onto single lines."""
    md = _HEADING_BEFORE.sub("\n\n", md)
    md = _HEADING_AFTER.sub(lambda m: m.group(1) + "\n\n", md)
    md = _FIELD_SPLIT.sub("\n", md)
    md = _TAG_SPLIT.sub(lambda m: "\n" + m.group(1).upper() + "\n\n", md)
    return md


def _split_sections(md: str) -> list[tuple[str, list[str]]]:
    sections, heading, buffer = [], "", []
    for line in _unrun(md).splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("##"):
            continue
        found = _as_heading(line)
        if found:
            sections.append((heading, buffer))
            heading, buffer = found, []
        else:
            buffer.append(line)
    sections.append((heading, buffer))
    return sections


def _render_fields(lines: list[str]) -> str:
    rows = []
    for line in lines:
        if not line.strip():
            continue
        match = FIELD_RE.match(_strip_md(line))
        if not match:
            continue
        label, value = match.group(1).strip(), match.group(2).strip()
        if not label:
            continue
        cls = ' class="unknown"' if value.upper() in UNKNOWNS else ""
        rows.append(
            f"<dt>{html_lib.escape(_prettify_label(label))}</dt>"
            f"<dd{cls}>{html_lib.escape(value or 'UNKNOWN')}</dd>"
        )
    return f'<dl class="fields">{"".join(rows)}</dl>' if rows else ""


def _render_findings(lines: list[str], urls: list[str]) -> str:
    blocks: list[str] = []
    body_lines: list[str] = []
    tag: str | None = None

    def flush():
        nonlocal body_lines, tag
        raw = " ".join(l for l in body_lines if l).strip()
        local_tag, body_lines, tag = tag, [], None
        if not raw:
            return

        # Pull URLs out before anything is stripped, so footnotes survive.
        found_urls = URL_RE.findall(raw)
        found_date = DATE_RE.search(raw)

        if local_tag is None:
            tail = ATTRIB_TAIL.search(raw)
            if tail:
                found = PROV_RE.search(tail.group(0))
                local_tag = found.group(1) if found else None

        body = URL_RE.sub("", ATTRIB_TAIL.sub("", raw)).strip(" ,;.")
        if body:
            body += "."

        refs = ""
        for url in found_urls:
            cleaned = url.rstrip(".,;:)")
            if cleaned not in urls:
                urls.append(cleaned)
            refs += f'<sup class="fn">{urls.index(cleaned) + 1}</sup>'

        marker = ""
        if local_tag:
            normalised = local_tag.replace(" ", "-").upper()
            cls = "issued" if normalised.startswith("COMPANY") else "independent"
            label = "Company-issued" if cls == "issued" else "Independent"
            marker = f'<span class="tag {cls}">{label}</span>'

        stamp = (
            f'<span class="date">{html_lib.escape(found_date.group(1))}</span>'
            if found_date
            else ""
        )
        blocks.append(f'<div class="finding">{marker}<p>{body}{refs}{stamp}</p></div>')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
        elif BARE_TAG_RE.match(stripped):
            tag = BARE_TAG_RE.match(stripped).group(1)
            flush()
        else:
            body_lines.append(html_lib.escape(_strip_md(stripped)))
    flush()
    return "".join(blocks)


def _footnote(match, urls: list[str]) -> str:
    url = match.group(0).rstrip(".,;:)")
    if url not in urls:
        urls.append(url)
    return f'<sup class="fn">{urls.index(url) + 1}</sup>'


def _render_gaps(lines: list[str]) -> str:
    items = []
    for line in lines:
        stripped = _strip_md(line).strip().lstrip("-* ").strip()
        if not stripped or stripped.lower().startswith("this profile is"):
            continue
        items.append(f"<li>{html_lib.escape(stripped)}</li>")
    return f'<ul class="gaps">{"".join(items)}</ul>' if items else ""


def _render_prose(lines: list[str], urls: list[str]) -> str:
    paragraphs, chunk = [], []
    for line in lines:
        if line.strip():
            chunk.append(html_lib.escape(_strip_md(line).strip()))
        elif chunk:
            paragraphs.append(" ".join(chunk))
            chunk = []
    if chunk:
        paragraphs.append(" ".join(chunk))
    return "".join(
        f"<p>{URL_RE.sub(lambda m: _footnote(m, urls), p)}</p>" for p in paragraphs
    )


def render(profile_markdown: str, company: str, out_dir: Path = Path("output")) -> Path:
    urls: list[str] = []
    parts: list[str] = []

    for heading, lines in _split_sections(profile_markdown):
        if not "\n".join(lines).strip():
            continue
        key = heading.lower()
        if heading:
            parts.append(f"<h2>{html_lib.escape(heading)}</h2>")

        if "summary" in key:
            rendered = _render_fields(lines)
            parts.append(rendered or _render_prose(lines, urls))
        elif "development" in key or "finding" in key:
            parts.append(_render_findings(lines, urls))
        elif "could not" in key or "determined" in key or "unknown" in key:
            parts.append(_render_gaps(lines))
        else:
            parts.append(_render_prose(lines, urls))

    sources = ""
    if urls:
        items = "".join(f"<li>{html_lib.escape(u)}</li>" for u in urls)
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
  {"".join(parts)}
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
