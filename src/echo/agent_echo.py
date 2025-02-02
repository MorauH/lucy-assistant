# a langchain agent that has access to calendar

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from langchain_openai import ChatOpenAI

from .tools_wikipedia import get_tools as get_wiki_tools
from .tools_duck import get_tools as get_duck_tools



agent_instructions = f'''
You are an research and fact-checking assistant. You are designed to help users find accurate and reliable information on a wide range of topics. Your goal is to provide well-researched and trustworthy answers to user queries.

# Steps

1. Understand the request
2. Gather useful information with the tools
3. Analyze the information
4. Respond to the query with accurate and reliable information

# Notes
- Answers should be concise and informative
- Only answer with information that is relevant to the request
'''

instruction_msg = SystemMessage(content=agent_instructions)

class AgentEcho:
    def __init__(self):
        self.tools = get_duck_tools() + get_wiki_tools()
        self.memory = MemorySaver() # TODO: should it have memory?
        self.llm = ChatOpenAI(model='gpt-4o-mini')
        self.agent_executor = create_react_agent(model=self.llm, tools=self.tools, checkpointer=self.memory)
    
    def prompt(self, prompt: str):
        messages = [instruction_msg, HumanMessage(content=prompt)]
        
        for chunk in self.agent_executor.stream({"messages": messages}, {"configurable": {"thread_id": "echo"}}):
            print(chunk)
            print("----")

            # add chunk messages to messages if exist
            if "agent" in chunk:
                messages.extend(chunk["agent"]["messages"])
            elif "tools" in chunk:
                messages.extend(chunk["tools"]["messages"])
                
        # return the last message
        return messages[-1].content

