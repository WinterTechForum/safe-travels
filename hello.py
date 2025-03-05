# Import relevant functionality
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Create the agent
memory = MemorySaver()
model = ChatOpenAI(model_name="gpt-4o")
search = TavilySearchResults(max_results=2)
tools = [search]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

# Use the agent
config = {"configurable": {"thread_id": "abc123"}}
for step in agent_executor.stream(
        {"messages": [HumanMessage(content="hi im bob! and i live in Crested Butte, CO")]},
        config,
        stream_mode="values",
):
    step["messages"][-1].pretty_print()

# for step in agent_executor.stream(
#         {"messages": [HumanMessage(content="plot a route from where I live to Denver, CO")]},
#         config,
#         stream_mode="values",
# ):
#     step["messages"][-1].pretty_print()

for step in agent_executor.stream(
        {"messages": [HumanMessage(content="Get the latitude and longitude for my city.")]},
        config,
        stream_mode="values",
):
    step["messages"][-1].pretty_print()
