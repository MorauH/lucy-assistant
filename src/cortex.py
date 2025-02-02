# Import necessary libraries from LangChain
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from tools.code_tools import get_tools
from langchain_openai import ChatOpenAI

from langchain.tools import StructuredTool

from orion.agent_orion import AgentOrion
from echo.agent_echo import AgentEcho

from pydantic import BaseModel


agent_instructions = '''
You are an AI assistant named Lucy, designed to be helpful, friendly, and efficient in assisting users with their queries, providing information, and solving problems.

# Steps

1. **Understanding the Query**: Carefully read and comprehend the user's request to ensure an accurate understanding.
   
2. **Gather Information**: If necessary, access your internal database or reasoning capabilities to collect relevant information related to the query.

3. **Reasoning**: Analyze the gathered information to determine the best response or solution to the user's request.

4. **Response Generation**: Construct a clear, concise, and friendly response that addresses the user's query or problem effectively.

5. **Follow-up**: If relevant, ask if the user needs further assistance with related or follow-up questions.

# Output Format

- **Response**: A friendly and concise paragraph that specifically addresses the user's query. The length will depend on the complexity of the user's question but should aim to be informative yet succinct.
- **Tone**: Friendly, supportive, and professional.

# Examples

**Example 1:**

- **Input**: "Lucy, what's the weather like today in New York?"
- **Reasoning**: Check the current weather forecast for New York using the latest data available.
- **Output**: "Today in New York, Lucy sees that it's sunny with a high of 75°F. Is there anything else I can assist you with regarding your plans for the day?"

**Example 2:**

- **Input**: "Lucy, can you help me find a good Italian restaurant?"
- **Reasoning**: Search for highly-rated Italian restaurants in the user's area based on recent reviews and ratings.
- **Output**: "Certainly! One great option is 'Trattoria Bello,' known for its authentic cuisine and cozy atmosphere. Would you like me to help with directions or reservations?"

# Notes

- Always ensure that the advice provided is up-to-date and accurate.
- Maintain a user-friendly tone that encourages further engagement.
- Be aware of the context in which the user is asking to provide more personalized responses.
'''
instruction_msg = SystemMessage(content=agent_instructions)

echo = AgentEcho()
orion = AgentOrion()

class PromptInput(BaseModel):
    prompt: str
subagent_tools = [
    StructuredTool.from_function(
        name="prompt_orion",
        func=orion.prompt,
        description="Prompt Orion agent for assistance. Orion manages the calendar, events, and tasks. Like a personal assistant.",
        args_schema=PromptInput,
    ),
    StructuredTool.from_function(
        name="prompt_echo",
        func=echo.prompt,
        description="Prompt Echo agent for assistance. Echo can access internet for research and fact-checking.",
        args_schema=PromptInput,
    ),
]

class Cortex:
    def __init__(self):
        # compile tools list
        self.tools = get_tools(execute_string_callable=self.execute_string, create_tool_callable=self.create_tool)
        self.tools.extend(subagent_tools)

        self.memory = MemorySaver()
        self.llm = ChatOpenAI(model='gpt-4o-mini')
        #self.llm = ChatOpenAI(model='openai-assistant')  # Use OpenAI assistant model
        self.agent_executor = create_react_agent(model=self.llm, tools=self.tools, checkpointer=self.memory)

        self.code_context = {}
        self.start_stream = False
    
    # executes python code string
    def execute_string(self, code):
        exec(code, self.code_context)

        # TODO: save important variables to memory?

        return "Code executed successfully"
    
    def create_tool(self, name:str, description: str, func: str): #, args_schema: Type[BaseModel]):
        print("Adding tool ----------------------------------")
        print(name)
        print(description)
        print(func)
        # print(args_schema)
        print("-------------------------------------------------")

        # intepret code
        self.execute_string(func)
        
        func_callable = self.code_context.get(name, None)

        if func_callable is None:
            return "Error: Function not found in context."

        new_tool = StructuredTool.from_function(
            name=name,
            func=func_callable,
            description=description,
            # args_schema=args_schema
        )
        self.tools.append(new_tool)
        self.start_stream = True
        
        return "Tool added successfully. Assistant restarted with new tools."# Available after next user prompt."
    
    def prompt(self, prompt: str):
        if prompt.lower() == "exit":
            return

        try:
            self.start_stream = True # start stream once
            messages = [instruction_msg, HumanMessage(content=prompt)]

            while self.start_stream:
                self.start_stream = False
                for chunk in self.agent_executor.stream({"messages": messages}, {"configurable": {"thread_id": "cortex"}}):
                    print(chunk)
                    print("----")

                    # add chunk messages to messages if exist
                    if "agent" in chunk:
                        messages.extend(chunk["agent"]["messages"])
                    elif "tools" in chunk:
                        messages.extend(chunk["tools"]["messages"])
                    
                    if self.start_stream: # restart stream with updated agent
                        self.agent_executor = create_react_agent(model=self.llm, tools=self.tools, checkpointer=self.memory)
                        break
            # return the last message
            return messages[-1].content
        except Exception as e:
            print(f"Error: {e}")


    def command_prompt(self):
        while True:
            prompt = input("Prompt: ")
            if prompt.lower() == "exit":
                break
            
            self.prompt(prompt)


def main():
    cortex_game = Cortex()
    cortex_game.command_prompt()

if __name__ == "__main__":
    main()