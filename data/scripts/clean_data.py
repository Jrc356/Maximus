import pandas as pd
import json
from os.path import dirname, join, abspath
from tqdm import tqdm

DATAFOLDER_PATH = dirname(dirname(abspath(__file__)))

DATASETS_PATH = join(DATAFOLDER_PATH, "sets")

with open(join(dirname(abspath(__file__)), 'config.json')) as f:
    CONFIG = json.load(f)


def getPairFiles():
    for pair in tqdm(CONFIG["PAIRS"]):
        pair_file = join(DATASETS_PATH, pair, f"{pair}-COMPLETE.ftr")
        yield pair_file


def load(fileName):
    """
        @returns pd.DataFrame
    """
    return pd.read_feather(fileName)


def save(df, fileName):
    df.to_feather(fileName)


def addPctChange(col):
    print(f"Adding percent change for column {col}")
    for pair_file in getPairFiles():
        df = load(pair_file)

        pct = df[col].pct_change()
        pct.fillna(0, inplace=True)

        df[f"{col}_PCT"] = pct

        save(df, pair_file)


def addMovingAverage(col, win):
    print(f"Adding {win} moving averages for column {col}")
    for pair_file in getPairFiles():
        df = load(pair_file)

        ma = df[col].rolling(win, win_type="triang").mean()
        ma.fillna(0, inplace=True)

        df[f"{col}_{win}MA"] = ma

        save(df, pair_file)


def addRSI(win=14):
    print("Adding rsi")
    for pair_file in getPairFiles():
        df = load(pair_file)
        delta = df.CLOSE.diff(1)

        gain = delta.mask(delta < 0, 0)
        loss = delta.mask(delta > 0, 0)

        avg_gain = gain.ewm(com=win-1, min_periods=win).mean()
        avg_loss = loss.ewm(com=win-1, min_periods=win).mean()

        rs = abs(avg_gain / avg_loss)
        rsi = 100 - (100/(1+rs))
        rsi.fillna(0, inplace=True)
        df["RSI"] = rsi

        save(df, pair_file)


def addStdDev(col, win):
    print(f"Adding {win} standard deviations for column {col}")
    for pair_file in getPairFiles():
        df = load(pair_file)

        sd = df[col].rolling(win).std()
        sd.fillna(0, inplace=True)

        df[f"{col}_{win}STD"] = sd

        save(df, pair_file)


def cleanIndexes():
    print(f"Cleaning up indexes")
    for pair_file in getPairFiles():
        df = load(pair_file)
        df = df.drop("index", 1)
        save(df, pair_file)


# For every pair
addRSI()

# Every column per pair
cols = ["OPEN", "CLOSE", "HIGH", "LOW", "VOLUME"]
for col in cols:
    addPctChange(col)

    addMovingAverage(col, 10)
    addMovingAverage(col, 50)
    addMovingAverage(col, 200)

    addStdDev(col, 10)
    addStdDev(col, 50)
    addStdDev(col, 200)

cleanIndexes()
