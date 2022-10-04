import numpy as np
import pandas as pd
import os
import config
import utils

default_features = ["open", "close", "high", "low", "volume"]

class DataDescription():
    def __init__(self, lst_crypto=config.LST_CRYPTO):
        # self.symbols = default_symbols
        self.symbols = lst_crypto
        # self.features = default_features
        self.features = config.DATA_COLUMNS
        self.lst_data = []


def get_current_data(data_description):
    symbols = ','.join(data_description.symbols)
    symbols = symbols.replace('/', '_')
    params = {"service": "history", "exchange": "ftx", "symbol": symbols, "start": "2019-01-01", "interval": "1h"}
    response_json = utils.fdp_request(params)

    data = {feature: [] for feature in data_description.features}
    data["symbol"] = []

    if response_json["status"] == "ok":
        for symbol in data_description.symbols:
            formatted_symbol = symbol.replace('/', '_')
            df = pd.read_json(response_json["result"][formatted_symbol]["info"])
            # df = features.add_features(df, data_description.features)
            columns = list(df.columns)

            data["symbol"].append(symbol)
            for feature in data_description.features:
                if feature not in columns:
                    return None
                data[feature].append(df[feature].iloc[-1])

    df_result = pd.DataFrame(data)
    df_result.set_index("symbol", inplace=True)
    return df_result


def record(data_description, target="./data/", start_date="2022-06-01", interval="1h"):
    symbols = ','.join(data_description.symbols)
    symbols = symbols.replace('/','_')
    params = { "service":"history", "exchange":"ftx", "symbol":symbols, "start":start_date, "interval": interval }
    response_json = utils.fdp_request(params)
    lst_df_data = []
    for symbol in data_description.symbols:
        formatted_symbol = symbol.replace('/','_')
        if response_json["result"][formatted_symbol]["status"] == "ko":
            print("no data for ",symbol)
            continue
        df = pd.read_json(response_json["result"][formatted_symbol]["info"])
        # df = features.add_features(df, data_description.features)
        if not os.path.exists(target):
            os.makedirs(target)
        # df.to_csv(target+'/'+formatted_symbol+".csv")
        lst_df_data.append(df)
    return lst_df_data

def lst_to_df(lst_data, ds):
    lst_data_clean = []
    for df in lst_data:
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)
        df['index'] = pd.to_datetime(df['index'], unit='ms')
        df.rename({'index': 'date'}, axis=1, inplace=True)
        lst_data_clean.append(df)

    ds.lst_data = lst_data_clean
    return ds

def process_trades(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['symbol'] = df['symbol'].str.split(':').str[0]
    df.drop(['info'], axis=1, inplace=True)
    df.drop(['id'], axis=1, inplace=True)
    df.drop(['order'], axis=1, inplace=True)
    df.drop(['type'], axis=1, inplace=True)
    df.drop(['datetime'], axis=1, inplace=True)
    # df.drop(['timestamp'], axis=1, inplace=True)
    df.rename({'timestamp': 'timestamp'}, axis=1, inplace=True)

    df['fee_cost'] = df['fee'].apply(lambda x: x.get('cost'))
    df['fee_rate'] = df['fee'].apply(lambda x: x.get('rate'))
    df.drop(['fee'], axis=1, inplace=True)
    df.drop(['fees'], axis=1, inplace=True)

    return df

def process_positions(df):

    df_positions = pd.DataFrame()

    df_positions['future'] = df['info'].apply(lambda x: x.get('future'))
    df_positions['datetime'] = df['datetime']
    df_positions['side'] = df['side']
    df_positions['size'] = df['info'].apply(lambda x: x.get('size'))
    df_positions['symbol'] = df['symbol']
    df_positions['entryPrice'] = df['entryPrice']
    df_positions['initialMargin'] = df['initialMargin']
    df_positions['initialMarginPercentage'] = df['initialMarginPercentage']
    df_positions['maintenanceMargin'] = df['maintenanceMargin']
    df_positions['leverage'] = df['leverage']
    df_positions['percentage'] = df['percentage']
    df_positions['unrealizedPnl'] = df['info'].apply(lambda x: x.get('unrealizedPnl'))
    df_positions['realizedPnl'] = df['info'].apply(lambda x: x.get('realizedPnl'))
    df_positions['liquidationPrice'] = df['liquidationPrice']
    df_positions['markPrice'] = df['markPrice']

    df_positions['netSize'] = df['info'].apply(lambda x: x.get('netSize'))
    df_positions['longOrderSize'] = df['info'].apply(lambda x: x.get('longOrderSize'))
    df_positions['shortOrderSize'] = df['info'].apply(lambda x: x.get('shortOrderSize'))
    df_positions['cost'] = df['info'].apply(lambda x: x.get('cost'))
    df_positions['entryPrice'] = df['info'].apply(lambda x: x.get('entryPrice'))

    df_positions['estimatedLiquidationPrice'] = df['info'].apply(lambda x: x.get('estimatedLiquidationPrice'))
    df_positions['openSize'] = df['info'].apply(lambda x: x.get('openSize'))

    return df_positions

def get_df_buy_and_sell(df):
    df_buy_n_sell = pd.DataFrame()

    df_buy_n_sell['timestamp'] = df['timestamp']
    df_buy_n_sell['symbol'] = df['symbol']
    df_buy_n_sell['side'] = df['side']
    df_buy_n_sell['cost'] = df['cost']
    df_buy_n_sell['price'] = df['price']
    df_buy_n_sell['amount'] = df['amount']
    df_buy_n_sell['fee_cost'] = df['fee_cost']

    df_buy_n_sell['buy'] = df['cost']
    df_buy_n_sell['sell'] = df['cost']
    df_buy_n_sell['buy_size'] = df['amount']
    df_buy_n_sell['sell_size'] = df['amount']

    df_buy_n_sell.loc[(df_buy_n_sell.side == 'buy'), 'sell'] = 0
    df_buy_n_sell.loc[(df_buy_n_sell.side == 'sell'), 'buy'] = 0
    df_buy_n_sell['buy'] = df_buy_n_sell['buy'] * (-1)
    df_buy_n_sell['buy_sell'] = 0
    df_buy_n_sell['buy_sell'] = np.where((df_buy_n_sell['buy'] != 0), df_buy_n_sell['buy'], df_buy_n_sell['buy_sell'])
    df_buy_n_sell['buy_sell'] = np.where((df_buy_n_sell['sell'] != 0), df_buy_n_sell['sell'], df_buy_n_sell['buy_sell'])

    df_buy_n_sell.loc[(df_buy_n_sell.side == 'buy'), 'sell_size'] = 0
    df_buy_n_sell.loc[(df_buy_n_sell.side == 'sell'), 'buy_size'] = 0
    df_buy_n_sell['buy_size'] = df_buy_n_sell['buy_size'] * (-1)

    return df_buy_n_sell