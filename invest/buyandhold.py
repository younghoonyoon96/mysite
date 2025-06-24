import pandas as pd 
from datetime import datetime 
import numpy as np

def bnh(
    _df, 
    _start = '2010-01-01', 
    _end = datetime.now(), 
    _col = 'Adj Close'
):
    # 데이터프레임의 복사본 생성 
    df = _df.copy()
    # try:
    #     _start = datetime.strptime(_start, '%Y-%m-%d')
    #     # 만약에 _end의 타입이 문자라면?
    #     if type(_end) == 'str':
    #         _end = datetime.strptime(_end, '%Y-%m-%d')
    # except:
    #     print('시간의 포멧이 맞지 않습니다. (YYYY-mm-dd)')
    #     return ""
    # Date 가 컬럼에 존재하면 Date를 인덱스로 변경 
    if 'Date' in df.columns:
        df.set_index('Date', inplace = True)
    # 인덱스를 시계열 데이터로 변경 
    df.index = pd.to_datetime(df.index)
    # 결측치와 무한대 값 제거
    flag = df.isin([np.nan, np.inf, -np.inf]).any(axis=1)
    df = df.loc[~flag, ]
    try :
        df = df.loc[_start : _end, [_col]]
    except Exception as e:
        print(e)
        print('입력 된 인자값이 잘못되었습니다.')
        return ""
    # 일별 수익율 계산하여 rtn 컬럼에 대입
    df['rtn'] = (df[_col].pct_change() + 1).fillna(1)
    # 누적 수익율 계산하여 acc_rtn 컬럼에 대입 
    df['acc_rtn'] = df['rtn'].cumprod()
    acc_rtn = df.iloc[-1, -1]
    # 결과 데이터프레임과 최종 누적수익율을 되돌려준다. 
    return df, acc_rtn