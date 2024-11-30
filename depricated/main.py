
import time

from games.tetrish import Tetrish
from interface_ollama import OllamaInterface


class main():
    def __init__(self):
        self.game = Tetrish(display_window=True)
        self.ollama = OllamaInterface(tools=self.game.tools, game_context=self.game.game_context)

        self.run()
    
    def run(self):


        while True:
            prompt = input("Prompt: ")
            if prompt == "exit":
                del(self.game)
            
            response = self.ollama.prompt(prompt)
            print(response)




if __name__ == "__main__":
    main()