# Company Research Profiler

A multi-agent pipeline built on CrewAI. You give it a company name, it researches the company, checks its own claims against the sources they came from, and spits out a formatted profile.

I built this to learn CrewAI properly. The output is fine. The interesting part was everything that went wrong on the way there.

## What it does
Searches and scrapes pages about the company
Pulls out six summary fields and three findings: a recent development, a risk, a capital action — each with a source URL
A second agent checks every claim against the source it cites and throws out anything unsupported
Branches: enough verified findings → write the profile. Not enough → say so instead
Renders it as HTML

Every claim is labelled company-issued or independent, and the output shows that in the margin so you can see at a glance how much of the profile rests on the company's own material.

## Architecture
Flow  ── @start           set company + run date
      ├─ Research Crew    Researcher (has tools) → Verifier (no tools)
      ├─ @router          enough verified findings?
      ├─ Writing Crew     Writer, or a gap report
      └─ render HTML      plain Python, no model

Three decisions worth explaining:

Flow first, crews inside it. Orchestration, state and branching are ordinary Python. The crews only do the parts that need judgment. So the call on whether there's enough evidence to write is made by code, not by a model.

Verification is its own agent. Telling the researcher "only make supported claims" doesn't work. A second agent whose entire job is checking claims against sources

Formatting is not an agent. Markdown to styled HTML is deterministic. Putting it in an agent would cost tokens, vary between runs, and give the model a chance to quietly edit content that had already been verified. It was shaky when handled by an agent.

## Running it

Python 3.10+ and uv.

bash
uv sync
cp .env.example .env    # OPENAI_API_KEY and SERPER_API_KEY
uv run kickoff

Output goes to output/. uv run plot draws the flow.

## A Note on Running Locally

It also runs fully local through Ollama, since that was the original design, intended to not use API credits as I tested. You can swap the model strings in the two crew files and nothing leaves your machine. It was tough to make reliable though and get agents to either stick to instructions or not need very heavy prompting (which caused other problems). I used Qwen3-embedding 4b for embeddings, llama3.1 8b for the Researcher, Muse Glimmer 30b for the Verifier and Writer. It was an interesting experiment and uncovered a lot:

Model-specific failures

- 9B reasoning model emitted its internal thinking as the final answer
- Same model returned nothing at all when forced to a final answer mid-loop
- 8B instruct model fabricated sources and attributed them to pages it never visited
- 30B leaked chat-template tokens that broke JSON parsing

Speed and timeouts

- Local inference roughly 15-25 tokens/sec versus near-instant cloud, so runs took 15+ minutes
- Repeatedly hit max_execution_time and max_iter before finishing
- Runtime scaled with how much coverage a company had, making it unpredictable

Instruction-following under load

- Ignored stated search budgets. Models couldn't count their own tool calls
- Format specs drifted between runs until schemas were enforced
- Degraded noticeably as prompts accumulated constraints
- Struggled with reliable tool calling, which is why function_calling_llm had to point at a cloud model

Operational

- Three models loaded simultaneously created memory pressure on a laptop (I drained my battery like crazy too, my charger couldn't even keep up)
- Embeddings needed a separate local model, since memory and knowledge require one

CrewAI · OpenAI API (or Ollama) · Serper · Pydantic · BeautifulSoup
