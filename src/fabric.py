
from queue import Queue
import threading

from stt import LiveSST
from tts import TTS
from cortex import Cortex

import sounddevice as sd

# interconnects the cortex, tts, stt


agent_to_tts_queue = Queue()
sst_to_agent_queue = Queue()

# interrupt flag
interrupt_tts = threading.Event()


def sst_loop():
    stt = LiveSST()
    stt.start_continous()

    # TODO: Codewords for start/stop passthrough to agent (collect until stop-word)
    for text in stt.get_transcription():
        sst_to_agent_queue.put(text)






def tts_loop():
    tts = TTS(speaker='EN-BR')
    while True:
        text = agent_to_tts_queue.get()
        audio = tts.tts_audio(text)
        
        # play audio with sounddevice but allow for interrupt
        sd.play(audio, tts.sample_rate)
        while sd.get_stream().active and not interrupt_tts.is_set():
            pass
        sd.stop()
        interrupt_tts.clear()

def main():
    sst_thread = threading.Thread(target=sst_loop)
    tts_thread = threading.Thread(target=tts_loop)

    sst_thread.start()
    tts_thread.start()

    cortex = Cortex()

    while True:
        print("Listening for input...")
        text = sst_to_agent_queue.get(block=True)

        print(f"Received input: {text}")
        response = cortex.prompt(text)

        print(f"Response: {response}")
        agent_to_tts_queue.put(response)


if __name__ == '__main__':
    main()