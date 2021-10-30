from base_trader import BaseTrader,LookBackEnum
from agent import Agent

class AgentTrader(BaseTrader):
    def __init__(self,backward_steps=20):
        super.__init__(BaseTrader)
        self.agent = Agent(self.symbol,backward_steps)

    def trade(self,qty):
        order = None
        while True:
            future_price = self.agent.predict()[0]
            last_row = self.get_lookback(LookBackEnum.ROWS,1)
            actual_price = last_row.iloc[0]['price']

            # se il prezzo scendera', vendo
            # vendo solo se il guadagno previsto è maggiore di 1
            if actual_price > future_price and self.total_qty>=qty:
                order,buy_order = self.simulate_sell(qty)
                partial_profit = self.get_transaction_profit(buy_order,order)
                if partial_profit > 0.01:
                    order,buy_order = self.sell(qty)
                    print("predicted {} > actual {}".format(future_price,actual_price))
                    print("sold: {}".format(order))
            # se il prezzo salira', compro
            if actual_price < future_price and self.balance > actual_price*qty:
                order = self.buy(qty)
                print("predicted {} < actual {}".format(future_price,actual_price))
                print("bought: {}".format(order))
            # quanto ho in cassa?
            if order is not None:
                self.get_status()
                order = None
            self.pause()