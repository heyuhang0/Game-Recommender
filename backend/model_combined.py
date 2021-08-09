import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from . import preliminary_bm25 as bm25
from . import preliminary_genre as genre
from . import preliminary_vector as vector

WEIGHT_BM25 = 0.5
WEIGHT_GENRE = 0.2
WEIGHT_VECTOR = 0.3


def recommend_by_name(query_games: List[str], n: int = 25) -> List[str]:
    results_by_genre = genre.recommend(query_games, n)
    results_by_bm25 = bm25.recommend(query_games, n)
    results_by_vector = vector.recommend(query_games, n)

    games = defaultdict(float)
    for idx, game_name in enumerate(results_by_genre):
        rank = idx + 1
        games[game_name] += (1 / rank) * WEIGHT_GENRE
    for idx, game_name in enumerate(results_by_bm25):
        rank = idx + 1
        games[game_name] += (1 / rank) * WEIGHT_BM25
    for idx, game_name in enumerate(results_by_vector):
        rank = idx + 1
        games[game_name] += (1 / rank) * WEIGHT_VECTOR

    ordered_results = list(games.items())
    ordered_results.sort(key=lambda x: x[1], reverse=True)

    return [game for game, _ in ordered_results][:n]


def _load_name_app_id_mapping():
    dataset_path = Path(__file__).resolve().parent.parent / "data" / "steam-store-games"
    app_id_to_name: Dict[int, str] = {}
    with open(dataset_path / "steam.csv", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        next(reader, None)  # skip header
        for row in reader:
            app_id, name = row[:2]
            app_id_to_name[int(app_id)] = name

    name_to_app_id = {v: k for k, v in app_id_to_name.items()}
    return app_id_to_name, name_to_app_id


app_id_to_name, name_to_app_id = _load_name_app_id_mapping()


def recommend(steam_app_ids: List[int], n: int = 25) -> List[int]:
    game_names = [app_id_to_name[i] for i in steam_app_ids]
    results = recommend_by_name(game_names, n*2)
    return [name_to_app_id[r] for r in results if r in name_to_app_id][:n]
