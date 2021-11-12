from threading import Lock
from traders.base_trader import LookBackEnum
from traders.agent import Agent
from traders.base_trader import BaseTrader

class AgentTrader(BaseTrader):
    def __init__(self,api_key,secret_key,symbol:str='BTCUSDT',db_lock:Lock=None,pause_seconds:float=1,initial_balance=250,qty=0.001,backward_steps=20,console_lock:Lock=None,name:str="agent",with_profit_control:bool=True):
        super().__init__(api_key,secret_key,symbol,db_lock,pause_seconds,initial_balance,qty,console_lock,name,with_profit_control)
        self.agent = Agent(self.symbol,backward_steps)

    def trade(self):
        while True:
            future_price = self.agent.predict()[0]
            last_row = self.get_lookback(LookBackEnum.ROWS,1)
            actual_price = last_row.iloc[0]['price']

            # se il prezzo scendera', vendo
            # vendo solo se il guadagno previsto è maggiore di 1
            if actual_price > future_price and self.total_qty>=self.qty:
                if self.with_profit_control:
                    sell_order,buy_order = self.simulate_sell(self.qty)
                    partial_profit = self.get_transaction_profit(buy_order,sell_order)
                    if partial_profit > 0.01:
                        sell_order,buy_order = self.sell(self.qty)
                else:
                    sell_order,buy_order = self.sell(self.qty)
            # se il prezzo salira', compro
            if actual_price < future_price and self.balance > actual_price*self.qty:
                buy_order = self.buy(self.qty)
            # quanto ho in cassa?
            self.get_status()
            self.pause()