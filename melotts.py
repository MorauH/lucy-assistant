from melo.api import TTS

import nltk
nltk.download('averaged_perceptron_tagger_eng')

speed = 1.0

device = 'auto'

text = '''
Buzz the bee dreamt of touching the moon, its pale glow reflecting in his tiny eyes. Each day, he flew higher, fueled by hope and nectar. One night, a gust of wind carried him above the tallest tree, where he saw the moon mirrored in a still pond below. Though he never reached the moon, he realized its beauty could be found everywhere he looked.
'''
model = TTS(language='EN', device=device)
speaker_ids = model.hps.data.spk2id

# american accent
output_path = 'en_us.wav'
model.tts_to_file(text, speaker_id=speaker_ids['EN-US'], output_path=output_path, speed=speed)

# british accent
output_path = 'en_br.wav'
model.tts_to_file(text, speaker_id=speaker_ids['EN-BR'], output_path=output_path, speed=speed)

# australian accent
output_path = 'en_au.wav'
model.tts_to_file(text, speaker_id=speaker_ids['EN-AU'], output_path=output_path, speed=speed)

# default accent
output_path = 'en_default.wav'
model.tts_to_file(text, speaker_id=speaker_ids['EN-Default'], output_path=output_path, speed=speed)