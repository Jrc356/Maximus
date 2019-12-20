import pandas as pd
import bitfinex as bf
import json
from datetime import datetime
import time
import os
import sys
import logging
from logging import handlers
from tqdm import tqdm

# LOGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(format)
logger.addHandler(ch)

fh = handlers.RotatingFileHandler('app.log', maxBytes=(1048576*5), backupCount=7)
fh.setFormatter(format)
logger.addHandler(fh)
# END LOGGING

PATH = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(PATH, 'config.json')) as f:
    CONFIG = json.load(f)


def scale(value, oldMin, oldMax, newMin, newMax):
    return ( (value - oldMin) / (oldMax - oldMin) ) * (newMax - newMin) + newMin


class Collector:
    def __init__(self):
        self.api = bf.bitfinex_v2.api_v2()

    def getPair(self, pair, start, stop, interval):
        data = self.api.candles(symbol=pair,
                                interval=interval,
                                limit=CONFIG["LIMIT"],
                                start=start,
                                end=stop)

        df = pd.DataFrame(data, columns=["TS", "OPEN", "CLOSE", "HIGH", "LOW", "VOLUME"])
        df['TS'] = pd.to_datetime(df['TS'], unit="ms")
        return df

    def saveData(self, df, pair_name, start, end, interval):
        pair_dir = os.path.join(os.path.dirname(PATH), "sets", pair_name)
        if not os.path.exists(pair_dir):
            os.mkdir(pair_dir)

        fname = os.path.join(pair_dir, f"{pair_name}-{interval}-{start}-{end}.ftr")
        logger.debug(f"Saving to {fname}")
        try:
            df.to_feather(fname)
        except Exception as e:
            logger.error("Exception occured: ", e)
            logger.error("Data: ", df.head())
            raise e

    def combine(self, pair_name):
        pair_dir = os.path.join(os.path.dirname(PATH), "sets", pair_name)
        files = os.listdir(pair_dir)
        files = [file for file in files if "COMPLETE" not in file and "parts" not in file]

        if not files:
            return

        parts_dir = os.path.join(pair_dir, "parts")
        if not os.path.exists(parts_dir):
            os.makedirs(parts_dir)

        df = pd.read_feather(os.path.join(pair_dir, files[0]))
        for file in files:
            p = os.path.join(pair_dir, file)
            dat = pd.read_feather(p)
            df = pd.concat([df, dat], axis=0)
            os.rename(p, os.path.join(parts_dir, file))

        df.drop_duplicates(inplace=True)
        df.sort_values("TS", ascending=True, inplace=True)
        df.reset_index(inplace=True)

        df.to_feather(os.path.join(pair_dir, f"{pair_name}-COMPLETE.ftr"))

    def collect(self, pair, start, end, step, interval):
        logger.info(f'Retrieving data for pair {pair}')

        stop = start + step
        
        max_it = end-start
        pbar = tqdm(total=round(scale(end-start, 0, max_it, 0, 100)))
        while start < end:
            logger.debug(f"Collecting data for {pair} from {start} to {stop}")
            data = self.getPair(pair, start, stop, interval)
            self.saveData(data, pair, start, stop, interval)

            logger.debug(f"Increasing time range by {step}")
            start += step
            stop += step

            logger.debug("Waiting 2 seconds")
            time.sleep(2)

            pbar.update(round(scale(step, 0, max_it, 0, 100)))

        pbar.close()

        self.combine(pair)


if __name__ == "__main__":
    pairs = CONFIG["PAIRS"]
    start = int(datetime.timestamp(datetime.strptime(CONFIG['START_DATE'], "%m/%d/%Y"))) * 1000
    end = int(datetime.timestamp(datetime.strptime(CONFIG['END_DATE'], "%m/%d/%Y"))) * 1000
    step = 60000 * CONFIG["LIMIT"] # assumes 1 min interval, change for different intervals
    interval = CONFIG['INTERVAL']
    collector = Collector()

    for pair in pairs:
        collector.collect(pair, start, end, step, interval)