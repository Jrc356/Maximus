import pandas as pd
from os.path import join, dirname, abspath
import json

DATAFOLDER_PATH = dirname(dirname(abspath(__file__)))
DATASETS_PATH = join(DATAFOLDER_PATH, "data", "sets")

with open(join(dirname(dirname(abspath(__file__))), 'config.json')) as f:
    CONFIG = json.load(f)


def getPairFiles():
    for pair in CONFIG["PAIRS"]:
        pair_file = join(DATASETS_PATH, pair, f"{pair}-COMPLETE.ftr")
        yield pair_file


class MarketSim(object):
    def __init__(self, sim_length_in_minutes):
        self.sim_length = sim_length_in_minutes
        self.balance = 1000.00  # in dollars
        self.holding = 0.00  # total coin held
        self.__ts_index = 0
        self.__timestamp = self.__getTimeStamp()
        self.done = False

        first_pair = next(getPairFiles())
        df = pd.read_feather(first_pair)
        self.__end_timestamp = pd.read_feather(first_pair).iloc[len(df) - 1, 0]

    def __getTimeStamp(self):
        return pd.read_feather(next(getPairFiles())).iloc[self.__ts_index, 0]

    def buy(self, pct_balance):
        spend_amt = pct_balance * self.balance
        cost = next(getPairFiles()).iloc[self.__ts_index, ].CLOSE
        
        purchase_amt = spend_amt/cost
        self.holding += purchase_amt
        self.balance -= spend_amt

    def sell(self, pct_holding):
        sell_amt = pct_holding * self.holding
        cost = pd.read_feather(next(getPairFiles())).iloc[self.__ts_index, ].CLOSE

        earnings = sell_amt * cost
        self.holding -= sell_amt
        self.balance += earnings

    def step(self, trade):
        self.__ts_index += 1
        self.__timestamp = self.__getTimeStamp()

        if trade[0] == "SELL":
            # print(f"selling {trade[1]}% of holdings")
            self.sell(trade[1])
        elif trade[0] == "BUY":
            # print(f"buying {trade[1]}% worth of balance")
            self.buy(trade[1])
        else:
            # print("Holding")
            pass

        if self.__timestamp == self.__end_timestamp or self.__ts_index >= self.sim_length:
            self.done = True

    def getState(self):
        dat = []
        for pair in getPairFiles():
            df = pd.read_feather(pair)
            df = df[df.TS == self.__timestamp]

            values = df.drop("TS", axis=1).values.tolist()
            if len(values) == 0:
                values = [[0 for _ in range(len(df.columns) - 1)]]  # without ts
            
            dat.extend(values[0])
        
        dat.extend([self.holding, self.balance])

        return dat


def getTrade(action):
    if action[0] < 0.33:
        return ("SELL", action[1])
    elif action[0] >= 0.33 and action[0] < 0.66:
        return ("HOLD", action[1])
    elif action[0] >= 0.66:
        return ("BUY", action[1])
