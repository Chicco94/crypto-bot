import pandas as pd
import sqlalchemy
from binance.client import AsyncClient
from binance import BinanceSocketManager
from enum import Enum
from time import sleep
from key import api_key,secret_key
from config import symbol
import datetime as dt
from agent import Agent


class LookBackEnum(Enum):
    ROWS = 1
    TIMESTAMP = 2

class Trader():
    def __init__(self,api_key,secret_key,symbol='BTCUSDT',pause=1):
        '''apy_key: apy_key of Binance client
            secret_key: secret_key of Binance client
            symbol: [str] symbol of crypto (default 'BTCUSDT')
            pause: [float] pause between readings (default 0.5)'''
        self.symbol = symbol
        self.client = AsyncClient(api_key,secret_key)
        self.bsm = BinanceSocketManager(self.client)
        self.engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
        self.store_engine = sqlalchemy.create_engine('sqlite:///data/{}_order_stream.db'.format(symbol))
        self.pause = pause
        self.agent = Agent(symbol)

    def trade_with_agent(self,qty):
        order = None
        total_qty = 0
        balance = 250
        store = []
        profit = 0
        while True:
            future_price = self.agent.predict()[0]
            last_row = self.get_lookback(LookBackEnum.ROWS,1)
            actual_price = last_row.iloc[0]['price']
            actual_time = last_row.iloc[0]['time']

            # se il prezzo scendera', vendo
            if actual_price > future_price and total_qty>=qty:
                order = {'transactTime':actual_time,'price':actual_price,'qty':qty,'type':'SELL'}
                balance += order['price']*order['qty']
                buy_order = store[0]
                store = store[1:]
                profit += self.get_transaction_profit(buy_order,order)
                total_qty -= qty
                print("predicted {} > actual {}".format(future_price,actual_price))
                print("sold: {}".format(order))
            # se il prezzo salira', compro
            if actual_price < future_price and balance > actual_price*qty:
                order = {'transactTime':actual_time,'price':actual_price,'qty':qty,'type':'BUY'}
                balance -= order['price']*order['qty']
                store.append(order)
                total_qty += qty
                print("predicted {} < actual {}".format(future_price,actual_price))
                print("bought: {}".format(order))
            # quanto ho in assa
            if order is not None:
                self.store_order(order)
                print("\nactual balance: {}".format(balance))
                print("actual profit: {}".format(profit))
                print("actual qty: {}".format(total_qty))
                print("storage: ")
                for el in store:
                    print(el)
                print("\n")
                order = None
            

    def trade(self, entry_level, lookback, qty, min_profit, max_loss):
        '''start the connection and store data'''
        profit = 0
        while True:
            buy_order = self.buy(lookback,entry_level,qty)
            if buy_order is not None:
                print("bought: {}".format(buy_order))
                self.store_order(buy_order)
                sell_order = self.sell(buy_order,qty,min_profit,max_loss)
                if sell_order is not None:
                    self.store_order(sell_order)
                    profit += self.get_transaction_profit(buy_order,sell_order)
                    print("sold: {}".format(sell_order))
                    print("actual profit: {}\n".format(profit))
            sleep(self.pause)


    def get_transaction_profit(self,buy_order,sell_order):
        return sell_order['price']*sell_order['qty'] - buy_order['price']*buy_order['qty']

    
    def store_order(self,order):
        df = pd.DataFrame([order])
        df.price = df.price.astype(float)
        df.qty = df.qty.astype(float)
        #df.transactTime = pd.to_datetime(df.transactTime,unit='ms')
        df.to_sql(self.symbol,self.store_engine,if_exists='append',index=False)

    
    def buy(self,lookback,entry_level,qty):
        print("buying...")
        while True:
            # get lookback rows
            loopback_period = self.get_lookback(LookBackEnum.ROWS, rows=lookback)
            # get cumulative return
            cum_ret = self.get_cumulative_return(loopback_period)
            # if cumulative return greater then entry level
            if cum_ret[cum_ret.last_valid_index()] > entry_level:
                # BUY!!
                try:
                    last = loopback_period.iloc[-1]
                    order = {'transactTime':last['time'],'price':last['price'],'qty':qty,'type':'BUY'} 
                    #order = self.client.create_order(symbol='BTCUSDT',side='BUY',type='MARKET',quantity=qty)
                    return order
                except Exception as e:
                    print(e)
                    return None


    def sell(self,order,qty,min_profit,max_loss):
        print("selling...")
        while True:
            # take all rows since last buy order
            since_buy = self.get_lookback(LookBackEnum.TIMESTAMP, timestamp=pd.to_datetime(order['transactTime'],unit='ms'))
            # get cumulative return
            since_buy_ret = self.get_cumulative_return(since_buy)
            last_entry = since_buy_ret.last_valid_index()
            if last_entry is not None:
                last_entry_profit = since_buy_ret[last_entry]
                # if minimum profit aquired or max loss reached
                if last_entry_profit > min_profit or last_entry_profit < -max_loss:
                    # SELL!!
                    last = since_buy.iloc[-1]
                    order = {'transactTime':last['time'],'price':last['price'],'qty':qty,'type':'SELL'} 
                    return order
                    return self.client.create_order(symbol='BTCUSDT',side='SELL',type='MARKET',quantity=qty)
                    

    def get_lookback(self,type:LookBackEnum, rows:int=0, timestamp:dt.datetime=None):
        # get fresh data
        df = pd.read_sql('BTCUSDT',self.engine)
        if type == LookBackEnum.ROWS:
            # take all rows of lookback
            return df.iloc[-rows:]
        if type == LookBackEnum.TIMESTAMP: 
            # take all rows from timestamp
            return df.loc[df.time > timestamp ]
        return df


    def get_cumulative_return(self,df):
        return (df.price.pct_change()+1).cumprod() -1



def init():
    '''Initialization of trader'''
    print("staring initialization...")
    myTrader = Trader(api_key,secret_key,symbol)
    print("initialization of trader completed...")
    return myTrader


def main():
    trader = init()
    trader.trade_with_agent(0.001)
    #trader.trade(0,500,0.001,0.001,0.01)
    print("collector stopped")


if __name__=="__main__":
    main()