from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load Data
dataset_path = Path(__file__).resolve().parent.parent / "data" / "steam-store-games"
steam_df = pd.read_csv(dataset_path / "steam.csv")

# rename column from appid to steam_appid for joining and consistency with the other data sets
steam_df = steam_df.rename(columns={"appid": "steam_appid"})

# Load another dataset
steam_description_df = pd.read_csv(dataset_path / "steam_description_data.csv")

# Join relevant & useful datasets together on steam_appid column
# steam_df, steam_description_data_df, steam_requirements_df(not sure whether to include), steam_spytag_df
steam_and_description_df = steam_df.merge(steam_description_df, on="steam_appid")

# add game id column
steam_and_description_df["game_id"] = steam_and_description_df.index


def build_token_counts():
    # function to get important features
    def get_important_features(data):
        important_features = []
        for i in range(0, data.shape[0]):
            important_features.append(
                data["name"][i]
                + " "
                + data["developer"][i]
                + " "
                + data["publisher"][i]
                + " "
                + data["categories"][i]
                + " "
                + data["genres"][i]
                + " "
                + data["steamspy_tags"][i]
                + " "
                + data["detailed_description"][i]
                + " "
                + data["about_the_game"][i]
                + " "
                + data["short_description"][i]
            )
        return important_features

    # create a column called important_features in the dataframe to hold the combined strings
    steam_and_description_df["important_features"] = get_important_features(steam_and_description_df)
    # convert the text to a matrix of token counts
    cm = CountVectorizer().fit_transform(steam_and_description_df["important_features"])
    return cm


cm = build_token_counts()
games_names = steam_and_description_df.name.values


# final game recommendation function
def recommend(games, n=25):
    scores_sum = None
    for game in games:
        steam_app_id = steam_and_description_df[steam_and_description_df.name == game]["game_id"].values[0]
        score = cosine_similarity(cm, cm[steam_app_id])
        if scores_sum is None:
            scores_sum = score
        else:
            scores_sum += score

    # Create a list of enumerations for the similarity score
    scores = list(enumerate(scores_sum))

    # sort the list
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)

    results = []
    for item in sorted_scores:
        game_name = games_names[item[0]]
        if game_name in games:
            continue
        results.append(game_name)
        if len(results) >= n:
            return results
    return results
