import pandas as pd
import sqlalchemy
from config import symbol
from matplotlib import pyplot as plt

class DataAnalyzer():
    def __init__(self,symbol='BTCUSDT',pause=1):
        '''symbol: [str] symbol of crypto (default 'BTCUSDT')
            pause: [float] pause between readings (default 0.5)'''
        self.symbol = symbol
        self.engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
        self.pause = pause


    def plot_data(self):
        '''start the connection and store data'''
        plt.ion()
        ax = None
        while True:
            df = self.getFrame()
            ax = df.plot(x='time',y='price', ax=ax)
            plt.draw()
            plt.pause(self.pause)
            ax.clear()
    
    def getFrame(self):
        df = pd.read_sql(self.symbol,self.engine)
        end = df.index.max()
        start= end - 1000
        df = df.loc[start:end]
        return df



def init(symbol:str):
    '''Initialization of collector'''
    print("staring initialization...")
    myDataAnalizer = DataAnalyzer(symbol)
    print("initialization of data analyzer completed...")
    return myDataAnalizer


def main():
    analyzer = init(symbol)
    analyzer.plot_data()
    print("analyzer stopped")


if __name__=="__main__":
    main()