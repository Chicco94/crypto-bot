import pandas as pd
import sqlalchemy
import asyncio
from binance.client import AsyncClient
from binance import BinanceSocketManager
from time import sleep
from key import api_key,secret_key
from config import symbol

class DataCollector():
    def __init__(self,api_key,secret_key,symbol='BTCUSDT',pause=1):
        '''apy_key: apy_key of Binance client
            secret_key: secret_key of Binance client
            symbol: [str] symbol of crypto (default 'BTCUSDT')
            pause: [float] pause between readings (default 0.5)'''
        self.symbol = symbol
        self.client = AsyncClient(api_key,secret_key)
        self.bsm = BinanceSocketManager(self.client)
        self.engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
        self.pause = pause


    async def get_data(self):
        '''start the connection and store data'''
        async with self.bsm.trade_socket(symbol=self.symbol) as stream:
            while True:
                try:
                    res = await stream.recv()
                except InterruptedError as e:
                    print(e)
                finally:
                    frame = self.createFrame(res)
                    frame.to_sql(self.symbol,self.engine,if_exists='append',index=False)
                    sleep(self.pause)


    def createFrame(self,msg):
        '''create a frame based on socket response'''
        df = pd.DataFrame([msg])
        # "e": "aggTrade",  // Event type
        # "E": 123456789,   // Event time
        # "s": "BNBBTC",    // Symbol
        # "a": 12345,       // Aggregate trade ID
        # "p": "0.001",     // Price
        # "q": "100",       // Quantity
        # "f": 100,         // First trade ID
        # "l": 105,         // Last trade ID
        # "T": 123456785,   // Trade time
        # "m": true,        // Is the buyer the market maker?
        # "M": true         // Ignore
        df = df.loc[:,['s','E','p','q']]
        df.columns = ['symbol','time','price','quantity']
        df.price = df.price.astype(float)
        df.quantity = df.quantity.astype(float)
        df.time = pd.to_datetime(df.time,unit='ms')
        return df    



def init():
    '''Initialization of collector'''
    print("staring initialization...")
    myDataCollector = DataCollector(api_key,secret_key,symbol)
    print("initialization of data collector completed...")
    return myDataCollector


async def main():
    collector = init()
    await collector.get_data()
    print("collector stopped")


if __name__=="__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())