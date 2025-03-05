#!/usr/bin/env python3
import uuid

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from danger_assessment import assess_danger
from routing import derive_route

# Create the agent
memory = MemorySaver()
model = ChatOpenAI(model="gpt-4o")
search = TavilySearchResults(max_results=2)
mapper = derive_route
danger_accessor = assess_danger

tools = [mapper, search, danger_accessor]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

thread_id = uuid.uuid4().hex
config = {"configurable": {"thread_id": thread_id}}

# HumanMessage(content="get the weather forecast at each point along that route, assuming we depart the origin city at 7:00 AM on 2025-03-08.")


for step in agent_executor.stream(
        {
            "messages": [
                HumanMessage(content='derive a route from Crested Butte, CO to Denver, CO, '
                                     'departing at 7:00 AM on 2025-03-08.'),
                HumanMessage(content='get any weather events at each point along that route, '
                                     'assuming we depart the origin city at 7:00 AM on 2025-03-08.'),
                HumanMessage(content='asses the danger of each point along that route using '
                                     'the results from the previous step.')
            ]
        },
        config,
        stream_mode="values",
):
    step["messages"][-1].pretty_print()