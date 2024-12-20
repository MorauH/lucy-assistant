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

class Cortex:
    def __init__(self):
        self.tools = get_tools(execute_string_callable=self.execute_string, create_tool_callable=self.create_tool)
        self.memory = MemorySaver()
        self.llm = ChatOpenAI(model='gpt-4o-mini')
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
            messages = [HumanMessage(content=prompt)]

            while self.start_stream:
                self.start_stream = False
                for chunk in self.agent_executor.stream({"messages": messages}, {"configurable": {"thread_id": "abc123"}}):
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