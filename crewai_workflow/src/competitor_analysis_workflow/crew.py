import os

from crewai import LLM
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
	ScrapeWebsiteTool,
	BraveSearchTool
)





@CrewBase
class CompetitorAnalysisWorkflowCrew:
    """CompetitorAnalysisWorkflow crew"""

    
    @agent
    def market_scout(self) -> Agent:
        
        return Agent(
            config=self.agents_config["market_scout"],
            
            
            tools=[				ScrapeWebsiteTool()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
            ),
            
        )
    
    @agent
    def feature_analyst(self) -> Agent:
        
        return Agent(
            config=self.agents_config["feature_analyst"],
            
            
            tools=[				BraveSearchTool()],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
            ),
            
        )
    
    @agent
    def strategy_consultant(self) -> Agent:
        
        return Agent(
            config=self.agents_config["strategy_consultant"],
            
            
            tools=[],
            reasoning=False,
            max_reasoning_attempts=None,
            inject_date=True,
            allow_delegation=False,
            max_iter=25,
            max_rpm=None,
            
            max_execution_time=None,
            llm=LLM(
                model="openai/gpt-4o-mini",
                temperature=0.7,
            ),
            
        )
    

    
    @task
    def scout_competitor_website(self) -> Task:
        return Task(
            config=self.tasks_config["scout_competitor_website"],
            markdown=False,
            
            
        )
    
    @task
    def analyze_feature_comparison(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_feature_comparison"],
            markdown=False,
            
            
        )
    
    @task
    def create_swot_analysis_and_strategic_recommendations(self) -> Task:
        return Task(
            config=self.tasks_config["create_swot_analysis_and_strategic_recommendations"],
            markdown=False,
            
            
        )
    

    @crew
    def crew(self) -> Crew:
        """Creates the CompetitorAnalysisWorkflow crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )

    def _load_response_format(self, name):
        with open(os.path.join(self.base_directory, "config", f"{name}.json")) as f:
            json_schema = json.loads(f.read())

        return SchemaConverter.build(json_schema)
