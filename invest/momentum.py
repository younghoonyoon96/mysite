from datetime import datetime 
import pandas as pd
import numpy as np

def create_YM(
    _df, 
    _col = 'Adj Close'
):
    df = _df.copy()
    if 'Date' in df.columns:
        df.set_index('Date', inplace=True)
    df.index = pd.to_datetime(df.index)
    flag = df.isin( [np.nan, np.inf, -np.inf] ).any(axis=1)
    df = df.loc[~flag, ]
    df = df[[_col]]
    df['STD-YM'] = df.index.strftime('%Y-%m')
    return df

def create_last_month(
    _df, 
    _start = '2010-01-01', 
    _end = datetime.now(), 
    _momentum = 12
):
    # 기준이 되는 컬럼의 이름을 변수에 저장 
    col = _df.columns[0]
    # 월말의 기준 : STD-YM이 현재와 다음행의 데이터가 다른경우
    flag = _df['STD-YM'] != _df.shift(-1)['STD-YM']
    df = _df.loc[flag, ]
    # 전월의 데이터를 생성 
    df['BF1'] = df.shift(1)[col].fillna(0)
    # _momentum의 개월 전의 데이터를 생성 
    df['BF2'] = df.shift(_momentum)[col].fillna(0)
    # 시작 시간과 종료 시간을 기준으로 필터링 
    df = df.loc[_start : _end, ]
    return df

def create_rtn(
    _df1, _df2, 
    _start = '2010-01-01',
    _end = datetime.now(),
    _score = 1
):
    df = _df1.copy()
    df = df.loc[_start : _end, ]
    # trade, rtn 컬럼을 생성
    df['trade'] = ""
    df['rtn'] = 1

    # _df2를 이용해서 momentum_index를 구한다. 
    for idx in _df2.index:
        signal = ""

        # 모멘텀 인덱스를 계산 
        momentum_index = \
            _df2.loc[idx, 'BF1'] / _df2.loc[idx, 'BF2'] - _score
        
        flag = (momentum_index > 0) & (momentum_index != np.inf)

        if flag : 
            signal = 'buy'
        # df에 구매내역 추가
        df.loc[idx: , 'trade'] = signal
    # 기준이 되는 컬럼의 이름 변수에 저장 
    col = df.columns[0]

    for idx in df.index:
        # 매수 조건 
        if (df.shift().loc[idx, 'trade'] == "") & \
            (df.loc[idx, 'trade'] == "buy"):
            buy = df.loc[idx, col]
            print(f"매수일 : {idx}, 매수가 : {buy}")
        # 매도 조건
        elif (df.shift().loc[idx, 'trade'] == 'buy') & \
            (df.loc[idx, 'trade'] == ""):
            sell = df.loc[idx, col]
            rtn = sell / buy
            df.loc[idx, 'rtn'] = rtn
            print(f"매도일 : {idx}, 매도가 : {sell}, 수익율 : {rtn}")
    #  누적수익율 계산
    df['acc_rtn'] = df['rtn'].cumprod()
    acc_rtn = df.iloc[-1, -1]
    return df, acc_rtn