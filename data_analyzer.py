import pandas as pd
import sqlalchemy
from config.config import symbol,backward_steps
from matplotlib import pyplot as plt
from agent import Agent

class DataAnalyzer():
    def __init__(self,symbol='BTCUSDT',pause=1,backward_steps=3):
        '''symbol: [str] symbol of crypto (default 'BTCUSDT')
            pause: [float] pause between readings (default 0.5)'''
        self.symbol = symbol
        self.engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
        self.pause = pause
        self.agent = Agent(symbol,backward_steps)


    def plot_data(self):
        '''start the connection and store data'''
        plt.ion()
        ax = None
        while True:
            df = self.getFrame()
            ax = df.plot(x='time',y='price', ax=ax)
            df = self.agent.get_sample()
            # df['predicted'] = self.agent.predict()[0]
            # ax = df.plot(x='time1',y='predicted', ax=ax)
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
    myDataAnalizer = DataAnalyzer(symbol,backward_steps = backward_steps)
    print("initialization of data analyzer completed...")
    return myDataAnalizer


def main():
    analyzer = init(symbol)
    analyzer.plot_data()
    print("analyzer stopped")


if __name__=="__main__":
    main()