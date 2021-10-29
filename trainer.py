from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pandas as pd
import sqlalchemy
from config.config import symbol,backward_steps
import joblib
from df_functions import *

def prepare_single_dataset(df,remove_from_heads:int,remove_from_tails:int,label:int):
    df_copy = df.copy()
    for _ in range(remove_from_tails):
        remove_row_from_tail(df_copy)
    for _ in range(remove_from_heads):
        remove_row_from_head(df_copy)
    add_id(df_copy)
    df_copy.time = df_copy.time.apply(lambda x: x.value)
    df_copy.rename(columns={"time": "time{}".format(label)
                        , "price": "price{}".format(label)
                        , "quantity":"quantity{}".format(label)}
                    ,inplace=True)
    df_copy.drop(columns=['symbol'],inplace=True)
    return df_copy
    

def prepare_dataset(df,steps:int):
    datasets = []
    for i in range(1,steps):
        datasets.append(prepare_single_dataset(df,steps-i,i-1,i))
    df_target = prepare_single_dataset(df,0,steps-1,steps)

    result = datasets.pop()
    while len(datasets)>0:
        result = pd.merge(result, datasets.pop(), on="ID")

    target = df_target['price{}'.format(steps)]
    return result,target

def main():
    # open database
    engine = sqlalchemy.create_engine('sqlite:///data/{}_stream.db'.format(symbol))
    df = pd.read_sql(symbol,engine)
    # prepare dataset
    source,target = prepare_dataset(df,backward_steps)
    # train model
    model = LinearRegression()
    X_train,X_test,y_train,y_test = train_test_split(source,target,test_size=0.33)
    model.fit(X_train,y_train)
    # evaluate model
    score = model.score(X_test,y_test)
    print('score: ',score)
    # save model
    filename = 'models/model_{}.sav'.format(score)
    joblib.dump(model, filename)

    #model = joblib.load(filename)

if __name__=='__main__':
    main() 