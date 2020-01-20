# Maximus
An attempt at a NEAT Crypto Currency Trading Bot. This bot utilizes (neat-python)[https://github.com/CodeReclaimers/neat-python] to create a nueral network to trade crypto currencies in a given amount of time.

## Status
This bot is currently useless and the config untuned. To improve upon the bot, play with the parameters in `bot/config`. The best I've gotten so far was about 2% in a couple days time.

## Installation
First, create a virtual env of your choice and run `pip install -r requirements.txt` to install dependencies. 

Then, collect the needed data by going into the `data` folder. Then run `collect_data.py` to collect the data needed. The script relies on the open bitfinex api's so a key should not be needed. This will try to collect all of the data laid out in `config.json` (in the top most directory).

Next, edit and run `clean_data.py` to clean up the data and add derivitives such as moving averages and RSI.

Finally, Run the bot using `python3 bot/model.py`
