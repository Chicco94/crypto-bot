from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pandas as pd
import sqlalchemy
import joblib
from df_functions import add_id


class Agent():
    def __init__(self,symbol,backward_steps):
        self.symbol = symbol
        self.engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
        self.model = joblib.load('models/model_best.sav')
        self.backward_steps = backward_steps
        # per ignorare SettingWithCopyWarning
        pd.options.mode.chained_assignment = None

    def prepare_single_step_sample(self,df,start,end):
        if start == 1: 
            step_of_df = df.iloc[-start:]
        else: 
            step_of_df = df.iloc[-start:-end]
        add_id(step_of_df)
        step_of_df.time = step_of_df.time.apply(lambda x: x.value)
        step_of_df.rename(columns={"time": "time{}".format(start)
                                ,"price": "price{}".format(start)
                                ,"quantity":"quantity{}".format(start)}
                            ,inplace=True)
        step_of_df.drop(columns=['symbol'],inplace=True)
        return step_of_df

    def prepare_sample(self, df):
        # get last rows
        datasets = []
        for i in range(1,self.backward_steps):
            datasets.append(self.prepare_single_step_sample(df,i,i-1))

        result = datasets.pop()
        while len(datasets)>0:
            result = pd.merge(result, datasets.pop(), on="ID")
        return result
    
    def get_sample(self):
        df = pd.read_sql(self.symbol,self.engine)
        sample = self.prepare_sample(df)
        return sample

    def predict(self):
        sample = self.get_sample()
        return self.model.predict(sample)
