import asyncio
from threading import Lock
from config.key import api_key,secret_key
from config.config import symbol,backward_steps
from data_collector import DataCollector
from traders.traders import HeuristicTrader,AgentTrader,CumRetTrader


async def main():
    console_lock = Lock()
    db_lock = Lock()
    data_collector = DataCollector(api_key,secret_key,symbol,db_lock=db_lock)

    heuristic_trader = HeuristicTrader(api_key,secret_key,symbol,db_lock=db_lock,backward_steps=backward_steps,console_lock=console_lock)
    free_heuristic_trader = HeuristicTrader(api_key,secret_key,symbol,db_lock=db_lock,backward_steps=backward_steps,console_lock=console_lock,with_profit_control=False,name="free_heuristic")
    agent_trader = AgentTrader(api_key,secret_key,symbol,db_lock=db_lock,console_lock=console_lock)
    free_agent_trader = AgentTrader(api_key,secret_key,symbol,db_lock=db_lock,console_lock=console_lock,with_profit_control=False,name="free_agent")
    cum_ret_trader = CumRetTrader(api_key,secret_key,symbol,db_lock=db_lock,console_lock=console_lock)

    heuristic_trader.start()
    free_heuristic_trader.start()
    agent_trader.start()
    free_agent_trader.start()
    cum_ret_trader.start()

    await data_collector.get_data()

    heuristic_trader.join()
    free_heuristic_trader.join()
    agent_trader.join()
    free_agent_trader.join()
    cum_ret_trader.join()
    print("collector stopped")


if __name__=="__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())