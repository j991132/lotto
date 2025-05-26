import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# 더미 데이터 생성 (실제 데이터로 대체 필요)
def create_dummy_data():
    dates = pd.date_range(start="2020-01-01", end="2025-05-24", freq="W-SAT")
    data = []
    np.random.seed(42)
    for date in dates:
        numbers = np.random.choice(range(1, 46), size=6, replace=False)
        data.append([date, *sorted(numbers)])
    return pd.DataFrame(data, columns=["Date", "Num1", "Num2", "Num3", "Num4", "Num5", "Num6"])

# 데이터 로드 (실제 데이터 소스 사용 시 수정)
@st.cache_data
def load_data():
    return create_dummy_data()

# 번호 빈도 분석
def analyze_number_frequency(df, start_date=None, end_date=None):
    if start_date and end_date:
        df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    numbers = df[["Num1", "Num2", "Num3", "Num4", "Num5", "Num6"]].values.flatten()
    freq = pd.Series(numbers).value_counts().sort_index()
    freq_df = pd.DataFrame({"Number": freq.index, "Frequency": freq.values})
    return freq_df

# 번호 예측 (빈도 기반 단순 예측)
def predict_numbers(df, n_sets=5):
    freq_df = analyze_number_frequency(df)
    top_numbers = freq_df.sort_values("Frequency", ascending=False)["Number"].head(10).values
    predictions = []
    np.random.seed(42)
    for _ in range(n_sets):
        pred = np.random.choice(top_numbers, size=6, replace=False)
        predictions.append(sorted(pred))
    return predictions

# 스트림릿 앱
st.title("로또 1등 당첨번호 분석기")

# 데이터 로드
df = load_data()

# 지난 주 당첨번호 표시
last_week = df.iloc[-1]
st.subheader("지난 주 (최신 회차) 1등 당첨번호")
st.write(f"날짜: {last_week['Date'].strftime('%Y-%m-%d')}")
st.write(f"번호: {', '.join(map(str, last_week[['Num1', 'Num2', 'Num3', 'Num4', 'Num5', 'Num6']].values))}")

# 기간 선택
st.subheader("기간별 당첨번호 검색 및 분석")
col1, col2, col3 = st.columns(3)
with col1:
    year = st.selectbox("년도", sorted(df["Date"].dt.year.unique()), index=len(df["Date"].dt.year.unique())-1)
with col2:
    month = st.selectbox("월", range(1, 13), index=datetime.now().month-1)
with col3:
    weeks = df[df["Date"].dt.year == year][df["Date"].dt.month == month]["Date"].dt.isocalendar().week.unique()
    week = st.selectbox("주차", sorted(weeks))

# 선택된 기간의 데이터 필터링
start_date = pd.to_datetime(f"{year}-{month}-01")
end_date = start_date + pd.offsets.MonthEnd(0)
if week:
    week_dates = df[(df["Date"].dt.year == year) & (df["Date"].dt.month == month) & (df["Date"].dt.isocalendar().week == week)]
    if not week_dates.empty:
        st.subheader(f"{year}년 {month}월 {week}주차 당첨번호")
        for _, row in week_dates.iterrows():
            st.write(f"날짜: {row['Date'].strftime('%Y-%m-%d')} | 번호: {', '.join(map(str, row[['Num1', 'Num2', 'Num3', 'Num4', 'Num5', 'Num6']].values))}")
    else:
        st.warning("선택한 주차에 데이터가 없습니다.")

# 번호 빈도 그래프
freq_df = analyze_number_frequency(df, start_date, end_date)
fig = px.bar(freq_df, x="Number", y="Frequency", title=f"{year}년 {month}월 번호별 당첨 횟수")
fig.update_layout(xaxis=dict(tickmode="linear", tick0=1, dtick=1))
st.plotly_chart(fig)

# 예측 번호
st.subheader("이번 주 예측 번호 (빈도 기반)")
predictions = predict_numbers(df)
for i, pred in enumerate(predictions, 1):
    st.write(f"예측 {i}세트: {', '.join(map(str, pred))}")

st.info("참고: 예측 번호는 과거 데이터의 빈도 분석을 기반으로 하며, 실제 당첨을 보장하지 않습니다. 데이터는 더미 데이터로 생성되었으며, 실제 구현 시 동행복권 공식 데이터를 사용해야 합니다.")[](https://dhlottery.co.kr/gameResult.do?method=statIndex)
