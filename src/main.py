from traders.heuristic_trader import HeuristicTrader
from config.key import api_key,secret_key
from config.config import symbol,backward_steps

def init():
    '''Initialization of trader'''
    print("staring initialization...")
    myTrader = HeuristicTrader(api_key,secret_key,symbol,backward_steps=backward_steps)
    print("initialization of trader completed...")
    return myTrader


def main():
    trader = init()
    #trader.trade_with_agent(0.001)
    trader.trade(0.001)
    #trader.trade(0,500,0.001,0.001,0.01)
    print("collector stopped")


if __name__=="__main__":
    main()