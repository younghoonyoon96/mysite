# __init__.py는 해당하는 파일이 있는 폴더를 호출할 때 자동적으로 실행
import invest.buyandhold as bnh
import invest.bollinger as boll
import invest.halloween as hall
import invest.momentum as mmt
from datetime import datetime
import pandas as pd
import yfinance as yf

# 야후파이낸스 라이브러리 이용해서 데이터 로드
def load_data(_ticker,
              _start = '2010-01-01',
              _end = datetime.now()):
    Ticker = yf.Ticker(_ticker)
    result = Ticker.history(start = _start, end = _end)
    return result


# Quant Class 생성
class Quant:
    # 생성자 함수 -> 데이터프레임, 투자의 시작시간, 종료시간, 기준이되는 컬럼
    def __init__(self,
                _df,
                _start = '2010-01-01',
                _end = datetime.now(),
                _col = 'Adj Close'):
        if 'Date'in _df.columns:
            _df.set_index('Date', inplace=True)
        # 인덱스를 시계열 변환하면서 tz 설정
        _df.index = pd.to_datetime(_df.index, utc=True)
        try:
            # tz를 제거
            _df.index = _df.index.tz_localize(None)
        except Exception as e:
            print(e)
        self.df = _df
        self.start = _start
        self.end = _end
        self.col = _col
    # 투자 전략 4가지의 함수를 생성
    def buyandhold(self):
        df, acc_rtn = bnh.bnh(self.df, self.start, self.end, self.col)
        print(f'Buy&Hold 최종수익률: {acc_rtn}')
        return df, acc_rtn
    
    def bollinger(self, cnt = 20):
        # cnt: 이동평균선에서 사용할 일자
        band_df = boll.create_band(self.df, self.start, self.end, self.col, cnt)
        trade_df = boll.create_trade(band_df)
        trade_df['trade'].fillna('', inplace=True)
        df, acc_rtn = boll.create_rtn(trade_df)
        print(f'Bollinger Band 최종수익률 : {acc_rtn}')
        return df, acc_rtn
    
    def halloween(self, month = 11):
        df, acc_rtn = hall.six_month(self.df, self.start, self.end, self.col, month)
        print(f'Halloween 최종수익률 : {acc_rtn}')
        return df, acc_rtn
    
    def momentum(self, _momentum = 12, _score = 1):
        ym_df = mmt.create_YM(self.df, self.col)
        month_df = mmt.create_last_month(ym_df, self.start, self.end, _momentum)
        df, acc_rtn = mmt.create_rtn(ym_df, month_df, self.start, self.end, _score)
        print(f'Momentum 최종수익률: {acc_rtn}')
        return df, acc_rtn