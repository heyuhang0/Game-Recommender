import csv
import json
import random
from pathlib import Path
from typing import Dict, List, NamedTuple, Union

from fastapi import FastAPI
from pydantic import BaseModel, validator
from typing_extensions import Literal

from .model_combined import recommend as combined_recommender
from .model_neural_network import recommend as neural_recommender
from .model_random import RandomRecommender

app = FastAPI()
base_path = Path(__file__).resolve().parent


class SteamGame(NamedTuple):
    app_id: int
    name: str
    description: str
    name_lower: str
    description_lower: str

    def to_json(self):
        return {
            "appID": self.app_id,
            "name": self.name,
            "description": self.description,
        }


def load_games() -> Dict[int, SteamGame]:
    steam_ds_path = base_path.parent / "data" / "steam-store-games"

    game_names: Dict[int, str] = {}
    with open(steam_ds_path / "steam.csv", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        next(reader, None)  # skip header
        for row in reader:
            app_id, name = row[:2]
            game_names[int(app_id)] = name

    game_descriptions: Dict[int, str] = {}
    with open(steam_ds_path / "steam_description_data.csv", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        next(reader, None)  # skip header
        for row in reader:
            app_id = row[0]
            description = row[3]
            game_descriptions[int(app_id)] = description

    games: Dict[int, SteamGame] = {}
    for app_id, name in game_names.items():
        description = game_descriptions[app_id]
        games[app_id] = SteamGame(
            app_id, name, description, name.lower(), description.lower()
        )

    return games


games = load_games()


@app.get("/api/games")
async def search_game(q: str, limit: int = 10):
    q = q.lower()
    retrieved: List[SteamGame] = []
    for game in games.values():
        if q in game.name_lower:
            retrieved.append(game)
            if len(retrieved) >= limit:
                break
    else:
        for game in games.values():
            if q in game.description_lower:
                if game in retrieved:
                    continue
                retrieved.append(game)
                if len(retrieved) >= limit:
                    break

    return {"results": [g.to_json() for g in retrieved]}


class RecommendRequest(BaseModel):
    games: List[int]
    limit: int = 30

    @validator("games")
    def games_must_exist(cls, values: List[str]):
        for app_id in values:
            if app_id not in games:
                raise ValueError(f"game {app_id} not found")
        return values


ENGINES = {
    "combined": combined_recommender,
    "neural": neural_recommender,
    "random": RandomRecommender([g.app_id for g in games.values()]),
}

ENGINES_WEIGHTS = {
    "combined": 0.4,
    "neural": 0.4,
    "random": 0.2,
}


@app.post("/api/recommend")
async def recommend_games(request: RecommendRequest):
    engine_name = random.choices(
        list(ENGINES_WEIGHTS.keys()), weights=list(ENGINES_WEIGHTS.values()), k=1
    )[0]
    engine = ENGINES[engine_name]
    recommended = engine(request.games, request.limit)
    with open("records.txt", "a", encoding="utf-8") as fp:
        record = {
            "engine": engine_name,
            "queries": request.games,
            "action": "recommend",
        }
        fp.write(json.dumps(record))
        fp.write("\n")
    return {
        "engine": engine_name,
        "queries": [games[app_id].to_json() for app_id in request.games],
        "results": [games[app_id].to_json() for app_id in recommended],
    }


class Action(BaseModel):
    engine: str
    queries: List[int]
    game: int
    action: Union[Literal["click"], Literal["rate"]]
    score: int

    @validator("queries")
    def queries_must_exist(cls, queries: List[str]):
        for app_id in queries:
            if app_id not in games:
                raise ValueError(f"game {app_id} not found")
        return queries

    @validator("game")
    def game_must_exist(cls, game: str):
        if game not in games:
            raise ValueError(f"game {game} not found")
        return game


@app.post("/api/record")
async def record_action(action: Action):
    with open("records.txt", "a", encoding="utf-8") as fp:
        fp.write(action.json())
        fp.write("\n")
    return {}
