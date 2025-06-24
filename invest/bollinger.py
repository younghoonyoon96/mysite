import pandas as pd 
import numpy as np
from datetime import datetime

def create_band(
    _df, 
    _start = '2010-01-01', 
    _end = datetime.now(),
    _col = 'Adj Close', 
    _cnt = 20
):
    # 복사본을 생성 
    df = _df.copy()
    # Date 컬럼에 존재하면 인덱스로 변환
    if 'Date' in df.columns:
        df.set_index('Date', inplace=True)
    # 인덱스를 시계열 데이터로 변경 
    df.index = pd.to_datetime(df.index)
    # 기준이 되는 컬럼을 제외하고 모두 제거 -> 특정 컬럼만 선택
    df = df[[_col]]
    # 결측치, 무한대 제거 
    flag = df.isin([np.nan, np.inf, -np.inf]).any(axis=1)
    df = df.loc[~flag, ]
    df['center'] = df[_col].rolling(_cnt).mean()
    std_data = df[_col].rolling(_cnt).std()
    df['ub'] = df['center'] + (2 * std_data)
    df['lb'] = df['center'] - (2 * std_data)
    # 시작 시간과 종료시간으로 데이터를 필터링
    df = df.loc[_start : _end, ]
    return df

def create_trade(_df):
    # 복사본을 생성
    df = _df.copy()
    # trade 컬럼을 생성
    df['trade'] = ""
    # 기준이 되는 컬럼의 이름을 변수에 저장 
    col = df.columns[0]
    # 거래 내역 추가하는 반복문을 사용 
    for idx in df.index:
        # 상단 밴드보다 기준이되는 컬럼의 값이 크거나 같은 경우 
        if df.loc[idx, col] >= df.loc[idx, 'ub']:
            df.loc[idx, 'trade'] = ""
        # 하단 밴드보다 기준이 되는 컬럼의 값이 작거나 같은 경우
        elif df.loc[idx, col] <= df.loc[idx, 'lb']:
            df.loc[idx, 'trade'] = 'buy'
        # 밴드 사이에 기준이 되는 컬럼의 값이 존재하는 경우
        else:
            # 현재 보유중 -> 보유 유지
            # 보유 상태가 아니면 -> 유지
            # 전날의 trade를 그대로 유지 
            df.loc[idx, 'trade'] = df.shift().loc[idx, 'trade']
    return df

def create_rtn(_df):
    # 복사본 생성 
    df = _df.copy()
    # 기준이 되는 컬럼의 이름은 변수에 저장 
    col = df.columns[0]

    # rtn 컬럼을 생성하여 1을 대입 
    df['rtn'] = 1

    # 수익율 계산
    for idx in df.index:
        # 매수 
        if (df.shift().loc[idx, 'trade'] == "") & \
            (df.loc[idx, 'trade'] == 'buy'):
            buy = df.loc[idx, col]
            print(f"매수일 : {idx}, 매수가 : {buy}")
        # 매도
        elif (df.shift().loc[idx, 'trade'] == "buy") & \
            (df.loc[idx, 'trade'] == ""):
            sell = df.loc[idx, col]
            rtn = sell / buy
            df.loc[idx, 'rtn'] = rtn
            print(f"매도일 : {idx}, 매도가 : {sell}, 수익율 : {rtn}")
    # 누적수익율 계산
    df['acc_rtn'] = df['rtn'].cumprod()
    # 최종 누적 수익율
    acc_rtn = df.iloc[-1, -1]
    return df, acc_rtn