import numpy as np
from transformers import AutoModel, AutoTokenizer
import torch

device = "cuda:0" if torch.cuda.is_available() else "cpu"

model_name = "../lib/DR-BERT"

tokenizer_drbert = AutoTokenizer.from_pretrained(model_name)
model_drbert = AutoModel.from_pretrained(model_name).eval().to(device)


def encode_by_drbert(seq):
    def get_hidden_states(encoded, model):
        with torch.no_grad():
            output = model(**encoded)
        # Get last hidden state
        return output.last_hidden_state

    embedding_dim = 600
    maxsize = 500

    seq = seq.upper()
    encoded = tokenizer_drbert.encode_plus(seq, return_tensors="pt").to(device)
    embedding = get_hidden_states(encoded, model_drbert).detach().cpu().numpy()[0, 1:-1, :embedding_dim]

    return embedding[:maxsize]

"""
seq = 'arck' * 150
tmpDeepDRP = encode_by_drbert(seq)
print(tmpDeepDRP.shape)
"""
seq = 'arck' * 150
tmpDeepDRP = encode_by_drbert(seq)
print(tmpDeepDRP.shape)
