import pandas as pd
import os
from glob import glob
from datetime import datetime

def create_1m_rtn(
        _df,
        _ticker,
        _start = '2010-01-01',
        _end = datetime.now(),
        _col = 'Adj Close'
):
    # 복사본 생성
    df = _df.copy()
    # 'Date'가 컬럼에 존재하면 인덱스로 변환
    if 'Date' in df.columns:
        df.set_index('Date', inplace = True)
    # 인덱스를 시계열 변환
    df.index = pd.to_datetime(df.index)
    # 투자의 시작시간과 종료시간으로 인덱스 필터링
    # 기준이 되는 컬럼으로 컬럼 필터링
    df= df.loc[_start : _end, [_col]]
    df['STD-YM'] = df.index.strftime('%Y-%m')
    # 월별 수익율 컬럼을 생성
    df['1m_rtn'] = 0
    # ticker를 컬럼에 대입
    df['CODE'] = _ticker
    # 기준년월의 유니크값을 생성
    ym_list = df['STD-YM'].unique()
    return df, ym_list

# 데이터를 로드하고 월별 수익율을 계산하여 새로운 데이터프레임에 추가하는 함수
def data_load(
        _path = './data',
        _ext = 'csv',
        _start = '2010-01-01',
        _end = datetime.now(),
        _col = 'Adj Close'
):
    files = glob(f'{_path}/*.{_ext}')
    stock_df = pd.DataFrame()
    month_last_df = pd.DataFrame()

    # files를 이용해서 반복문 생성
    for file in files:
        # file: 특정 경로와 파일명
        # print(file)
        # 경로와 파일명을 나눠준다 -> os 경로에있는 스플릿 함수
        folder, name = os.path.split(file)
        # 파일명에서 이름과 확장자로 나눠준다.
        head, tail = os.path.splitext(name)
        # head는 create_1m_rtn()에서 _ticker 매개변수의 인자값

        # 데이터프레임 로드
        read_df = pd.read_csv(file)
        # 함수 호출
        price_df, ym_list = create_1m_rtn(read_df, head, _start, _end, _col)
        # price_df를 stock_df에 단순 행 결합
        stock_df = pd.concat([stock_df, price_df], axis=0)

        # 두번째 반복문 생성
        # 월별 수익률을 계산하여 대입
        for ym in ym_list:
            # ym : 기준년월
            # 월초의 가격(매수)
            buy = price_df.loc[ym,].iloc[0,0]
            # 월말의 가격(매도)
            sell = price_df.loc[ym,].iloc[-1,0]
            # 수익율 생성
            rtn = sell / buy
            # 수익율 대입
            price_df.loc[ym, '1m_rtn'] = rtn
            # 월말의 데이터를 month_lsat_df에 단순 행 결합
            last_df = price_df.loc[ym, ['CODE', '1m_rtn']].tail(1)
            month_last_df = pd.concat([month_last_df, last_df], axis=0)
    return stock_df, month_last_df

# 구매 포지션을 잡아주는 함수 생성
def create_position(
        _df,
        _pct = 0.4
):
    # 복사본 생성
    month_rtn_df = _df.copy()
    # _pct의 값이 1보다 크거나 같은 숫자라면 100으로 나눠준다.
    if _pct >= 1:
        _pct = _pct / 100
    # 인덱스 리셋
    month_rtn_df.reset_index(inplace=True)
    # 테이블을 재구조화
    month_rtn_df = month_rtn_df.pivot_table(
        index = 'Date',
        columns= 'CODE',
        values= '1m_rtn'
    )
    # month_rtn_df의 데이터들을 랭크화(열의 값들을 이용)
    month_rtn_df = month_rtn_df.rank(axis=1, ascending= False, pct= True)
    # where() 함수를 사용
    # where(조건식, 거짓일 때 대입될 데이터) -> replace랑 반대의 개념
    month_rtn_df = month_rtn_df.where(month_rtn_df <= _pct, 0)
    month_rtn_df[month_rtn_df != 0] = 1
    # stock_df의 code의 unique()를 변수에 저장 
    stock_codes = list(month_rtn_df.columns)

    # 해당 일자의 구매하려는 종목들을 딕셔너리로 생성
    sig_dict = dict()

    for idx in month_rtn_df.index:
        # idx: month_rtn_df의 인덱스들 (시계열)
        flag_col = month_rtn_df.loc[idx, ] == 1
        ticker_list = list(
            month_rtn_df.loc[idx, flag_col].index
        )
        # sig_dict에 추가
        sig_dict[idx] = ticker_list
    return sig_dict, stock_codes

