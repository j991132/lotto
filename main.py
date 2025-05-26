import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
from bs4 import BeautifulSoup
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
import random

# --- 1. 데이터 수집 함수 ---
@st.cache_data
def load_lotto_data():
    base_url = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo="
    all_data = []
    
    # 1회차부터 최신 회차까지 데이터 가져오기 (시간이 오래 걸릴 수 있음)
    # 실제 사용 시에는 최신 회차 번호를 동적으로 가져오는 로직 추가 필요
    # 예: 첫 페이지에서 최신 회차 번호 파싱 후 반복문 범위 설정
    
    # 예시: 최근 500회차만 가져오기 (실제로는 더 많은 데이터 필요)
    # 최신 회차 번호를 동적으로 가져오는 함수를 구현하는 것이 좋습니다.
    # 현재는 수동으로 최대 회차를 설정합니다.
    
    # 최신 회차 번호 가져오기 (동행복권 웹사이트에서 파싱)
    try:
        response = requests.get(base_url + "1") # 아무 회차나 요청하여 최신 회차 번호 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        latest_drw_no_str = soup.find('strong', class_='drwNo').text
        latest_drw_no = int(latest_drw_no_str)
    except Exception as e:
        st.error(f"최신 회차 번호를 가져오는 데 실패했습니다: {e}")
        latest_drw_no = 1122 # 실패 시 임의의 최신 회차 (업데이트 필요)

    for drw_no in range(1, latest_drw_no + 1): # 1회차부터 최신 회차까지
        url = base_url + str(drw_no)
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 당첨 번호
            numbers = []
            for i in range(1, 7):
                num = soup.find('span', class_=f'drw no{i}').text
                numbers.append(int(num))
            
            bonus_num = int(soup.find('span', class_='drwBonus no7').text)
            
            # 당첨일자
            date_str = soup.find('p', class_='desc').text.split('(')[0].strip()
            
            all_data.append({
                '회차': drw_no,
                '날짜': date_str,
                '번호1': numbers[0],
                '번호2': numbers[1],
                '번호3': numbers[2],
                '번호4': numbers[3],
                '번호5': numbers[4],
                '번호6': numbers[5],
                '보너스번호': bonus_num,
                '당첨번호': sorted(numbers) # 정렬된 당첨 번호 리스트
            })
        except AttributeError:
            # 데이터가 없는 회차이거나 파싱 오류
            pass
        except Exception as e:
            st.warning(f"{drw_no}회차 데이터를 가져오는 중 오류 발생: {e}")
            pass
            
    df = pd.DataFrame(all_data)
    df['날짜'] = pd.to_datetime(df['날짜'])
    return df

# --- 2. 데이터 분석 및 시각화 함수 ---
def plot_frequency(df, title):
    all_numbers = []
    for _, row in df.iterrows():
        all_numbers.extend(row['당첨번호']) # '당첨번호' 리스트 사용

    if not all_numbers:
        st.warning("선택된 기간에 당첨 번호 데이터가 없습니다.")
        return

    freq_df = pd.Series(all_numbers).value_counts().sort_index()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    freq_df.plot(kind='bar', ax=ax, color='skyblue')
    ax.set_title(title, fontsize=16)
    ax.set_xlabel('숫자', fontsize=14)
    ax.set_ylabel('출현 빈도', fontsize=14)
    ax.set_xticks(np.arange(0, 45, 5)) # 0부터 44까지 5단위로 x축 눈금 설정
    ax.set_xticklabels(np.arange(1, 46, 5)) # 1부터 45까지 5단위로 x축 레이블 설정
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    st.pyplot(fig)

