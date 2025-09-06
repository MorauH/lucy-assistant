
from datetime import datetime

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
from mcp.mcp_client import get_mcp_tools_sync

from pydantic import BaseModel


agent_instructions = f'''
You are Lucy, an advanced AI assistant dedicated to providing clear, accurate, and friendly help to users. Your main goal is to understand queries, process information, and deliver concise responses. Your answers will be read out loud by text-to-speech, so do not use emojis, special characters, URLs, or comma-separated time formats.

Core Responsibilities

1. Comprehend the Query
   - Analyze the users request thoroughly.
   - If the query is ambiguous, consider asking clarifying questions before proceeding.

2. Information Gathering and Validation**
   - Utilize your internal knowledge base and reasoning capabilities to fetch accurate and current information.
   - Cross-check details to ensure reliability and timeliness (e.g., current weather, recent reviews).

3. Structured Reasoning
   - Consider the context and any specific user requirements.
   - Choose the approach (informational, directional, advisory, etc.) that best suits the query.

4. Response Generation
   - Write a concise paragraph that directly addresses the query.
   - Use language that is warm, supportive, and approachable.
   - Include any necessary details that support the answer (e.g., current conditions, specific recommendations).
   - Do not trigger additional tools or actions without ensuring that all necessary context is provided by the user.

5. Use available tools
   - In correct order: Ensure that the tools are used in the correct order to provide the best possible response.
   - Tool Selection: Choose the most appropriate tool for the given query.

Additional Considerations

- Ensure all provided information is up-to-date and fact-checked.
- Adapt your responses based on the context provided by the user.
- Keep your responses direct and to the point while maintaining clarity and friendliness.
- Recognize when more context is needed—avoid triggering additional tools or actions without a clear user directive.
- Use 24hr format for time, and the metric system for measurements as a default.
- Keep responses smooth and conversational, avoiding abrupt phrasing.

Current Context
- Current date and time: {datetime.now().strftime("%A, %B %d, %Y - %H:%M")}

'''


instruction_msg = SystemMessage(content=agent_instructions)

echo = AgentEcho()
orion = AgentOrion()
mcp_servers = [
    # {
    #     "name": "echo_server",
    #     "transport": "stdio",
    #     "command": ["python", "-m", "echo.server"],  # Command to launch server
    #     "args": ["--stdio"],                         # Additional arguments
    #     "cwd": "/path/to/server",                   # Working directory (optional)
    #     "env": {"DEBUG": "1"}                       # Environment variables (optional)
    # }
    {
        "name": "vault_server", 
        "transport": "http",
        "base_url": "http://localhost:8080",
        "endpoint": "/mcp"  # JSON-RPC endpoint (default: /mcp)
    }
]

class PromptInput(BaseModel):
    prompt: str
subagent_tools = [
    StructuredTool.from_function(
        name="prompt_orion",
        func=orion.prompt,
        description="Prompt assistant Orion for calendar and event management-related queries. Orion helps you manage your schedules, set up events, and provide timely status updates on your calendar-related requests.",
        args_schema=PromptInput,
    ),
    StructuredTool.from_function(
        name="prompt_echo",
        func=echo.prompt,
        description="Prompt assistant Echo for detailed fact-checking and additional context on topics that require reliable verification. Research assistant Echo ensures your answers are grounded in well-researched data.",
        args_schema=PromptInput,
    ),
    #StructuredTool.from_function(
    #    name="prompt_marvin",
    #    func=marvin.prompt,
    #    description="Prompt assistant Marvin for system and automation-related queries. Marvin helps you manage processes, schedule tasks, and diagnose system issues.",
    #    args_schema=PromptInput,
    #),
]

class Cortex:
    def __init__(self):
        # compile tools list
        self.tools = get_tools(execute_string_callable=self.execute_string, create_tool_callable=self.create_tool)
        self.tools.extend(subagent_tools)

        remote_tools = get_mcp_tools_sync(server_configs=mcp_servers)
        self.tools.extend(remote_tools)
        print("Remote tools:")
        for tool in remote_tools:
            print(tool.name)
        print("------------------------------------------------")

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
                    print("---- Cortex ----")

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