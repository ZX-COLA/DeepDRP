import re
import torch
import numpy as np

from transformers import T5Tokenizer, T5Model

tokenizer_t5 = T5Tokenizer.from_pretrained('Rostlab/prot_t5_xl_uniref50', do_lower_case=False)
model_t5 = T5Model.from_pretrained("Rostlab/prot_t5_xl_uniref50")


def encode_by_t5(seq):
    sequences_Example = [" ".join(list(seq.upper()))]
    sequences_Example = [re.sub(r"[UZOB]", "X", sequence) for sequence in sequences_Example]
    ids = tokenizer_t5.batch_encode_plus(sequences_Example,
                                         add_special_tokens=True,
                                         padding=False)

    input_ids = torch.tensor(ids['input_ids'])
    attention_mask = torch.tensor(ids['attention_mask'])

    with torch.no_grad():
        embedding = model_t5(input_ids=input_ids,
                             attention_mask=attention_mask,
                             decoder_input_ids=input_ids,
                             )

    maxsize = 500
    embedding_size = 600

    encoder_embedding = embedding.last_hidden_state[0,:-1].detach().cpu().numpy()
    return encoder_embedding[:maxsize, :embedding_size]


"""
seq = "ARC"*200
x = encode_by_t5(seq)
print(x.shape)
"""

seq = "ARC"*200
x = encode_by_t5(seq)
print(x.shape)