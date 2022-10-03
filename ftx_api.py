import pandas as pd
import time
from datetime import datetime

import broker_ftx

def fetch_df_balance():
    my_broker = broker_ftx.BrokerFTX()
    result, balance = my_broker.get_balance()
    df_account_usd_value = pd.DataFrame(result)

    cash = my_broker.get_cash()
    portfolio = my_broker.get_portfolio_value()

    return df_account_usd_value, cash, portfolio

def fetch_df_mytrades():
    dt = datetime(2022, 1, 1) # starting date
    milliseconds = int(round(dt.timestamp() * 1000))

    my_broker = broker_ftx.BrokerFTX()
    result = my_broker.get_mytrades(milliseconds)
    # result = my_broker.fetch_my_trades(symbol=None, since=milliseconds, limit=200, params={})
    return result

def fetch_df_positions():
    my_broker = broker_ftx.BrokerFTX()
    result = my_broker.get_positions()
    return result

