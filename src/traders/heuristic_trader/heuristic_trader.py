from threading import Lock
from traders.base_trader import BaseTrader,LookBackEnum
from scipy.stats import linregress
from numpy import NaN
import warnings


class HeuristicTrader(BaseTrader):
    def __init__(self,api_key,secret_key,symbol:str='BTCUSDT',db_lock:Lock=None,pause_seconds:float=1,initial_balance=250,qty=0.001,backward_steps=20,console_lock:Lock=None,name:str="heuristic",with_profit_control:bool=True):
        super().__init__(api_key,secret_key,symbol,db_lock,pause_seconds,initial_balance,qty,console_lock,name,with_profit_control)
        self.backward_steps = backward_steps

    def get_gradient(self,df):
        '''0:stable
            1: increasing
            -1:decreasing'''
        df.time = df.time.apply(lambda x: x.value)
        prices = df['price'].tolist()
        times = df['time'].tolist()
        try:
            slope = linregress(times,prices).slope
        except RuntimeWarning as w:
            warnings.simplefilter("ignore")
            return 0
        if slope is NaN :
            return 0
        if slope > 0:
            return 1
        return -1

    def trade(self):
        last_gradients = []
        # recupero un po' di info
        while len(last_gradients)<self.backward_steps:
            new_gradient = self.get_gradient(self.get_lookback(LookBackEnum.ROWS,self.backward_steps))
            last_gradients.append(new_gradient)
            self.pause()
            
        while True:
            # valori attuali
            last_row = self.get_lookback(LookBackEnum.ROWS,1)
            actual_price = last_row.iloc[0]['price']

            # valuto andamento
            new_gradient = self.get_gradient(self.get_lookback(LookBackEnum.ROWS,self.backward_steps))
            last_gradients = last_gradients[1:]
            last_gradients.append(new_gradient)
            
            # sto crescendo...se ho ancora denaro, compro
            if sum(last_gradients) == len(last_gradients):
                while self.balance > actual_price*self.qty:
                    buy_order = self.buy(self.qty)
             # sto calando...se ho ancora crediti, vendo
            elif sum(last_gradients) == -len(last_gradients):
                while self.total_qty>=self.qty:
                    if self.with_profit_control:
                        sell_order,buy_order = self.simulate_sell(self.qty)
                        partial_profit = self.get_transaction_profit(buy_order,sell_order)
                        if partial_profit > 0.01:
                            sell_order,buy_order = self.sell(self.qty)
                    else:
                        sell_order,buy_order = self.sell(self.qty)
            # else:
                #self.sem_print("sono stabile")
            # quanto ho in cassa?
            self.get_status()
            self.pause()