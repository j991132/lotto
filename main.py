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
import datetime # 날짜 계산을 위해 추가

# --- 데이터 수집 함수 ---
# 최신 회차 번호를 가져오는 헬퍼 함수
@st.cache_data(ttl=datetime.timedelta(hours=1)) # 1시간마다 최신 회차 정보 갱신
def get_latest_drw_no():
    base_url = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo="
    try:
        response = requests.get(base_url + "1") # 아무 회차나 요청하여 최신 회차 번호 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        latest_drw_no_str = soup.find('strong', class_='drwNo').text
        return int(latest_drw_no_str)
    except Exception as e:
        st.error(f"최신 회차 번호를 가져오는 데 실패했습니다: {e}. 기본값 1122 사용.")
        return 1122 # 실패 시 임의의 최신 회차 (수동 업데이트 필요)

# 지정된 범위의 로또 데이터를 로드하는 함수 (캐싱 적용)
@st.cache_data(ttl=datetime.timedelta(days=1)) # 하루에 한 번만 데이터 로드 (자정 기준)
def load_lotto_data_range(start_drw_no, end_drw_no):
    base_url = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo="
    all_data = []
    
    st.info(f"{start_drw_no}회차부터 {end_drw_no}회차까지의 데이터를 불러오는 중입니다. 잠시 기다려 주세요...")

    for drw_no in range(start_drw_no, end_drw_no + 1):
        url = base_url + str(drw_no)
        try:
            response = requests.get(url, timeout=5) # 5초 타임아웃 설정
            response.raise_for_status() # HTTP 오류 발생 시 예외 발생
            soup = BeautifulSoup(response.text, 'html.parser')

            numbers = []
            for i in range(1, 7):
                num_tag = soup.find('span', class_=f'drw no{i}')
                if num_tag:
                    numbers.append(int(num_tag.text))
                else:
                    raise ValueError(f"번호{i} 태그를 찾을 수 없습니다.") # 번호 태그 없으면 오류
            
            bonus_num_tag = soup.find('span', class_='drwBonus no7')
            if bonus_num_tag:
                bonus_num = int(bonus_num_tag.text)
            else:
                raise ValueError("보너스 번호 태그를 찾을 수 없습니다.")

            date_str_tag = soup.find('p', class_='desc')
            if date_str_tag:
                date_str = date_str_tag.text.split('(')[0].strip()
            else:
                raise ValueError("날짜 태그를 찾을 수 없습니다.")
            
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
        except requests.exceptions.RequestException as req_err:
            st.warning(f"{drw_no}회차 데이터 요청 중 오류 발생 (네트워크 또는 서버): {req_err}")
            pass
        except (AttributeError, ValueError) as parse_err:
            st.warning(f"{drw_no}회차 데이터 파싱 중 오류 발생 (사이트 구조 변경?): {parse_err}")
            pass
        except Exception as e:
            st.warning(f"{drw_no}회차 데이터를 가져오는 중 알 수 없는 오류 발생: {e}")
            pass
            
    df = pd.DataFrame(all_data)
    if not df.empty:
        df['날짜'] = pd.to_datetime(df['날짜'])
    return df

# --- 데이터 분석 및 시각화 함수 ---
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

