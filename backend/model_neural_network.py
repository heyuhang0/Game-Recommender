from pathlib import Path
from typing import List

import numpy as np
import torch
import torch.nn as nn

UNK_GAME = "<unk>"
UNK_ID = 0


class CBOG(nn.Module):
    def __init__(self, num_games: int, embedding_size: int):
        super().__init__()
        self.embeddings = nn.Embedding(num_games, embedding_size, padding_idx=UNK_ID)
        self.linear = nn.Linear(embedding_size, num_games)

    def forward(self, inputs):
        embeds = self.embeddings(inputs)
        embeds_sum = embeds.sum(dim=1)
        out = self.linear(embeds_sum)
        return out


saved = torch.load(Path(__file__).resolve().parent / "model_neural_network.pth")
model = CBOG(saved["num_games"], saved["embedding_size"])
model.load_state_dict(saved["weights"])

steam_app_id_to_index = saved["steam_app_id_to_index"]
index_to_steam_app_id = {v: k for k, v in steam_app_id_to_index.items()}


def recommend(steam_app_ids: List[int], n: int = 20) -> List[int]:
    query_ids = [steam_app_id_to_index.get(i, UNK_ID) for i in steam_app_ids]
    model.eval()
    with torch.no_grad():
        scores = model(torch.LongTensor([query_ids])).detach().cpu()[0].numpy()
    sorted_indexes = np.argsort(scores)[::-1]
    recommended = [
        index_to_steam_app_id[i]
        for i in sorted_indexes
        if i in index_to_steam_app_id and i not in query_ids
    ][:n]
    return recommended
