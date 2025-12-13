"""
CrewAI Research Workflow Example

This is a real CrewAI workflow that researches a topic and creates a report.
Based on the CrewAI quickstart guide from https://docs.crewai.com/en/quickstart
"""

from crewai import Agent, Crew, Process, Task
from crewai_tools import SerperDevTool

# Define agents
researcher = Agent(
    role='Senior Research Analyst',
    goal='Conduct thorough research on the given topic and find the most relevant and up-to-date information',
    backstory='''You are an experienced research analyst with a knack for finding 
    cutting-edge information. You excel at uncovering the latest developments and 
    presenting information in a clear and concise manner. You have access to 
    search tools to find the most relevant information.''',
    verbose=True,
    allow_delegation=False,
    tools=[SerperDevTool()]
)

reporting_analyst = Agent(
    role='Reporting Analyst',
    goal='Create detailed, well-structured reports based on research findings',
    backstory='''You are a meticulous analyst with a keen eye for detail. You excel 
    at turning complex data into clear and concise reports that are easy to understand 
    and act upon. You ensure all information is properly formatted and organized.''',
    verbose=True,
    allow_delegation=False
)

# Define tasks
research_task = Task(
    description='''Conduct thorough research about {topic}. 
    Make sure you find any interesting and relevant information given 
    the current year is 2025. Focus on recent developments, trends, and key insights.''',
    expected_output='A list with 10 bullet points of the most relevant information about {topic}',
    agent=researcher
)

reporting_task = Task(
    description='''Review the research findings and create a comprehensive report. 
    Expand each topic into a full section with detailed information. 
    Make sure the report is well-structured and contains all relevant information.''',
    expected_output='''A fully-fledged report with the main topics, each with a full 
    section of information. Formatted as markdown without code blocks.''',
    agent=reporting_analyst
)

# Create the crew
research_crew = Crew(
    agents=[researcher, reporting_analyst],
    tasks=[research_task, reporting_task],
    process=Process.sequential,
    verbose=True
)

# This crew can be exported using:
# omium export-crew test-projects/crewai_research_workflow.py:research_crew -o crewai_workflow.json

