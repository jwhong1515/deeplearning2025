import pyupbit
import pandas as pd
import time

# --- 설정 ---
ACCESS_KEY = "YOUR_ACCESS_KEY"  # 발급받은 Access Key
SECRET_KEY = "YOUR_SECRET_KEY"  # 발급받은 Secret Key
TICKER = "KRW-BTC"  # 거래할 코인 티커
INTERVAL = "minute15"  # 15분봉
SHORT_MA = 5  # 단기 이동평균선
LONG_MA = 20  # 장기 이동평균선
INVESTMENT_KRW = 5000  # 1회 투자 금액 (최소 주문 금액 이상)

# --- 업비트 로그인 ---
try:
    upbit = pyupbit.Upbit(ACCESS_KEY, SECRET_KEY)
    my_balance = upbit.get_balance("KRW")
    print(f"로그인 성공! 보유 원화: {my_balance:,.0f} KRW")
except Exception as e:
    print(f"로그인 실패: {e}")
    exit()

def get_moving_averages(ticker, interval):
    """지정된 티커와 간격으로 이동평균선을 계산합니다."""
    df = pyupbit.get_ohlcv(ticker, interval=interval, count=LONG_MA + 5)
    if df is None:
        return None, None
    
    ma_short = df['close'].rolling(window=SHORT_MA).mean()
    ma_long = df['close'].rolling(window=LONG_MA).mean()
    return ma_short, ma_long

def check_and_order():
    """골든크로스/데드크로스 확인 후 주문을 실행합니다."""
    ma_short, ma_long = get_moving_averages(TICKER, INTERVAL)
    
    if ma_short is None or ma_long is None:
        print("이동평균선 계산에 실패했습니다.")
        return

    # 최신 데이터 (바로 전 캔들)
    last_short_ma = ma_short.iloc[-2]
    last_long_ma = ma_long.iloc[-2]
    
    # 그 이전 데이터
    prev_short_ma = ma_short.iloc[-3]
    prev_long_ma = ma_long.iloc[-3]

    btc_balance = upbit.get_balance(TICKER.split('-')[1])

    # 골든크로스: 단기 이평선이 장기 이평선을 아래에서 위로 돌파
    if prev_short_ma < prev_long_ma and last_short_ma > last_long_ma:
        krw_balance = upbit.get_balance("KRW")
        if krw_balance > INVESTMENT_KRW:
            print("📈 골든크로스 발생! 매수를 시도합니다.")
            result = upbit.buy_market_order(TICKER, INVESTMENT_KRW * 0.9995) # 수수료 고려
            print("매수 주문 결과:", result)
        else:
            print("원화 잔고가 부족하여 매수할 수 없습니다.")

    # 데드크로스: 단기 이평선이 장기 이평선을 위에서 아래로 돌파
    elif prev_short_ma > prev_long_ma and last_short_ma < last_long_ma:
        if btc_balance > 0.00008: # 최소 판매 수량 이상일 때
            print("📉 데드크로스 발생! 매도를 시도합니다.")
            result = upbit.sell_market_order(TICKER, btc_balance)
            print("매도 주문 결과:", result)
        else:
            print("보유한 코인이 없어 매도할 수 없습니다.")
    else:
        print("매매 조건이 충족되지 않았습니다.")


# --- 메인 루프 ---
print("자동 거래 봇을 시작합니다. (종료: Ctrl+C)")
while True:
    try:
        check_and_order()
        time.sleep(60)  # 1분마다 체크
    except Exception as e:
        print(f"오류 발생: {e}")
        time.sleep(60)