# --- 3. 예측 모델 함수 (간단한 예시) ---
# 이 부분은 더욱 정교한 모델로 개선될 수 있습니다.
def predict_lotto_numbers(df):
    st.subheader("📊 지난 당첨 번호 데이터 분석 (예측 근거)")

    # 모든 당첨 번호를 하나의 리스트로 통합
    all_winning_numbers = []
    for _, row in df.iterrows():
        all_winning_numbers.extend(row['당첨번호'])

    if not all_winning_numbers:
        st.warning("예측을 위한 충분한 데이터가 없습니다. 더 많은 당첨 번호 데이터를 로드해주세요.")
        return []

    # 각 숫자의 출현 빈도 계산
    number_counts = pd.Series(all_winning_numbers).value_counts().sort_index()
    
    st.write("**👉 각 숫자의 전체 출현 빈도:**")
    st.dataframe(number_counts.reset_index().rename(columns={'index': '숫자', 0: '빈도'}))

    # 최근 회차 데이터만 사용하여 패턴 분석 (예: 최근 100회차)
    recent_df = df.tail(100) # 최근 100회차 데이터
    recent_winning_numbers = []
    for _, row in recent_df.iterrows():
        recent_winning_numbers.extend(row['당첨번호'])
    
    if recent_winning_numbers:
        recent_number_counts = pd.Series(recent_winning_numbers).value_counts().sort_index()
        st.write("**👉 최근 100회차 출현 빈도:**")
        st.dataframe(recent_number_counts.reset_index().rename(columns={'index': '숫자', 0: '빈도'}))

        # 번호 그룹화 (K-Means Clustering)
        # 예: 숫자를 저빈도/중빈도/고빈도로 클러스터링
        if len(number_counts) > 0: # 숫자가 있는 경우에만 클러스터링 시도
            X = number_counts.values.reshape(-1, 1)
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            kmeans.fit(X)
            number_counts_with_cluster = number_counts.reset_index().rename(columns={'index': '숫자', 0: '빈도'})
            number_counts_with_cluster['cluster'] = kmeans.labels_
            st.write("**👉 숫자의 빈도 기반 클러스터링 (저빈도/중빈도/고빈도):**")
            st.dataframe(number_counts_with_cluster.sort_values(by='cluster'))
        else:
            st.warning("클러스터링을 위한 충분한 숫자 데이터가 없습니다.")
    else:
        st.warning("최근 데이터에서 예측을 위한 충분한 당첨 번호 데이터가 없습니다.")


    # 예측 로직 (매우 간단한 예시)
    # 1. 전체 빈도를 기반으로 가중치 부여
    # 2. 최근 출현 빈도를 더 높은 가중치 부여
    # 3. 이월 가능성이 있는 번호 (최근에 나오지 않았지만 과거 빈도가 높은 번호) 고려

    predicted_sets = []
    available_numbers = list(range(1, 46))
    
    for _ in range(5): # 5세트 예측
        # 각 숫자의 가중치 계산 (전체 빈도 + 최근 빈도)
        weights = np.zeros(46)
        for num in available_numbers:
            overall_freq = number_counts.get(num, 0)
            recent_freq = recent_number_counts.get(num, 0) if recent_winning_numbers else 0
            
            # 가중치 부여 (조정 가능)
            weights[num-1] = overall_freq * 0.7 + recent_freq * 0.3 + 1 # +1은 0 방지

        # 가중치에 따라 6개 숫자 선택
        predicted_numbers = random.choices(available_numbers, weights=weights[np.array(available_numbers)-1], k=6)
        
        # 중복 제거 및 정렬
        predicted_numbers = sorted(list(set(predicted_numbers)))
        
        # 6개 숫자가 안되면 다시 뽑기 (매우 드물겠지만)
        while len(predicted_numbers) < 6:
            additional_num = random.choices(available_numbers, weights=weights[np.array(available_numbers)-1], k=1)[0]
            predicted_numbers.append(additional_num)
            predicted_numbers = sorted(list(set(predicted_numbers)))
        
        predicted_sets.append(predicted_numbers[:6]) # 6개만 선택

    return predicted_sets

