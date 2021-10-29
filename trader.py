from numpy import NaN
import pandas as pd
import sqlalchemy
from binance.client import AsyncClient
from binance import BinanceSocketManager
from enum import Enum
from time import sleep
from config.key import api_key,secret_key
from config.config import symbol,backward_steps
import datetime as dt
from agent import Agent
from scipy.stats import linregress


class LookBackEnum(Enum):
    ROWS = 1
    TIMESTAMP = 2

class Trader():
    def __init__(self,api_key,secret_key,symbol='BTCUSDT',pause=1,backward_steps=3):
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
        self.agent = Agent(symbol,backward_steps)

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
            # vendo solo se il guadagno previsto è maggiore di 1
            if actual_price > future_price and total_qty>=qty:
                order = {'transactTime':actual_time,'price':actual_price,'qty':qty,'type':'SELL'}
                buy_order = store[0]
                partial_profit = self.get_transaction_profit(buy_order,order)
                if partial_profit > 0.01:
                    balance += order['price']*order['qty']
                    store = store[1:]
                    profit += partial_profit
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
            # quanto ho in cassa?
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

    def get_gradient(self,df):
        '''0:stable
            1: increasing
            -1:decreasing'''
        df.time = df.time.apply(lambda x: x.value)
        prices = df['price'].tolist()
        times = df['time'].tolist()
        slope = linregress(times,prices).slope
        if slope is NaN :
            return 0
        if slope > 0:
            return 1
        return -1
    
    def trade_with_history(self,qty):
        order = None
        total_qty = 0
        balance = 250
        store = []
        profit = 0
        last_gradients = []
        # recupero un po' di info
        while len(last_gradients)<3:
            new_gradient = self.get_gradient(self.get_lookback(LookBackEnum.ROWS,3))
            last_gradients.append(new_gradient)
            sleep(self.pause)
            
        while True:
            # valori attuali
            last_row = self.get_lookback(LookBackEnum.ROWS,1)
            actual_price = last_row.iloc[0]['price']
            actual_time = last_row.iloc[0]['time']

            # valuto andamento
            new_gradient = self.get_gradient(self.get_lookback(LookBackEnum.ROWS,3))
            last_gradients = last_gradients[1:]
            last_gradients.append(new_gradient)
            
            # sto crescendo...se ho ancora denaro, compro
            if sum(last_gradients) == len(last_gradients):
                print("sto crescendo")
                while balance > actual_price*qty:
                    order = {'transactTime':actual_time,'price':actual_price,'qty':qty,'type':'BUY'}
                    balance -= order['price']*order['qty']
                    store.append(order)
                    total_qty += qty
                    print("bought: {}".format(order))
             # sto calando...se ho ancora crediti, vendo
            elif sum(last_gradients) == -len(last_gradients):
                print("sto calando")
                while total_qty>=qty:
                    order = {'transactTime':actual_time,'price':actual_price,'qty':qty,'type':'SELL'}
                    balance += order['price']*order['qty']
                    buy_order = store[0]
                    partial_profit = self.get_transaction_profit(buy_order,order)
                    store = store[1:]
                    profit += partial_profit
                    total_qty -= qty
                    print("sold: {}".format(order))
            else:
                print("sono stabile")
            # quanto ho in cassa?
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
            sleep(self.pause)
            

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
    myTrader = Trader(api_key,secret_key,symbol,backward_steps=backward_steps)
    print("initialization of trader completed...")
    return myTrader


def main():
    trader = init()
    #trader.trade_with_agent(0.001)
    trader.trade_with_history(0.001)
    #trader.trade(0,500,0.001,0.001,0.01)
    print("collector stopped")


if __name__=="__main__":
    main()