
from gpt import GPT

from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()

TEMPERATURE = 0.5
MODEL = "gpt-4o-mini"


class Openai_Interface(GPT):

    def __init__(self, tools: dict, game_context):
        self.client = OpenAI()

        self.tools = tools

        self.messages = [("system", f"Current game: {game_context}")]
        
        print("Model ready")



    # def prompt(self, prompt) -> str:

    #     self.messages.append(('user', prompt))

    #     completion = self.client.chat.completions.create(
    #         model = MODEL,
    #         messages=[
    #             {"role": "system", "content": "You are a passive aggressive assistant."},
    #             {"role": "user", "content": prompt}
    #         ],
    #         tools=[t["interface"] for t in self.tools.values()]
    #     )

    #     return completion


if __name__ == "__main__":
    interface = Openai_Interface()
    prompt = input("Prompt: ")
    response = interface.prompt(prompt)
    print(response)
