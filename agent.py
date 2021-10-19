from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pandas as pd
import sqlalchemy
from config import symbol
import joblib
from df_functions import add_id


class Agent():
    def __init__(self,symbol):
        self.symbol = symbol
        self.engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
        self.model = joblib.load('models/model_best.sav')
        # per ignorare SettingWithCopyWarning
        pd.options.mode.chained_assignment = None

    def prepare_sample(self, df):
        # get last three rows
        df1 = df.iloc[-1:]
        df2 = df.iloc[-2:-1]
        df3 = df.iloc[-3:-2]

        add_id(df1)
        df1.time = df1.time.apply(lambda x: x.value)
        df1.rename(columns={"time": "time1", "price": "price1","quantity":"quantity1"},inplace=True)

        add_id(df2)
        df2.time = df2.time.apply(lambda x: x.value)
        df2.rename(columns={"time": "time2", "price": "price2","quantity":"quantity2"},inplace=True)

        add_id(df3)
        df3.time = df3.time.apply(lambda x: x.value)
        df3.rename(columns={"time": "time3", "price": "price3","quantity":"quantity3"},inplace=True)

        result = pd.merge(df1, df2, on="ID")
        result = pd.merge(result, df3, on="ID")

        result.drop(columns=['symbol_x','symbol_y','symbol'],inplace=True)
        return result
    
    def get_sample(self):
        df = pd.read_sql(self.symbol,self.engine)
        sample = self.prepare_sample(df)
        return sample

    def predict(self):
        sample = self.get_sample()
        return self.model.predict(sample)
