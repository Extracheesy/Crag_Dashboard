'''
- intégrer fud / ftx / spot_ftx
- externaliser la stratégie (d'achat et de vente)
'''

# from . import broker
import ccxt
import pandas as pd
from dotenv import load_dotenv
import os

# class BrokerFTX(broker.Broker):
class BrokerFTX():
    def __init__(self, params = None):
        # super().__init__(params)

        account = "Main Account"
        if params:
            account = params.get("account", account)
        self.authentificated = self.authentification(account)
         
    def authentification(self, account):
        authentificated = False
        load_dotenv()
        ftx_api_key = os.getenv("FTX_API_KEY")
        ftx_api_secret = os.getenv("FTX_API_SECRET")
        self.ftx_exchange = ccxt.ftx({
            # 'headers': {
            #    'FTX-SUBACCOUNT': account,
            # },
            'apiKey': ftx_api_key,
            'secret': ftx_api_secret
            })
        # check authentification
        try:
            authentificated = self.ftx_exchange.check_required_credentials()
        except ccxt.AuthenticationError as err:
            print("[BrokerFTX] AuthenticationError : ", err)
        return authentificated

    def authentication_required(fn):
        """decoration for methods that require authentification"""
        def wrapped(self, *args, **kwargs):
            if not self.authentificated:
                print("You must be authenticated to use this method {}".format(fn))
                return None
            else:
                return fn(self, *args, **kwargs)
        return wrapped

    @authentication_required
    def get_mytrades(self, timestamp):
        mytrades = self.ftx_exchange.fetch_my_trades(since=timestamp)

        df_trades = pd.DataFrame(mytrades)

        return df_trades


    @authentication_required
    def get_cash(self):
        # get free USD
        result = 0
        if self.ftx_exchange:
            try:
                balance = self.ftx_exchange.fetch_balance()
                if 'USD' in balance:
                    result = float(balance['USD']['free'])
            except BaseException as err:
                print("[BrokerFTX::get_balance] An error occured : {}".format(err))
        return result

    @authentication_required
    def get_balance(self):
        result = {}
        if self.ftx_exchange:
            balance = self.ftx_exchange.fetch_balance()
            try:
                balance = self.ftx_exchange.fetch_balance()
                result = {coin['coin']:{"availableForWithdrawal":float(coin['total']), "usdValue":float(coin["usdValue"])} for coin in balance["info"]["result"] if coin['total'] != "0.0"}
            except BaseException as err:
                print("[BrokerFTX::get_balance] An error occured : {}".format(err))
        return result, balance

    @authentication_required
    def get_portfolio_value(self):
        result, balance = self.get_balance()
        df_account = pd.DataFrame(result)
        portfolio_value = 0
        df_account.drop(['USD'], axis=1, inplace=True)
        for coin in df_account.columns.tolist():
            portfolio_value += df_account[coin]["usdValue"]
            #print("{}: {}".format(coin, balance[coin]["usdValue"]))

        return portfolio_value

    @authentication_required
    def get_positions(self):
        result = []
        if self.ftx_exchange:
            try:
                result = self.ftx_exchange.fetch_positions()
                df_result = pd.DataFrame(result)
            except BaseException as err:
                print("[BrokerFTX::get_positions] An error occured : {}".format(err))
        return df_result
       
    @authentication_required
    def get_commission(self, symbol):
        # https://docs.ftx.com/#execution-report-8
        return 0.0067307233

    def _format_row(self, current_trade):
        datetime = current_trade['datetime']
        symbol = current_trade['symbol']
        side = current_trade['side']
        price = current_trade['price']
        amount = current_trade['amount']
        cost = current_trade['cost']
        fee_cost = current_trade['fee']['cost']
        fee_rate = current_trade['fee']['rate']
        return "{},{},{},{},{},{},{},{}".format(datetime,symbol,side,price,amount,cost,fee_cost,fee_rate)

