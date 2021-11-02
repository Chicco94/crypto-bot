from traders.base_trader import BaseTrader,LookBackEnum
from scipy.stats import linregress
from numpy import NaN
import warnings

class HeuristicTrader(BaseTrader):
    def __init__(self,api_key,secret_key,symbol:str='BTCUSDT',pause_seconds:float=1,initial_balance=250,backward_steps=20):
        super().__init__(api_key,secret_key,symbol,pause_seconds,initial_balance)
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

    def trade(self,qty):
        last_gradients = []
        order = None
        # recupero un po' di info
        while len(last_gradients)<3:
            new_gradient = self.get_gradient(self.get_lookback(LookBackEnum.ROWS,self.backward_steps))
            last_gradients.append(new_gradient)
            self.pause()
            
        while True:
            # valori attuali
            last_row = self.get_lookback(LookBackEnum.ROWS,1)
            actual_price = last_row.iloc[0]['price']
            actual_time = last_row.iloc[0]['time']

            # valuto andamento
            new_gradient = self.get_gradient(self.get_lookback(LookBackEnum.ROWS,self.backward_steps))
            last_gradients = last_gradients[1:]
            last_gradients.append(new_gradient)
            
            # sto crescendo...se ho ancora denaro, compro
            if sum(last_gradients) == len(last_gradients):
                print("sto crescendo")
                while self.balance > actual_price*qty:
                    order = self.buy(qty)
                    print("bought: {}".format(order))
             # sto calando...se ho ancora crediti, vendo
            elif sum(last_gradients) == -len(last_gradients):
                print("sto calando")
                while self.total_qty>=qty:
                    order,buy_order = self.sell(qty)
                    print("sold: {}".format(order))
            else:
                print("sono stabile")
            # quanto ho in cassa?
            if order is not None:
                self.get_status()
                order = None
            self.pause()