import os
from sys import platform
from queue import Queue
from time import sleep
from datetime import datetime, timedelta

import torch
import whisper
import numpy as np
import speech_recognition as sr
import sounddevice



def print_mic_names():
    print('Available microphones: ')
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f'{index}: {name}')


class STT:
    def __init__(self):
        self.model = whisper.load_model('base')

    def transcribe_file(self, audio_path):
        result = self.model.transcribe(audio_path)
        return result['text']
    
    def transcribe_audio(self, audio, sample_rate):
        result = self.model.transcribe()

SAMPLE_RATE = 16000 # default for whisper

class LiveSST():
    # Inspired by: https://github.com/davabase/whisper_real_time

    def __init__(self, model='base', energy_threshold=1000, record_split=2, phrase_timeout=3, mic_name='default'):
        """
        model: str - 'tiny', 'base', 'small', 'medium', 'large'
        energy_threshold: float - Energy level for mic to detect speech
        record_split: int - Time in seconds until partial transcription is returned
        phrase_timeout: int - Time in seconds until new line in transcription
        mic_name: str - 'default', 'pulse', 'alsa', 'jack', 'portaudio', - Default microphone source
        """
        self.record_split = record_split
        self.phrase_timeout = phrase_timeout

        self.model = whisper.load_model(model)

        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = energy_threshold
        self.recorder.dynamic_energy_threshold = False

        self.generate_audio_source(mic_name)
        

        
    
    def generate_audio_source(self, mic_name):
        if not 'linux' in platform:
            self.source = sr.Microphone(sample_rate=SAMPLE_RATE)
        else:
            sources = sr.Microphone.list_microphone_names()
            if mic_name in sources:
                self.source = sr.Microphone(device_index=sources.index(mic_name), sample_rate=SAMPLE_RATE)
            else:
                print(f'Error: Microphone {mic_name} not found.')
                print_mic_names()
                exit(1)
        

    @staticmethod
    def concat_data_to_current_audio(last_sample, data_queue):
        while not data_queue.empty():
            data = data_queue.get()
            last_sample += data
        return last_sample
    
    def transcribe_audio(self, audio_np):
        # Read the transcrption
        result = self.model.transcribe(audio_np, fp16=torch.cuda.is_available())
        return result['text'].strip()
    
    def transcribe_bytes(self, audio_bytes):
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return self.transcribe_audio(audio_np)


    def start_old(self):
        phrase_time = None # Last time retrieved a recording from the queue
        data_queue = Queue()
        transcription = ['']
        
        np_phrase = Queue() # Buffer for audio data


        def record_callback(_, audio:sr.AudioData) -> None:
            """
            Threaded callback function to receive audio data when recordings finish.
            audio: An AudioData containing the recorded bytes.
            """
            # Grab the raw bytes and push it into the thread safe queue.
            data = audio.get_raw_data()
            data_queue.put(data)

        with self.source as source:
            self.recorder.adjust_for_ambient_noise(source)

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=self.record_split)

        print('Listening...')

        while True:
            try:
                now = datetime.now()

                if data_queue.empty():
                    sleep(0.25)
                else:
                    phrase_complete = False

                    if phrase_time and now - phrase_time > timedelta(seconds=self.phrase_timeout):
                        phrase_complete = True
                    
                    phrase_time = now

                    # Combine audio data from queue
                    audio_data = b''.join(data_queue.queue)

                    # Convert in-ram buffer to something the model can use directly without needing a temp file.
                    # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                    # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                    audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                    #np_phrase = np.concatenate((np_phrase, audio_np))

                    text = self.transcribe_audio(audio_np)

                    

                    # If we detected a pause between recordings, add a new item to our transcription.
                    # Otherwise edit the existing one.
                    if phrase_complete:
                        transcription.append(text)
                        data_queue.queue.clear()
                    else:
                        transcription[-1] = text
                    
                    # Clear the console to reprint the updated transcription.
                    os.system('cls' if os.name=='nt' else 'clear')
                    for line in transcription:
                        print(line)
                    # Flush stdout.
                    print('', end='', flush=True)
            except KeyboardInterrupt:
                break
        
        print("\n\nTranscription:")
        for line in transcription:
            print(line)
        


    def start(self):
        phrase_time = None # Last time retrieved a recording from the queue
        data_queue = Queue()
        buffer = bytearray()

        transcription = ['']
        

        def record_callback(_, audio:sr.AudioData) -> None:
            """
            Threaded callback function to receive audio data when recordings finish.
            audio: An AudioData containing the recorded bytes.
            """
            # Grab the raw bytes and push it into the thread safe queue.
            data = audio.get_raw_data()
            data_queue.put(data)

        with self.source as source:
            self.recorder.adjust_for_ambient_noise(source)
        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=self.record_split)
        print('Listening...')

        while True:
            try:
                now = datetime.now()

                if phrase_time and now - phrase_time > timedelta(seconds=self.phrase_timeout):
                    # Silence detected, end phrase.
                    phrase_time = None
                    
                    text = self.transcribe_bytes(buffer)
                    buffer.clear()
                    
                    if text != '':
                        transcription.append(text)
                    
                    # Clear the console to reprint the updated transcription.
                    os.system('cls' if os.name=='nt' else 'clear')
                    for line in transcription:
                        print(line)
                    # Flush stdout.
                    print('', end='', flush=True)
                    continue

                if data_queue.empty():
                    sleep(0.25)
                    continue

                phrase_time = now

                # Combine audio data from queue
                buffer += b''.join(data_queue.queue)
                data_queue.queue.clear()
                print(f'Buffer size: {len(buffer)}')
            except KeyboardInterrupt:
                break
        
        print("\n\nTranscription:")
        for line in transcription:
            print(line)
        
        
    
if __name__ == '__main__':
    #print_mic_names()

    stt = LiveSST()
    stt.start()
    print('Done.')
    