import whisper

model = whisper.load_model('base')
result = model.transcribe('en_br.wav')

print(result['text'])