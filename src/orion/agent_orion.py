# a langchain agent that has access to calendar

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from .tools_calendar import get_tools
from langchain_openai import ChatOpenAI

from langchain.tools import StructuredTool
import datetime

today = datetime.date.today()


# TODO: Add messaging/email communication
agent_instructions = f'''
You are  an personal assistant. You manage the calendar, events.

# Steps

1. Understand the request
2. Gather useful information with the tools
3. Analyze the information
4. Utalize tools to fulfill the request
5. Respond with status update or completion

# Notes
- Answers should be concise and informative
- Only answer with information that is relevant to the request
- Use 24hr time format

# Context
- Today is {today}
'''

instruction_msg = SystemMessage(content=agent_instructions)

class AgentOrion:
    def __init__(self):
        self.tools = get_tools()
        self.memory = MemorySaver() # TODO: should it have memory?
        self.llm = ChatOpenAI(model='gpt-4o-mini')
        self.agent_executor = create_react_agent(model=self.llm, tools=self.tools, checkpointer=self.memory)
    
    def prompt(self, prompt: str):
        messages = [instruction_msg, HumanMessage(content=prompt)]
        
        for chunk in self.agent_executor.stream({"messages": messages}, {"configurable": {"thread_id": "abc124"}}):
            print(chunk)
            print("----")

            # add chunk messages to messages if exist
            if "agent" in chunk:
                messages.extend(chunk["agent"]["messages"])
            elif "tools" in chunk:
                messages.extend(chunk["tools"]["messages"])
                
        # return the last message
        return messages[-1].content

