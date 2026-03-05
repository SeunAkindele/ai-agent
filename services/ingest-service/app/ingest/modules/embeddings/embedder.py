# embedding.py
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List

class EmbeddingModel:
    def __init__(self, model_name: str = "bert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def embed(self, text: str) -> List[float]:
        """Embed the text into a vector using a pre-trained model."""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).detach().numpy().flatten().tolist()  # Mean of token embeddings