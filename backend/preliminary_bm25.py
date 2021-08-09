import re
import string
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

dataset_path = Path(__file__).resolve().parent.parent / "data" / "steam-store-games"
basic_info = pd.read_csv(dataset_path / "steam.csv")
descriptions = pd.read_csv(dataset_path / "steam_description_data.csv")
dataset = basic_info.set_index("appid").join(descriptions.set_index("steam_appid"))

html_cleaner = re.compile("<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});")
remove_punctuation_table = str.maketrans(dict.fromkeys(string.punctuation))


def tokenize(text):
    text = re.sub(html_cleaner, "", text)
    text = text.translate(remove_punctuation_table)
    text = text.lower()
    return text.split()


corpus = dataset["detailed_description"].values
tokenized_corpus = [tokenize(doc) for doc in corpus]
bm25 = BM25Okapi(tokenized_corpus)

names = dataset["name"].values
cache = {}


def recommend(query_games: List[str], n: int = 25) -> List[str]:
    scores = np.zeros(len(corpus))
    for query_game in query_games:
        games = dataset[dataset["name"] == query_game]
        if len(games) == 0:
            raise ValueError(f"Unknown game name `{query_game}`")
        game_id = games["name"].iloc[0]
        if game_id not in cache:
            query = games["detailed_description"].iloc[0]
            game_scores = bm25.get_scores(tokenize(query))
            cache[game_id] = game_scores
        else:
            game_scores = cache[game_id]
        scores += game_scores
    top_n = np.argsort(scores)[::-1]
    games = []
    for i in top_n:
        if names[i] in query_games:
            continue
        games.append(names[i])
        if len(games) >= n:
            return games
    return games
