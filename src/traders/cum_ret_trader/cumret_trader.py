from threading import Lock
from traders.base_trader import BaseTrader,LookBackEnum
import pandas as pd


class CumRetTrader(BaseTrader):
    def __init__(self,api_key,secret_key,symbol:str='BTCUSDT',db_lock:Lock=None,pause_seconds:float=1,initial_balance=250,qty=0.001,backward_steps=20,console_lock:Lock=None,name:str="cum_ret",entry_level:float=0,min_profit:float=0.01,max_loss:float=0.1):
        super().__init__(api_key,secret_key,symbol,db_lock,pause_seconds,initial_balance,qty,console_lock,name)
        self.backward_steps = backward_steps
        self.entry_level = entry_level
        self.min_profit = min_profit
        self.max_loss = max_loss

    def get_cumulative_return(self,df):
        return (df.price.pct_change()+1).cumprod() -1

    def trade(self):
        while True:
            buy_order = None
            while buy_order is None:
                # get lookback rows
                loopback_period = self.get_lookback(LookBackEnum.ROWS, rows=self.backward_steps)
                # get cumulative return
                cum_ret = self.get_cumulative_return(loopback_period)
                # if cumulative return greater then entry level
                if cum_ret[cum_ret.last_valid_index()] > self.entry_level:
                    buy_order = self.buy(self.qty)
                    
            sell_order = None
            while sell_order is None:
                # take all rows since last buy order
                since_buy = self.get_lookback(LookBackEnum.TIMESTAMP, timestamp=pd.to_datetime(buy_order.transactTime,unit='ms'))
                # get cumulative return
                since_buy_ret = self.get_cumulative_return(since_buy)
                last_entry = since_buy_ret.last_valid_index()
                if last_entry is not None:
                    last_entry_profit = since_buy_ret[last_entry]
                    # if minimum profit aquired or max loss reached
                    if last_entry_profit > self.min_profit or last_entry_profit < -self.max_loss:
                        # SELL!!
                        sell_order,buy_order = self.sell(self.qty)
            self.get_status()
            self.pause()