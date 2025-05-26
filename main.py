import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
from bs4 import BeautifulSoup
import datetime

# --- 데이터 수집 함수 ---

# 최신 회차 번호를 가져오는 헬퍼 함수
@st.cache_data(ttl=datetime.timedelta(hours=1)) # 1시간마다 최신 회차 정보 갱신
def get_latest_drw_no():
    base_url = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo="
    try:
        response = requests.get(base_url + "1", timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        latest_drw_no_str = soup.find('strong', class_='drwNo').text
        return int(latest_drw_no_str)
    except Exception as e:
        st.error(f"최신 회차 번호를 가져오는 데 실패했습니다: {e}. 기본값 1122 사용.")
        return 1122 # 실패 시 임의의 최신 회차 (수동 업데이트 필요)

# 단일 회차의 로또 데이터를 로드하는 함수
@st.cache_data(ttl=datetime.timedelta(days=1)) # 하루에 한 번만 캐싱
def load_single_lotto_data(drw_no):
    base_url = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo="
    url = base_url + str(drw_no)
    data = {}
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        numbers = []
        for i in range(1, 7):
            num_tag = soup.find('span', class_=f'drw no{i}')
            if num_tag:
                numbers.append(int(num_tag.text))
            else:
                raise ValueError(f"번호{i} 태그를 찾을 수 없습니다.")
        
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
        
        data = {
            '회차': drw_no,
            '날짜': pd.to_datetime(date_str),
            '번호1': numbers[0],
            '번호2': numbers[1],
            '번호3': numbers[2],
            '번호4': numbers[3],
            '번호5': numbers[4],
            '번호6': numbers[5],
            '보너스번호': bonus_num,
            '당첨번호': sorted(numbers) # 정렬된 당첨 번호 리스트
        }
    except requests.exceptions.RequestException as req_err:
        st.warning(f"{drw_no}회차 데이터 요청 중 오류 발생 (네트워크 또는 서버): {req_err}")
    except (AttributeError, ValueError) as parse_err:
        st.warning(f"{drw_no}회차 데이터 파싱 중 오류 발생 (사이트 구조 변경?): {parse_err}")
    except Exception as e:
        st.warning(f"{drw_no}회차 데이터를 가져오는 중 알 수 없는 오류 발생: {e}")
            
    return data

# 지정된 범위의 로또 데이터를 로드하는 함수 (캐싱 적용)
@st.cache_data(ttl=datetime.timedelta(days=1)) # 하루에 한 번만 데이터 로드 (자정 기준)
def load_lotto_data_range(start_drw_no, end_drw_no):
    base_url = "https://dhlottery.co.kr/gameResult.do?method=byWin&drwNo="
    all_data = []
    
    progress_text = f"{start_drw_no}회차부터 {end_drw_no}회차까지의 데이터를 불러오는 중..."
    my_bar = st.progress(0, text=progress_text)
    
    total_iterations = end_drw_no - start_drw_no + 1
    
    for i, drw_no in enumerate(range(start_drw_no, end_drw_no + 1)):
        url = base_url + str(drw_no)
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            numbers = []
            for j in range(1, 7):
                num_tag = soup.find('span', class_=f'drw no{j}')
                if num_tag:
                    numbers.append(int(num_tag.text))
                else:
                    raise ValueError(f"번호{j} 태그를 찾을 수 없습니다.")
            
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
        
        # 진행 상황 업데이트
        progress_percentage = (i + 1) / total_iterations
        my_bar.progress(progress_percentage, text=f"{progress_text} ({int(progress_percentage*100)}%)")
            
    my_bar.empty() # 진행 바 제거
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

# --- Streamlit 앱 메인 로직 ---
def main():
    st.set_page_config(
        page_title="로또 1등 번호 분석",
        page_icon="🍀",
        layout="centered" # 초기 화면은 centered가 더 깔끔할 수 있습니다.
    )

    st.title("🍀 로또 1등 번호 분석 웹 앱")
    st.markdown("""
    **이번 주 로또 당첨 번호를 확인하고, 지난 당첨 번호의 통계를 분석해 보세요.**
    """)

    latest_drw_no = get_latest_drw_no()

    # --- 1. 초기 화면: 지난 주 로또 1등 당첨번호 표시 ---
    st.header("✨ 지난 주 1등 당첨번호")
    if latest_drw_no > 0:
        previous_drw_no = latest_drw_no - 1
        last_week_data = load_single_lotto_data(previous_drw_no)
        
        if last_week_data:
            st.markdown(f"**{last_week_data['회차']}회차 당첨번호 ({last_week_data['날짜'].strftime('%Y-%m-%d')})**")
            
            # 당첨 번호를 시각적으로 예쁘게 표시
            cols = st.columns(7)
            for i, num in enumerate(last_week_data['당첨번호']):
                cols[i].markdown(f"<h3 style='text-align: center; color: white; background-color: #4CAF50; border-radius: 50%; width: 50px; height: 50px; line-height: 50px; display: inline-block;'>{num}</h3>", unsafe_allow_html=True)
            cols[6].markdown(f"<h3 style='text-align: center; color: white; background-color: #FFC107; border-radius: 50%; width: 50px; height: 50px; line-height: 50px; display: inline-block;'>+{last_week_data['보너스번호']}</h3>", unsafe_allow_html=True)
            
        else:
            st.warning(f"지난 주 ({previous_drw_no}회차) 당첨 번호를 불러올 수 없습니다. 네트워크 연결 또는 웹사이트 상태를 확인해 주세요.")
    else:
        st.warning("최신 회차 정보를 가져올 수 없습니다.")

    st.markdown("---")

    # --- 2. 과거 데이터 분석 섹션 (사용자 선택 시 로드) ---
    st.header("📊 과거 당첨 번호 분석")
    st.info("오랜 기간의 데이터를 불러오면 시간이 다소 소요될 수 있습니다.")

    # 세션 상태 초기화 (초기 로드 시 데이터가 없는 상태로 시작)
    if 'analysis_df' not in st.session_state:
        st.session_state.analysis_df = pd.DataFrame()
        st.session_state.min_loaded_drw = 1
        st.session_state.max_loaded_drw = 1 # 더미 값

    # 데이터 로드 옵션
    if st.session_state.analysis_df.empty:
        st.subheader("데이터 불러오기")
        start_drw_input = st.number_input("시작 회차", min_value=1, value=max(1, latest_drw_no - 100), max_value=latest_drw_no)
        end_drw_input = st.number_input("끝 회차", min_value=start_drw_input, value=latest_drw_no, max_value=latest_drw_no)

        if st.button("📈 데이터 불러오고 분석하기"):
            with st.spinner(f"{start_drw_input}회차부터 {end_drw_input}회차까지 데이터를 불러오는 중..."):
                loaded_df = load_lotto_data_range(start_drw_input, end_drw_input)
                if not loaded_df.empty:
                    st.session_state.analysis_df = loaded_df
                    st.session_state.min_loaded_drw = start_drw_input
                    st.session_state.max_loaded_drw = end_drw_input
                    st.success(f"데이터 로드 완료: {start_drw_input}회차 ~ {end_drw_input}회차")
                    st.rerun() # 데이터 로드 후 앱 다시 렌더링
                else:
                    st.error("선택된 기간의 데이터를 불러오는 데 실패했습니다.")
    else:
        # 데이터가 이미 로드된 경우
        st.success(f"현재 분석 데이터 범위: {st.session_state.min_loaded_drw}회차 ~ {st.session_state.max_loaded_drw}회차")
        
        # 다시 불러오기 버튼
        if st.button("다른 기간 데이터 다시 불러오기"):
            st.session_state.analysis_df = pd.DataFrame() # 데이터 초기화
            st.rerun()

        st.subheader("기간별 당첨 번호 출현 빈도")

        # 로드된 데이터프레임 내에서 기간 선택
        min_year_loaded = st.session_state.analysis_df['날짜'].dt.year.min()
        max_year_loaded = st.session_state.analysis_df['날짜'].dt.year.max()

        selected_year_analysis = st.slider("년도 선택", min_year_loaded, max_year_loaded, max_year_loaded, key='year_analysis')
        
        # 선택된 년도에 해당하는 월만 필터링
        available_months_analysis = sorted(st.session_state.analysis_df[st.session_state.analysis_df['날짜'].dt.year == selected_year_analysis]['날짜'].dt.month.unique())
        
        selected_month_analysis = None
        if available_months_analysis:
            selected_month_analysis = st.slider("월 선택", min(available_months_analysis), max(available_months_analysis), max(available_months_analysis), key='month_analysis')
        else:
            st.warning("선택된 년도에 해당하는 월 데이터가 없습니다.")


        analysis_period = st.radio(
            "분석 기간 선택",
            ('선택된 기간 전체', '선택된 년도', '선택된 월'),
            key='analysis_radio'
        )

        if analysis_period == '선택된 기간 전체':
            plot_frequency(st.session_state.analysis_df, 
                           f"{st.session_state.min_loaded_drw}회차 ~ {st.session_state.max_loaded_drw}회차 로또 당첨 번호 출현 빈도")
        elif analysis_period == '선택된 년도':
            df_year = st.session_state.analysis_df[st.session_state.analysis_df['날짜'].dt.year == selected_year_analysis]
            plot_frequency(df_year, f"{selected_year_analysis}년 로또 당첨 번호 출현 빈도")
        elif analysis_period == '선택된 월':
            if selected_month_analysis is not None:
                df_month = st.session_state.analysis_df[
                    (st.session_state.analysis_df['날짜'].dt.year == selected_year_analysis) & 
                    (st.session_state.analysis_df['날짜'].dt.month == selected_month_analysis)
                ]
                plot_frequency(df_month, f"{selected_year_analysis}년 {selected_month_analysis}월 로또 당첨 번호 출현 빈도")
            else:
                st.warning("월 데이터가 없어 막대 그래프를 그릴 수 없습니다.")

if __name__ == "__main__":
    main()
