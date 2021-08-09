import random
from typing import List


class RandomRecommender:
    def __init__(self, choices: List[int]) -> None:
        self.choices = choices

    def __call__(self, steam_app_ids: List[int], n: int = 20) -> List[int]:
        return random.sample(self.choices, k=n)
