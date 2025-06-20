from google.adk.agents import SequentialAgent

from google.adk.tools.agent_tool import AgentTool

from .sub_agent.clause_retriever.agent import clause_retriever
from .sub_agent.drafting_agent.agent import drafting_agent




root_agent = SequentialAgent(
    name="LeadQualificationPipeline",
    sub_agents=[clause_retriever, drafting_agent],  #, export_agent],
    description="A pipeline that validates, scores, and recommends actions for sales leads",
)