# --- 예측 모델 함수 (간단한 예시) ---
def predict_lotto_numbers(df_for_prediction):
    st.subheader("📊 지난 당첨 번호 데이터 분석 (예측 근거)")

    # 모든 당첨 번호를 하나의 리스트로 통합
    all_winning_numbers = []
    for _, row in df_for_prediction.iterrows():
        all_winning_numbers.extend(row['당첨번호'])

    if not all_winning_numbers:
        st.warning("예측을 위한 충분한 데이터가 없습니다. 더 많은 당첨 번호 데이터를 로드해주세요.")
        return []

    # 각 숫자의 출현 빈도 계산
    number_counts = pd.Series(all_winning_numbers).value_counts().sort_index()
    
    st.write("**👉 분석 대상 기간 전체 출현 빈도:**")
    st.dataframe(number_counts.reset_index().rename(columns={'index': '숫자', 0: '빈도'}))

    # 최근 회차 데이터만 사용하여 패턴 분석 (예: 분석 대상 기간의 최근 20% 데이터)
    recent_count_for_pred = max(100, int(len(df_for_prediction) * 0.2)) # 최소 100회차 또는 20%
    recent_df_for_pred = df_for_prediction.tail(recent_count_for_pred) 
    recent_winning_numbers = []
    for _, row in recent_df_for_pred.iterrows():
        recent_winning_numbers.extend(row['당첨번호'])
    
    recent_number_counts = pd.Series(recent_winning_numbers).value_counts().sort_index() if recent_winning_numbers else pd.Series()

    if not recent_number_counts.empty:
        st.write(f"**👉 최근 {recent_count_for_pred}회차 출현 빈도:**")
        st.dataframe(recent_number_counts.reset_index().rename(columns={'index': '숫자', 0: '빈도'}))
    else:
        st.info(f"최근 {recent_count_for_pred}회차 데이터가 부족하여 최근 출현 빈도를 분석할 수 없습니다.")

    # 번호 그룹화 (K-Means Clustering)
    if len(number_counts) > 0: # 숫자가 있는 경우에만 클러스터링 시도
        X = number_counts.values.reshape(-1, 1)
        try:
            kmeans = KMeans(n_clusters=min(len(number_counts), 3), random_state=42, n_init=10) # 클러스터 개수 조정
            kmeans.fit(X)
            number_counts_with_cluster = number_counts.reset_index().rename(columns={'index': '숫자', 0: '빈도'})
            number_counts_with_cluster['cluster'] = kmeans.labels_
            st.write("**👉 숫자의 빈도 기반 클러스터링 (저빈도/중빈도/고빈도):**")
            st.dataframe(number_counts_with_cluster.sort_values(by='cluster'))
        except Exception as e:
            st.warning(f"클러스터링 중 오류 발생 (데이터 부족?): {e}")
    else:
        st.warning("클러스터링을 위한 충분한 숫자 데이터가 없습니다.")

    # 예측 로직 (매우 간단한 예시)
    predicted_sets = []
    available_numbers = list(range(1, 46))
    
    for _ in range(5): # 5세트 예측
        weights = np.zeros(46)
        for num in available_numbers:
            overall_freq = number_counts.get(num, 0)
            recent_freq = recent_number_counts.get(num, 0) if not recent_number_counts.empty else 0
            
            # 가중치 부여 (조정 가능)
            # 최근 데이터가 중요하다고 가정하고 가중치 부여
            weights[num-1] = (overall_freq * 0.4) + (recent_freq * 0.6) + 1 # +1은 0 빈도 방지
            
        # 가중치에 따라 6개 숫자 선택
        # random.choices는 중복을 허용하므로 set으로 중복 제거 후 다시 채움
        predicted_numbers_raw = random.choices(available_numbers, weights=weights[np.array(available_numbers)-1], k=6)
        
        predicted_numbers = sorted(list(set(predicted_numbers_raw)))
        
        # 6개 숫자가 안되면 (중복 제거로 인해) 다시 뽑기
        while len(predicted_numbers) < 6:
            # 아직 뽑히지 않은 숫자들 중에서 높은 가중치로 다시 뽑기
            remaining_numbers = list(set(available_numbers) - set(predicted_numbers))
            if not remaining_numbers: # 모든 숫자가 뽑혔다면 (극히 드물겠지만)
                break
            
            additional_num = random.choices(remaining_numbers, 
                                             weights=weights[np.array(remaining_numbers)-1], k=1)[0]
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

    latest_drw_no = get_latest_drw_no()

    # --- 초기 로딩: 최근 100회차 데이터 ---
    initial_start_drw = max(1, latest_drw_no - 99) # 최소 1회차부터
    initial_df = load_lotto_data_range(initial_start_drw, latest_drw_no)
    
    # 세션 상태에 현재 로드된 데이터 저장
    if 'current_df' not in st.session_state:
        st.session_state.current_df = initial_df
        st.session_state.current_data_range = f"{initial_start_drw}회차 ~ {latest_drw_no}회차 (최근 100회차)"
        st.session_state.is_full_data_loaded = False
    
    st.sidebar.header("🔍 데이터 로딩 및 분석 옵션")

    # 전체 데이터 로드 버튼
    if not st.session_state.is_full_data_loaded:
        if st.sidebar.button("전체 기간 데이터 로드 (오래 걸림!)"):
            with st.spinner("전체 로또 당첨 번호 데이터를 로드하는 중입니다..."):
                full_df = load_lotto_data_range(1, latest_drw_no)
                st.session_state.current_df = full_df
                st.session_state.current_data_range = f"1회차 ~ {latest_drw_no}회차 (전체 기간)"
                st.session_state.is_full_data_loaded = True
                st.rerun() # 데이터 로드 후 앱 다시 렌더링
    else:
        st.sidebar.success(f"현재 로드된 데이터: {st.session_state.current_data_range}")
        
    df = st.session_state.current_df

    if df.empty:
        st.error("로또 당첨 번호 데이터를 로드하는 데 실패했습니다. 잠시 후 다시 시도해주세요.")
        return

    st.sidebar.markdown("---")
    st.sidebar.subheader("특정 기간 데이터 분석")

    # 회차 범위 선택 슬라이더
    min_drw_loaded = df['회차'].min()
    max_drw_loaded = df['회차'].max()

    selected_drw_range = st.sidebar.slider(
        "분석할 회차 범위 선택",
        min_value=min_drw_loaded,
        max_value=max_drw_loaded,
        value=(min_drw_loaded, max_drw_loaded) # 기본값은 현재 로드된 데이터의 전체 범위
    )
    
    df_filtered_by_range = df[(df['회차'] >= selected_drw_range[0]) & 
                              (df['회차'] <= selected_drw_range[1])]

    # 년, 월, 주 선택 (회차 범위 필터링 후)
    st.sidebar.subheader("주차별 당첨 번호 검색")
    
    if not df_filtered_by_range.empty:
        min_year_filtered = df_filtered_by_range['날짜'].dt.year.min()
        max_year_filtered = df_filtered_by_range['날짜'].dt.year.max()

        selected_year_for_week = st.sidebar.slider("년도 선택", min_year_filtered, max_year_filtered, max_year_filtered)
        
        # 선택된 년도에 해당하는 월만 필터링
        available_months = sorted(df_filtered_by_range[df_filtered_by_range['날짜'].dt.year == selected_year_for_week]['날짜'].dt.month.unique())
        if available_months:
            selected_month_for_week = st.sidebar.slider("월 선택", min(available_months), max(available_months), max(available_months))
            
            # 선택된 년/월/회차 범위에 해당하는 회차 번호 목록 생성
            filtered_by_month_and_range = df_filtered_by_range[
                (df_filtered_by_range['날짜'].dt.year == selected_year_for_week) & 
                (df_filtered_by_range['날짜'].dt.month == selected_month_for_week)
            ]
            
            if not filtered_by_month_and_range.empty:
                drw_no_options = {}
                for index, row in filtered_by_month_and_range.iterrows():
                    drw_no_options[f"{row['회차']}회차 ({row['날짜'].strftime('%Y-%m-%d')})"] = row['회차']
                
                sorted_drw_no_keys = sorted(drw_no_options.keys(), key=lambda x: int(x.split('회차')[0]))

                selected_drw_no_key = st.sidebar.selectbox("주차(회차) 선택", sorted_drw_no_keys)
                selected_drw_no = drw_no_options[selected_drw_no_key]

                st.subheader(f"📅 {selected_year_for_week}년 {selected_month_for_week}월 {selected_drw_no_key} 당첨 번호")
                
                current_week_data = df_filtered_by_range[df_filtered_by_range['회차'] == selected_drw_no]
                if not current_week_data.empty:
                    st.write(f"**날짜:** {current_week_data['날짜'].dt.strftime('%Y-%m-%d').iloc[0]}")
                    st.write(f"**당첨 번호:** {', '.join(map(str, current_week_data[['번호1', '번호2', '번호3', '번호4', '번호5', '번호6']].iloc[0]))}")
                    st.write(f"**보너스 번호:** {current_week_data['보너스번호'].iloc[0]}")
                else:
                    st.warning("선택된 주차(회차)에 해당하는 데이터가 없습니다.")
            else:
                st.warning("선택된 년/월/회차 범위에 해당하는 당첨 번호 데이터가 없습니다.")
        else:
            st.warning("선택된 년도에 해당하는 월 데이터가 없습니다.")
    else:
        st.warning("선택된 회차 범위에 해당하는 당첨 번호 데이터가 없습니다.")


    st.sidebar.markdown("---")
    st.sidebar.subheader("막대 그래프 분석")
    analysis_period = st.sidebar.radio(
        "막대 그래프 분석 기간",
        ('선택된 회차 범위', '선택된 년도', '선택된 월') # '전체 기간'은 이제 전체 데이터 로드 후 가능
    )

    st.subheader("📊 당첨 번호 출현 빈도 막대 그래프")

    if analysis_period == '선택된 회차 범위':
        plot_frequency(df_filtered_by_range, f"{selected_drw_range[0]}회차 ~ {selected_drw_range[1]}회차 로또 당첨 번호 출현 빈도")
    elif analysis_period == '선택된 년도':
        # 회차 범위로 필터링된 데이터에서 다시 년도 필터링
        df_year = df_filtered_by_range[df_filtered_by_range['날짜'].dt.year == selected_year_for_week]
        plot_frequency(df_year, f"{selected_year_for_week}년 로또 당첨 번호 출현 빈도 (선택된 회차 범위 내)")
    elif analysis_period == '선택된 월':
        # 회차 범위로 필터링된 데이터에서 다시 월 필터링
        df_month = df_filtered_by_range[
            (df_filtered_by_range['날짜'].dt.year == selected_year_for_week) & 
            (df_filtered_by_range['날짜'].dt.month == selected_month_for_week)
        ]
        plot_frequency(df_month, f"{selected_year_for_week}년 {selected_month_for_week}월 로또 당첨 번호 출현 빈도 (선택된 회차 범위 내)")


    st.markdown("---")
    st.header("🔮 이번 주 1등 당첨번호 예측 (5세트)")
    st.info("""
    **참고:** 이 예측은 현재 **'분석할 회차 범위'**에 선택된 데이터만을 기반으로 한 통계적 경향 분석입니다. 
    로또 당첨 번호는 기본적으로 무작위이며, 어떤 예측 모델도 100% 정확한 당첨을 보장할 수 없습니다. 
    단순히 재미로 활용해 주세요!
    """)
    
    if st.button("이번 주 예측 번호 생성"):
        with st.spinner("예측 번호를 생성 중입니다..."):
            # 예측은 현재 필터링된 데이터 (df_filtered_by_range)를 기반으로 합니다.
            predicted_sets = predict_lotto_numbers(df_filtered_by_range)
            if predicted_sets:
                for i, s in enumerate(predicted_sets):
                    st.success(f"**예측 세트 {i+1}:** {', '.join(map(str, s))}")
            else:
                st.warning("예측 번호를 생성할 수 없습니다. 분석할 데이터가 충분한지 확인해주세요.")

if __name__ == "__main__":
    main()
