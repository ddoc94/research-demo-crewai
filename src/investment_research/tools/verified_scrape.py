"""A scraping tool that rejects blocked, empty, and non-text pages before the agent sees them."""

import re
from typing import Type

import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Sites that reliably block automated access. Cheaper to skip than to fetch and discard.
BLOCKED_DOMAINS = {
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "ft.com",
    "spglobal.com",
    "barrons.com",
    "economist.com",
    "nytimes.com",
    "seekingalpha.com",
}

# Phrases that mean the page is a wall, not content.
BLOCK_SIGNALS = [
    "enable javascript",
    "prove you are not a robot",
    "access to this page has been denied",
    "security controls triggered",
    "please enable js",
    "checking your browser",
    "captcha",
    "subscribe to continue",
    "subscribers only",
    "you have reached your article limit",
    "oops, something went wrong",
]

MIN_CHARS = 300  # below this, a "successful" fetch is almost always a stub or error page


class ScrapeInput(BaseModel):
    url: str = Field(..., description="The URL of the page to read.")


class VerifiedScrapeTool(BaseTool):
    name: str = "read_verified_page"
    description: str = (
        "Read the readable text of a web page. Returns the page text, or a short "
        "message explaining why the page could not be read. Only use URLs returned "
        "by a search. Never guess a URL."
    )
    args_schema: Type[BaseModel] = ScrapeInput

    def _run(self, url: str) -> str:
        url = url.strip().rstrip(".,);")

        # 1. Skip domains known to block scrapers.
        host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
        if any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS):
            return f"UNREADABLE: {host} blocks automated access. Do not cite this URL."

        # 2. Skip PDFs and other binaries.
        if url.lower().split("?")[0].endswith((".pdf", ".zip", ".xlsx", ".doc", ".docx")):
            return f"UNREADABLE: {url} is not an HTML page. Do not cite this URL."

        # 3. Fetch.
        try:
            resp = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"},
            )
        except Exception as exc:
            return f"UNREADABLE: request failed ({type(exc).__name__}). Do not cite this URL."

        if resp.status_code != 200:
            return f"UNREADABLE: HTTP {resp.status_code}. Do not cite this URL."

        # 4. Reject non-HTML payloads before parsing them.
        content_type = resp.headers.get("content-type", "").lower()
        if "html" not in content_type and "text" not in content_type:
            return f"UNREADABLE: content type {content_type}. Do not cite this URL."

        # 5. Strip markup down to readable prose.
        soup = BeautifulSoup(resp.text, "html.parser")
        for junk in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            junk.decompose()
        text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))

        # 6. Reject walls and stubs.
        lowered = text[:3000].lower()
        for signal in BLOCK_SIGNALS:
            if signal in lowered:
                return f"UNREADABLE: page is a block or paywall notice. Do not cite this URL."

        if len(text) < MIN_CHARS:
            print(f"[scrape] rejected {url} — only {len(text)} chars")
            return f"UNREADABLE: page returned only {len(text)} characters of text. Do not cite this URL."

        # 7. Cap length so one long page cannot swamp the context window.
        if len(text) > 12000:
            text = text[:12000] + "\n\n[truncated]"

        return f"READABLE CONTENT FROM {url}:\n\n{text}"
