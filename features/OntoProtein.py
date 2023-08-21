import numpy as np
from transformers import AutoTokenizer, AutoModelForMaskedLM, FeatureExtractionPipeline

tokenizer_onto = AutoTokenizer.from_pretrained("zjukg/OntoProtein")
model_onto = AutoModelForMaskedLM.from_pretrained("zjukg/OntoProtein")
bert_model_onto = FeatureExtractionPipeline(model=model_onto, tokenizer=tokenizer_onto)


def encode_by_onto(seq):
    maxsize = 500
    seq = " ".join(list(seq))
    res = bert_model_onto(seq)[0][1:-1]
    return np.squeeze(res)[:maxsize]


"""
seq = "ARCYCS" * 100
x = encode_by_onto(seq)
print(x.shape)
"""


