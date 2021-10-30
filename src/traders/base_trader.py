from typing import List, Sequence, Union
import pandas as pd
import sqlalchemy
from binance.client import AsyncClient
from binance import BinanceSocketManager
from enum import Enum
from time import sleep
import datetime as dt
from order import Order


class LookBackEnum(Enum):
    ROWS = 1
    TIMESTAMP = 2

class BaseTrader():
    def __init__(self,api_key,secret_key,symbol:str='BTCUSDT',pause_seconds:float=1,initial_balance=250):
        '''apy_key: apy_key of Binance client
            secret_key: secret_key of Binance client
            symbol: [str] symbol of crypto (default 'BTCUSDT')
            pause_seconds: [float] pause between readings (default 0.5)
            initial_balance: [float] initial investment (default 250)'''
        self.symbol = symbol
        self.client = AsyncClient(api_key,secret_key)
        self.bsm = BinanceSocketManager(self.client)
        self.engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
        self.store_engine = sqlalchemy.create_engine('sqlite:///data/{}_order_stream.db'.format(symbol))
        self.pause_seconds = pause_seconds

        self.order = None
        self.total_qty = 0
        self.balance = initial_balance
        self.acquired_crypto = []
        self.profit = 0
            
    def pause(self):
        sleep(self.pause_seconds)

    def trade(self, entry_level, lookback, qty, min_profit, max_loss):
        raise NotImplementedError


    def get_transaction_profit(self,buy_order:Order,sell_order:Order):
        return sell_order.value()*buy_order.value()


    def store_order(self,order:Order):
        df = pd.DataFrame([order])
        df.price = df.price.astype(float)
        df.qty = df.qty.astype(float)
        #df.transactTime = pd.to_datetime(df.transactTime,unit='ms')
        df.to_sql(self.symbol,self.store_engine,if_exists='append',index=False)


    def buy(self,qty:float)->Order:
        try:
            # get order
            # get last rows
            last_row = self.get_lookback(LookBackEnum.ROWS, rows=1)
            actual_price = last_row.iloc[0]['price']
            actual_time = last_row.iloc[0]['time']
            order = Order(actual_time,actual_price,qty,'BUY')
            #order = self.client.create_order(symbol='BTCUSDT',side='BUY',type='MARKET',quantity=qty)

            # save order in database
            self.store_order(order)

            # update main values
            self.balance -= order.price*order.qty
            self.total_qty += qty
            self.acquired_crypto.append(order)

            return order
        except Exception as e:
            print(e)
            return None


    def simulate_sell(self,qty:float)->List[Order,Order]:
        try:
            # get order
            # get last rows
            last_row = self.get_lookback(LookBackEnum.ROWS, rows=1)
            actual_price = last_row.iloc[0]['price']
            actual_time = last_row.iloc[0]['time']
            sell_order = Order(actual_time,actual_price,qty,'SELL')

            buy_order = self.acquired_crypto[0]

            return sell_order,buy_order
        except Exception as e:
            print(e)
            return None


    def sell(self,qty:float)->List[Order,Order]:
        try:
            # get order
            # get last rows
            last_row = self.get_lookback(LookBackEnum.ROWS, rows=1)
            actual_price = last_row.iloc[0]['price']
            actual_time = last_row.iloc[0]['time']
            sell_order = Order(actual_time,actual_price,qty,'SELL')
            #order = self.client.create_order(symbol='BTCUSDT',side='BUY',type='MARKET',quantity=qty)

            # save order in database
            self.store_order(sell_order)

            # update main values
            self.balance += sell_order.price*sell_order.qty
            self.total_qty -= qty

            buy_order = self.acquired_crypto[0]
            self.acquired_crypto = self.acquired_crypto[1:]

            return sell_order,buy_order
        except Exception as e:
            print(e)
            return None


    def get_lookback(self,type:LookBackEnum, rows:int=0, timestamp:dt.datetime=None):
        # get fresh data
        df = pd.read_sql(self.symbol,self.engine)
        if type == LookBackEnum.ROWS:
            # take all rows of lookback
            return df.iloc[-rows:]
        if type == LookBackEnum.TIMESTAMP: 
            # take all rows from timestamp
            return df.loc[df.time > timestamp ]
        return df

    
    def get_status(self):
        print("\nactual balance: {}".format(self.balance))
        print("actual profit: {}".format(self.profit))
        print("actual qty: {}".format(self.total_qty))
        print("storage: ")
        for el in self.acquired_crypto:
            print(el)
        print("\n")