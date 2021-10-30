from dataclasses import dataclass
from datetime import datetime

@dataclass
class Order():
    transactTime:datetime
    price:float
    qty:float
    type:str

    def value(self)->float:
        return self.price*self.qty