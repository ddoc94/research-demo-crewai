from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from investment_research.tools.verified_scrape import VerifiedScrapeTool
from investment_research.schemas import ResearchOutput, VerifiedOutput


researcher_llm = LLM(model="openai/gpt-4o-mini")
verifier_llm = LLM(model="openai/gpt-4o")


@CrewBase
class ResearchCrew:
    """Research Crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            llm=researcher_llm,
            tools=[SerperDevTool(), VerifiedScrapeTool()],
        )

    @agent
    def verifier(self) -> Agent:
        return Agent(
            config=self.agents_config["verifier"],  # type: ignore[index]
            llm=verifier_llm,
            tools=[],
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],  # type: ignore[index]
            output_pydantic=ResearchOutput,
        )

    @task
    def verification_task(self) -> Task:
        return Task(
            config=self.tasks_config["verification_task"],  # type: ignore[index]
            output_pydantic=VerifiedOutput,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )