# Company Research Profiler

This repo contains a CrewAI demo Flow comprised of two crews and three agents. It takes in a company name, researches it, and creates a brief company profile containing:

- Six summary fields — name, founding year, industry, headquarters, public/private, products
- Three findings — a recent development, an identified risk, and a capital action
- A source URL and date on every finding
- A provenance label on every finding: company-issued or independent

<br>

# Getting Started

### 1. Prerequisites
- Python 3.10+
- uv — handles Python versions, virtual environments, and packages. Install it with:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen terminal so it picks up PATH.

<br>

### 2. Clone and install

```
git clone https://github.com/ddoc94/research-demo-crewai.git
cd research-demo-crewai
uv sync
```

<br>

### 3. Add API keys

Example includes OpenAI key, but any other cloud LLM provider can be used.

- OPENAI_API_KEY:	platform.openai.com (for model inference)
- SERPER_API_KEY:	serper.dev	(for web search)

Rename example .env:

```
cp .env.example .env
```

Add keys to .env:
```
OPENAI_API_KEY=sk-...
<br>SERPER_API_KEY=...
```

.env is gitignored, so keys stay local.

<br>

### 4. Run it

```
uv run kickoff
```

It prompts for a company name and takes about a minute, printing each stage as it goes. Results land in output/ as markdown and HTML:

```
open output/<company>_profile.html
```

`uv run plot` generates a diagram of the flow.

<br>

# Flow Architecture
      ── @start           set company + run date
      ├─ Research Crew    Researcher (has tools) → Verifier (no tools)
      ├─ @router          enough verified findings?
      ├─ Writing Crew     Writer, or a gap report
      └─ render HTML      plain Python, no model

A Flow handles orchestration, state, and branching. Two Crews handle the parts that need judgment. Everything else is just Python.

<br>

# Known limitations

- Aggregators and Wikipedia pass verification more often than they should. Pointing the researcher at investor relations pages and SEC filings first would fix most of this.
- The verifier checks internal consistency only. It can't fetch a source to compare against it.
- Many publications like Reuters, Bloomberg, and WSJ block scrapers, which biases available sources toward company-issued material, which is not ideal.
- No evaluation harness. Output quality is assessed by reading it.

CrewAI · OpenAI API (or Ollama) · Serper · Pydantic · BeautifulSoup
