# Import relevant functionality
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from map import derive_route

# Create the agent
memory = MemorySaver()
model = ChatOpenAI(model="gpt-4o")
search = TavilySearchResults(max_results=2)
mapper = derive_route

tools = [mapper, search]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

# Use the agent
config = {"configurable": {"thread_id": "abc123"}}
for step in agent_executor.stream(
        {"messages": [HumanMessage(content="derive a route from Crested Butte, CO to Denver CO")]},
        config,
        stream_mode="values",
):
    step["messages"][-1].pretty_print()
