
from gpt import GPT

from pathlib import Path

import ollama

# OLLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "tetrish"
MODELFILE_PATH = f"models\{MODEL_NAME}.llama"



class OllamaInterface(GPT):

    def __init__(self, tools: dict, game_context):
        # check if model exists
        try:
            ollama.show(MODEL_NAME)
        except ollama.ResponseError as e:
            print(f"Model {MODEL_NAME} not found. Creating..")
            ollama.create(MODEL_NAME, MODELFILE_PATH)
        
        self.client = ollama.Client()

        self.tools = tools

        self.messages = [('system', f'Current game: {game_context}')]
        
        print("Model ready")
        


    def prompt(self, prompt) -> str:

        self.messages.append(('user', prompt))

        response = self.client.chat(
            model=MODEL_NAME,
            messages=[ {'role': role, 'content': content} for role,content in self.messages ],
            tools=[t["interface"] for t in self.tools.values()]
        )

        if response['message']['content'] == "":
            tools_calls = response['message']['tool_calls']

            print("Calling tools: ", tools_calls)

            new_state = None
            
            for tool_call in tools_calls:
                try:
                    tool_name = tool_call['function']['name']
                    tool = self.tools[tool_name]
                    
                    function = tool['callable']
                    kwarguments = tool_call['function']['arguments']
                    
                    # call the function
                    (log, new_state) = function(**kwarguments)

                    self.messages.append(('tool', f"{tool_name} executed with {kwarguments}. Log: {log}"))

                except Exception as e:
                    print(e)
                    print("Error calling tool")
                    self.messages.append(('tool', f"Error calling tool {tool_name} with {kwarguments}"))
            
            print("New state: ", new_state)
            if new_state:
                self.messages.append(('tool', f"Game state: {new_state}. Given the game state, please suggest for the user what a good next move would be."))

                response = self.client.chat(
                    model=MODEL_NAME,
                    messages=[ {'role': role, 'content': content} for role,content in self.messages ],
                    tools=[t["interface"] for t in self.tools.values()]
                )

                print("TEMP-Response: ", response)

                content = response['message']['content']
                self.messages.append(('assistant', content))
                return content
            
        else:
            content = response['message']['content']
            self.messages.append(('assistant', content))
            return content
            


OllamaInterface(tools={}, game_context="Tetrish")






# Available Commands:
#   serve       Start ollama
#   create      Create a model from a Modelfile
#   show        Show information for a model
#   run         Run a model
#   stop        Stop a running model
#   pull        Pull a model from a registry
#   push        Push a model to a registry
#   list        List models
#   ps          List running models
#   cp          Copy a model
#   rm          Remove a model
#   help        Help about any command