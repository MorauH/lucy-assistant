from melo.api import TTS as MeloTTS

import nltk
nltk.download('averaged_perceptron_tagger_eng')




class TTS():
    def __init__(self, device='auto', speaker='EN-BR'):
        self.speed = 1.2
        self.model = MeloTTS(language='EN', device=device)
        self.sample_rate = self.model.hps.data.sampling_rate
        self.speaker_id = self.model.hps.data.spk2id[speaker]

    def tts_audio(self, text):
        audio = self.model.tts_to_file(text, speaker_id=self.speaker_id, speed=self.speed)
        return audio
    
    def tts_file(self, text, output_path):
        self.model.tts_to_file(text, speaker_id=self.speaker_id, output_path=output_path, speed=self.speed)









if __name__ == '__main__':

    tts = TTS(speaker='EN-BR')

    text = '''
        Buzz the bee dreamt of touching the moon, its pale glow reflecting in his tiny eyes.
        Each day, he flew higher, fueled by hope and nectar. One night, a gust of wind carried him above the tallest tree, where he saw the moon mirrored in a still pond below.
        Though he never reached the moon - he realized its beauty could be found everywhere he looked.
    '''

    # Play TTS output
    import sounddevice as sd
    audio = tts.tts_audio(text)
    sd.play(audio, tts.sample_rate)
    sd.wait()

    # Save TTS output
    output_path = 'tts_out.wav'
    tts.tts_file(text, output_path)