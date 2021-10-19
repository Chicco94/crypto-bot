from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pandas as pd
import sqlalchemy
from config import symbol
import joblib
from df_functions import *

def prepare_dataset(df):
    df1 = df.copy()
    df2 = df.copy()
    df3 = df.copy()
    df4 = df.copy()

    remove_row_from_head(df1)
    remove_row_from_head(df1)
    remove_row_from_head(df1)
    add_id(df1)
    df1.time = df1.time.apply(lambda x: x.value)
    df1.rename(columns={"time": "time1", "price": "price1","quantity":"quantity1"},inplace=True)

    remove_row_from_tail(df2)
    remove_row_from_head(df2)
    remove_row_from_head(df2)
    add_id(df2)
    df2.time = df2.time.apply(lambda x: x.value)
    df2.rename(columns={"time": "time2", "price": "price2","quantity":"quantity2"},inplace=True)

    remove_row_from_tail(df3)
    remove_row_from_tail(df3)
    remove_row_from_head(df3)
    add_id(df3)
    df3.time = df3.time.apply(lambda x: x.value)
    df3.rename(columns={"time": "time3", "price": "price3","quantity":"quantity3"},inplace=True)

    remove_row_from_tail(df4)
    remove_row_from_tail(df4)
    remove_row_from_tail(df4)
    add_id(df4)

    result = pd.merge(df1, df2, on="ID")
    result = pd.merge(result, df3, on="ID")

    target = df4['price']
    result.drop(columns=['symbol_x','symbol_y','symbol'],inplace=True)
    return result,target

def main():
    # open database
    engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
    df = pd.read_sql(symbol,engine)
    # prepare dataset
    source,target = prepare_dataset(df)
    # train model
    model = LinearRegression()
    X_train,X_test,y_train,y_test = train_test_split(source,target,test_size=0.33)
    model.fit(X_train,y_train)
    # evaluate model
    score = model.score(X_test,y_test)
    # save model
    filename = 'models/model_{}.sav'.format(score)
    joblib.dump(model, filename)

    #model = joblib.load(filename)

if __name__=='__main__':
    main() 