import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

def six_month(
        _df, 
        _start = '2010-01-01', 
        _end = datetime.now(), 
        _col = 'Adj Close', 
        _month = 11
):
    # 복사본 생성 
    df = _df.copy()
    # Date 컬럼이 존재하는가?
    if 'Date' in df.columns:
        df.set_index('Date', inplace=True)
    # 인덱스를 시계열로 변환
    df.index = pd.to_datetime(df.index)
    # 시작 시간을 시계열 변경 
    start = pd.to_datetime(_start)
    # 종료 시간은 타입이 문자라면 
    if type(_end) == str:
        end = pd.to_datetime(_end)
    else:
        end = _end
    # 빈 데이터 프레임을 생성 
    result = pd.DataFrame()

    for year in range(start.year, end.year):
        # 매수 시간
        buy = datetime(year=year, month=_month, day = 1 )
        # 매도 (매수의 5개월 뒤)
        sell = buy + relativedelta(months=5)

        buy_mon = buy.strftime('%Y-%m')
        sell_mon = sell.strftime('%Y-%m')
        try : 
            start_df = df.loc[buy_mon, [_col]].head(1)
            end_df = df.loc[sell_mon, [_col]].tail(1)
            result = pd.concat(
                [result, start_df, end_df], axis=0
            )
        except:
            break
    # result를 이용하여 수익율 계산
    result['rtn'] = 1
    for idx in range(1, len(result), 2):
        rtn = result.iloc[idx, ][_col] / \
                result.iloc[idx-1, ][_col]
        result.iloc[idx, -1] = rtn
    # 누적 수익율 계산
    result['acc_rtn'] = result['rtn'].cumprod()
    acc_rtn = result.iloc[-1, -1]

    return result, acc_rtn

    