# 거래내역 컬럼을 추가하는 함수 생성
def create_trade_book(_df, _codes, _sig_dict):
    # 복사본 생성
    df = _df.copy()
    # stock_df를 재구조화
    df = _df.reset_index().pivot_table(
        index = 'Date',
        columns= 'CODE',
        values= _df.columns[0]
    )
    for code in _codes:
        df[f'p_{code}'] = ''
        df[f'r_{code}'] = ''
    # sig_dict를 이용해서 구매 전 준비내역을 추가
    for date, codes in _sig_dict.items():
        # date: key -> 시계열 데이터(말 일 데이터)
        # codes: value -> 종목 리스트
        # codes 반복문 생성
        for code in codes:
            # print(code)
            # book에서 인덱스가 date인 컬럼이 r_code인 컬럼에 준비 내역을 추가
            df.loc[date, f'p_{code}'] = f'ready_{code}'
    return df


# 보유 내역을 추가하는 함수 생성
def create_trading(_df, _codes):
    buy_phase = False
    df = _df.copy()
    std_ym = ''

    # _codes: 종목 리스트 -> 컬럼의 이름들 
    # 종목별로 순회(컬럼)하는 반복문 생성
    for code in _codes: # 10번 반복
        # 인덱스를 기준으로 반복문 생성
        for idx in df.index:
            # 특정 종목의 포지션을 잡는다.
            # 전 행의 p_code 컬럼이 ready이고 현재 행의 p_code인 컬럼에 준비 내역을 추가
            if (df.loc[idx, f'p_{code}'] == '') & (df.shift().loc[idx,f'p_{code}'] == f'ready_{code}'):
                std_ym = idx.strftime('%Y-%m')
                buy_phase = True
             # 구매 조건: (현재 p_code가 ''인 상태)이고 (index의 년도-월과 std_ym이 같고) buy_phase
            if (df.loc[idx, f'p_{code}'] == '') & (std_ym == idx.strftime('%Y-%m')) & (buy_phase):
                df.loc[idx, f'p_{code}'] = f'buy_{code}'
            # buy_phase, std_ym 초기화
            if df.loc[idx, f'p_{code}'] == '':
                buy_phase = False
                std_ym = ''
    return df

# 수익률을 계산하는 함수 생성
def multi_return (_df, _codes):
    # 복사본 생성
    df = _df.copy()
    rtn = 1
    # 매수가 -> dict 형태로 구성
    buy_dict = dict()
    # 매도가 -> dict 형태로 구성
    sell_dict = dict()

    # index를 기준으로 반복문 생성 -> 날짜별 매수, 매도 확인
    for idx in df.index:
        # 종목별로 매수, 매도를 확인
        for code in _codes:
            # 매수의 조건: 2행 전(shift(2))의 p_code가 ''이고 
            #           1행 전(shift())의 p_code가 'ready_code'
            #           현재 행의 p_code가 'buy_code'
            if (df.shift(2).loc[idx, f'p_{code}'] == '')&\
            (df.shift().loc[idx, f'p_{code}'] == f'ready_{code}') &\
            (df.loc[idx, f'p_{code}'] == f'buy_{code}'):
                # 매수가 -> idx 행에 code 컬럼에 존재
                buy_dict[code] = df.loc[idx, code]
                print(f'매수일: {idx}, 매수종목: {code}, 매수가: {df.loc[idx,code]}')
    # 매도의 조건: 1행 전의 p_code가 buy_code
    #           현재행의 p_code가 ''
            elif (df.shift().loc[idx,f'p_{code}'] == f'buy_{code}') &\
                (df.loc[idx, f'p_{code}'] == ''):
                # 매도가 -> idx 행에 code 컬럼에 존재
                sell_dict[code] = df.loc[idx, code]
                # 수익률 계산
                rtn = sell_dict[code] / buy_dict[code]
                df.loc[idx, f'r_{code}'] = rtn
                print(f'매도일: {idx}, 매도종목: {code}, 매도가: {sell_dict[code]}, 수익률: {rtn}')
                # buy_dict, sell_dict의 code안에 매수가 매도가 초기화
                if df.loc[idx, f'p_{code}'] == '':
                    buy_dict[code] == 0
                    sell_dict[code] == 0
    return df

# 누적수익률 계산
def multi_acc_rtn(_df, _codes):
    # 복사본 생성
    df = _df.copy()
    acc_rtn = 1

    # 인덱스를 기준으로 반복문 생성
    for idx in df.index:
        count = 0
        rtn = 0
        for code in _codes:
            # 수익률이 존재하는가?
            if df.loc[idx, f'r_{code}']:
                # 존재하는 경우
                count += 1
                rtn += df.loc[idx, f'r_{code}']
        if (rtn != 0) & (count != 0):
            acc_rtn *= rtn / count
            print(f'누적 - 매도일: {idx}, 매도 종목수 : {count}, 수익율: {round(rtn / count, 2)}')
        df.loc[idx, 'acc_rtn'] = acc_rtn
    return df, acc_rtn