# --- Streamlit 앱 메인 로직 ---
def main():
    st.set_page_config(
        page_title="로또 1등 번호 분석 및 예측",
        page_icon="🍀",
        layout="wide"
    )

    st.title("🍀 로또 1등 번호 분석 및 예측 웹 앱")
    st.markdown("""
    **동행복권 로또 1등 당첨 번호를 분석하고, 미래 당첨 번호를 예측해 봅니다.**
    """)

    df = load_lotto_data()

    if df.empty:
        st.error("로또 당첨 번호 데이터를 로드하는 데 실패했습니다. 잠시 후 다시 시도해주세요.")
        return

    st.sidebar.header("🔍 분석 옵션")

    # 년, 월, 주 선택
    st.sidebar.subheader("기간별 당첨 번호 검색")
    
    # 데이터프레임에서 가장 오래된 연도와 최신 연도 찾기
    min_year = df['날짜'].dt.year.min()
    max_year = df['날짜'].dt.year.max()

    selected_year = st.sidebar.slider("년도 선택", min_year, max_year, max_year)
    selected_month = st.sidebar.slider("월 선택", 1, 12, df['날짜'].dt.month.max() if selected_year == max_year else 1)

    # 선택된 년/월에 해당하는 회차 번호 목록 생성
    filtered_by_month = df[(df['날짜'].dt.year == selected_year) & (df['날짜'].dt.month == selected_month)]
    
    if not filtered_by_month.empty:
        # 회차 번호를 기준으로 주차를 대략적으로 계산
        # 실제 '주' 개념은 복잡하므로, 여기서는 회차 번호를 사용하여 유사하게 구현
        min_drw = filtered_by_month['회차'].min()
        max_drw = filtered_by_month['회차'].max()
        
        # 각 회차에 해당하는 날짜 정보를 기준으로 주차를 표시
        drw_no_options = {}
        for index, row in filtered_by_month.iterrows():
            drw_no_options[f"{row['회차']}회차 ({row['날짜'].strftime('%Y-%m-%d')})"] = row['회차']
        
        # 정렬된 옵션 키
        sorted_drw_no_keys = sorted(drw_no_options.keys(), key=lambda x: int(x.split('회차')[0]))

        selected_drw_no_key = st.sidebar.selectbox("주차(회차) 선택", sorted_drw_no_keys)
        selected_drw_no = drw_no_options[selected_drw_no_key]

        st.subheader(f"📅 {selected_year}년 {selected_month}월 {selected_drw_no_key} 당첨 번호")
        
        current_week_data = df[df['회차'] == selected_drw_no]
        if not current_week_data.empty:
            st.write(f"**날짜:** {current_week_data['날짜'].dt.strftime('%Y-%m-%d').iloc[0]}")
            st.write(f"**당첨 번호:** {', '.join(map(str, current_week_data[['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']].iloc[0]))}")
            st.write(f"**보너스 번호:** {current_week_data['보너스번호'].iloc[0]}")
        else:
            st.warning("선택된 주차(회차)에 해당하는 데이터가 없습니다.")
    else:
        st.warning("선택된 년/월에 해당하는 당첨 번호 데이터가 없습니다.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("막대 그래프 분석")
    analysis_period = st.sidebar.radio(
        "분석 기간 선택",
        ('전체 기간', '선택된 년도', '선택된 월')
    )

    st.subheader("📊 당첨 번호 출현 빈도 막대 그래프")

    if analysis_period == '전체 기간':
        plot_frequency(df, "전체 기간 로또 당첨 번호 출현 빈도")
    elif analysis_period == '선택된 년도':
        df_year = df[df['날짜'].dt.year == selected_year]
        plot_frequency(df_year, f"{selected_year}년 로또 당첨 번호 출현 빈도")
    elif analysis_period == '선택된 월':
        df_month = df[(df['날짜'].dt.year == selected_year) & (df['날짜'].dt.month == selected_month)]
        plot_frequency(df_month, f"{selected_year}년 {selected_month}월 로또 당첨 번호 출현 빈도")

    st.markdown("---")
    st.header("🔮 이번 주 1등 당첨번호 예측 (5세트)")
    st.info("""
    **참고:** 이 예측은 과거 데이터의 통계적 경향과 간단한 패턴 분석에 기반한 것입니다. 
    로또 당첨 번호는 기본적으로 무작위이며, 어떤 예측 모델도 100% 정확한 당첨을 보장할 수 없습니다. 
    단순히 재미로 활용해 주세요!
    """)
    
    if st.button("이번 주 예측 번호 생성"):
        with st.spinner("예측 번호를 생성 중입니다..."):
            predicted_sets = predict_lotto_numbers(df)
            if predicted_sets:
                for i, s in enumerate(predicted_sets):
                    st.success(f"**예측 세트 {i+1}:** {', '.join(map(str, s))}")
            else:
                st.warning("예측 번호를 생성할 수 없습니다. 데이터를 확인해주세요.")

if __name__ == "__main__":
    main()
