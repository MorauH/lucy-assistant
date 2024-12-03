
# load ASR model
from transformers import Wav2Vec2ForCTC, AutoProcessor
import torch

model_id = "facebook/mms-300m"

processor = AutoProcessor.from_pretrained(model_id)
model = Wav2Vec2ForCTC.from_pretrained(model_id)


