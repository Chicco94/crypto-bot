def add_id(df):
    df.insert(0, 'ID', range(0, 0 + len(df)))

def remove_row_from_head(df):
    df.drop(df.time.idxmin(),inplace=True)

def remove_row_from_tail(df):
    df.drop(len(df)-1,inplace=True)