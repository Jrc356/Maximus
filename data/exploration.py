import pandas as pd
import matplotlib.pyplot as plt 
import os
import json

DATASETS_PATH = os.path.join(os.path.dirname(__file__), "sets")

with open(os.path.join(os.path.dirname(__file__), "scripts", "config.json")) as f:
    CONFIG = json.load(f)

fig = plt.figure()
ax = fig.add_subplot(111)

for pair in CONFIG["PAIRS"]:
    df = pd.read_feather(os.path.join(DATASETS_PATH, pair, f"{pair}-COMPLETE.ftr"))

    close = df["CLOSE"].pct_change()
    close.fillna(0, inplace=True)

    ax.plot(df["TS"], close, label=pair)

plt.legend(loc=2)
plt.show()