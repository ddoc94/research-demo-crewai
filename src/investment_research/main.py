#!/usr/bin/env python
from pathlib import Path

from pydantic import BaseModel

from crewai.flow import Flow, listen, or_, router, start

from datetime import date

from investment_research.crews.research_crew.research_crew import ResearchCrew
from investment_research.crews.writing_crew.writing_crew import WritingCrew
from investment_research import formatting

class ResearchState(BaseModel):
    company: str = ""
    today: str = ""
    verified_findings: str = ""
    findings_count: int = 0
    research_note: str = ""


class InvestmentResearchFlow(Flow[ResearchState]):

    @start()
    def set_target(self, crewai_trigger_payload: dict = None):
        self.state.today = date.today().isoformat()

        if crewai_trigger_payload:
            self.state.company = crewai_trigger_payload.get("company", "Stripe")
        elif not self.state.company:
            self.state.company = "Stripe"

        print(f"Researching: {self.state.company}")

    @listen(set_target)
    def run_research(self):
        print("Starting research crew")
        result = (
            ResearchCrew()
            .crew()
            .kickoff(inputs={"company": self.state.company, "today": date.today().isoformat()})
        )
        
        self.state.verified_findings = result.raw
        self.state.findings_count = result.pydantic.verified_count

        print(f"Research complete. Verified findings: {self.state.findings_count}")

    @router(run_research)
    def check_sufficiency(self):
        if self.state.findings_count >= 1:
            print("Sufficient findings — proceeding to write")
            return "sufficient"
        print("Insufficient findings — writing gap report instead")
        return "insufficient"

    @listen("sufficient")
    def write_note(self):
        print("Starting writing crew")
        result = (
            WritingCrew()
            .crew()
            .kickoff(inputs={
                "company": self.state.company,
                "verified_findings": self.state.verified_findings,
		"today": self.state.today,
            })
        )
        self.state.research_note = result.raw
        print("Note written")

    @listen("insufficient")
    def write_gap_report(self):
        self.state.research_note = (
            f"# Insufficient basis for a research note on {self.state.company}\n\n"
            f"Verification produced only {self.state.findings_count} supported findings, "
            f"below the threshold required to write a note.\n\n"
            f"## What the research produced\n\n{self.state.verified_findings}\n"
        )
        print("Gap report written")

    @listen(or_(write_note, write_gap_report))
    def save_note(self):
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        filename = f"{self.state.company.lower().replace(' ', '_')}_note.md"
        with open(output_dir / filename, "w") as f:
            f.write(self.state.research_note)
        print(f"Saved to output/{filename}")

    @listen(save_note)
    def make_html(self):
        path = formatting.render(self.state.research_note, self.state.company)
        print(f"Formatted note at {path}")
        print(self.usage_metrics)

def kickoff():
    company = input("Company to research: ")
    flow = InvestmentResearchFlow()
    flow.kickoff(inputs={"company": company, "today": date.today().isoformat()})


def plot():
    flow = InvestmentResearchFlow()
    flow.plot()