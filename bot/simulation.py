import pandas as pd
from os.path import join, dirname, abspath
import json

DATAFOLDER_PATH = dirname(dirname(abspath(__file__)))
DATASETS_PATH = join(DATAFOLDER_PATH, "data", "sets")

with open(join(dirname(dirname(abspath(__file__))), 'config.json')) as f:
    CONFIG = json.load(f)


class MarketSim(object):
    __PENALTY = 0.001

    def __init__(self, sim_length_in_minutes, starting_point, starting_balance=1000, pair="BTCUSD"):
        self.sim_length = sim_length_in_minutes
        self.balance = starting_balance  # in dollars
        self.starting_balance = starting_balance
        self.pair = pair
        self.pair_file = join(DATASETS_PATH, pair, f"{pair}-COMPLETE.ftr")
        self.holding = 0.00  # total coin held

        self.__counter = 0
        self.__buy_counter = 0
        self.__penalty_mult = 1
        self.__penalty_time = int(self.sim_length * 0.05)

        max_idx = len(pd.read_feather(self.pair_file)) - self.sim_length
        self.__ts_index = int(starting_point * max_idx)
        self.__end_ts_index = self.__ts_index + self.sim_length
        self.__timestamp = self.__getTimeStamp()
        self.done = False

        df = pd.read_feather(self.pair_file)
        self.__max_timestamp = pd.read_feather(self.pair_file).iloc[len(df) - 1, 0]
        self.__sim_end_timestamp = pd.read_feather(self.pair_file).iloc[self.__end_ts_index, 0]

        # print(f"STARTING SIMULATION FROM {self.__timestamp} to {self.__sim_end_timestamp}")

    def __getTimeStamp(self):
        return pd.read_feather(self.pair_file).iloc[self.__ts_index, 0]

    def buy(self, pct_balance):
        pct_balance = round(pct_balance, 2)
        if self.balance == 0 or pct_balance < 0.5:
            return

        if pct_balance > 1:
            pct_balance = 1

        spend_amt = pct_balance * self.balance
        cost = pd.read_feather(self.pair_file).iloc[self.__ts_index, ].CLOSE

        purchase_amt = spend_amt/cost
        purchase_amt = round(purchase_amt, 8) # round to satoshis
        # print(f"BOUGHT {pct_balance * 100:.2f}% OF BALANCE ${self.balance:.2f} OR {purchase_amt} {self.pair} FOR {spend_amt:.2f} ON {self.__timestamp}!")
        self.holding += purchase_amt
        self.balance -= spend_amt

        self.__buy_counter += 1

    def sell(self, pct_holding):
        if self.holding == 0 or pct_holding < 0.5:
            return

        if pct_holding > 1:
            pct_holding = 1

        sell_amt = pct_holding * self.holding
        cost = pd.read_feather(self.pair_file).iloc[self.__ts_index, ].CLOSE

        earnings = sell_amt * cost
        # print(f"SELLING {pct_holding * 100:.2f}% OF HOLDING {self.holding:.2f} OR {sell_amt} {self.pair} FOR ${earnings:.2f} ON {self.__timestamp}!")
        self.holding -= sell_amt
        self.balance += earnings

    def step(self, trade):
        self.__counter += 1
        self.__ts_index += 1
        self.__timestamp = self.__getTimeStamp()

        if trade[0] == "SELL":
            self.sell(trade[1])
        elif trade[0] == "BUY":
            self.buy(trade[1])
        else:
            pass

        if self.__timestamp == self.__max_timestamp or self.__ts_index >= self.__end_ts_index:
            self.done = True

    def getState(self):
        dat = []

        df = pd.read_feather(self.pair_file)
        df = df.iloc[self.__ts_index - 10:self.__ts_index]

        values = df.drop("TS", axis=1).values.tolist()
        for v in values:
            dat.extend(v)

        # for pair in getPairFiles():
        #     df = pd.read_feather(pair)
        #     df = df[df.TS == self.__timestamp]

        #     values = df.drop("TS", axis=1).values.tolist()
        #     if len(values) == 0:
        #         values = [[0 for _ in range(len(df.columns) - 1)]]  # without ts

        #     dat.extend(values[0])

        dat.extend([self.holding, self.balance])

        return dat

    def getHoldingsValue(self):
        cost = pd.read_feather(self.pair_file).iloc[self.__ts_index, ].CLOSE
        return self.holding * cost

    def getFitness(self):
        fitness = ((self.balance + self.getHoldingsValue()) - self.starting_balance) / self.starting_balance
        if self.__counter > self.__penalty_time and self.__buy_counter < 1:
            #print(f"Genome has not bought anything in {self.__penalty_time} steps. Applying penalty.")
            fitness -= (self.__PENALTY * self.__penalty_mult)
            self.__penalty_mult += 1
        return fitness


def getTrade(action):
    # print(action)
    if action[0] < 0.33:
        return ("SELL", action[1])
    elif action[0] >= 0.33 and action[0] < 0.66:
        return ("HOLD", action[1])
    elif action[0] >= 0.66:
        return ("BUY", action[1])
