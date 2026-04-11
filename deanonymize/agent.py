from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .prompts import STRATEGIST_INSTRUCTION
from .sub_agents import extractor_agent, retriever_agent, summarizer_agent
from config import settings

root_agent = LlmAgent(
    name="strategist",
    model=settings.gemini_model,
    description=(
        "Orchestrates de-anonymization attempts on pseudonymous identity records "
        "by coordinating the retriever, extractor, and summarizer agents."
    ),
    instruction=STRATEGIST_INSTRUCTION.format(max_iterations=settings.max_iterations),
    tools=[
        AgentTool(agent=retriever_agent),
        AgentTool(agent=extractor_agent),
        AgentTool(agent=summarizer_agent),
    ],
)
