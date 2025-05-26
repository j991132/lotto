import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import font_manager, rc
from datetime import datetime, date, timedelta
import random # random 모듈 임포트 추가

def app():
    st.set_page_config(layout="wide")
    st.title("역대 로또 당첨번호 분석")
    st.write("로또 당첨번호를 많이 나온 횟수 순으로 막대그래프로 보여줍니다.")

    # Matplotlib 한글 폰트 설정
    font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    korean_font_name = None
    
    possible_korean_fonts = ['Malgun Gothic', 'AppleGothic', 'NanumGothic', 'NanumSquare', 'NanumBarunGothic']
    
    for font_name_attempt in possible_korean_fonts:
        for font_path in font_paths:
            fp = font_manager.FontProperties(fname=font_path)
            if font_name_attempt.lower() in fp.get_name().lower():
                korean_font_name = fp.get_name()
                break
        if korean_font_name:
            break

    if korean_font_name:
        rc('font', family=korean_font_name)
        plt.rcParams['axes.unicode_minus'] = False
    else:
        st.warning("경고: 한국어 폰트를 찾을 수 없습니다. 그래프의 한글 텍스트가 깨질 수 있습니다. '나눔고딕' 폰트(무료)를 설치하고 시스템에 반영(재부팅 또는 캐시 업데이트)하시는 것을 권장합니다.")
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False

    try:
        # 데이터 로드
        df = pd.read_csv('lotto_data.csv')
    except FileNotFoundError:
        st.error("오류: 'lotto_data.csv' 파일을 찾을 수 없습니다. 파일이 앱과 같은 디렉토리에 있는지 확인하세요.")
        return
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return

    # '추첨일' 컬럼을 datetime 형식으로 변환
    if '추첨일' in df.columns:
        df['추첨일'] = pd.to_datetime(df['추첨일'])
        min_dataset_date = df['추첨일'].min().date()
        max_dataset_date = df['추첨일'].max().date()

        st.sidebar.header("기간 선택")

        # 기본 종료일을 현재 날짜로 설정 (데이터셋의 최대 날짜를 넘지 않도록)
        default_end_date = min(date.today(), max_dataset_date)
        # 기본 시작일을 현재 날짜로부터 1년 전으로 설정 (데이터셋의 최소 날짜보다 이전으로 가지 않도록)
        default_start_date = max(default_end_date - timedelta(days=365), min_dataset_date)

        selected_start_date = st.sidebar.date_input("시작일", value=default_start_date, min_value=min_dataset_date, max_value=max_dataset_date)
        selected_end_date = st.sidebar.date_input("종료일", value=default_end_date, min_value=min_dataset_date, max_value=max_dataset_date)

        if selected_start_date > selected_end_date:
            st.sidebar.error("오류: 시작일은 종료일보다 빠르거나 같아야 합니다.")
            return

        df_filtered_by_date = df[(df['추첨일'].dt.date >= selected_start_date) & 
                                 (df['추첨일'].dt.date <= selected_end_date)]
        
        st.write(f"선택된 기간: **{selected_start_date}** 부터 **{selected_end_date}** 까지의 데이터 분석")

    else:
        st.warning("경고: '추첨일' 컬럼을 찾을 수 없습니다. 기간 선택 기능을 사용할 수 없습니다.")
        df_filtered_by_date = df.copy()

    lotto_columns = ['첫번째', '두번째', '세번째', '네번째', '다섯번째', '여섯번째', '보너스']
    
    missing_columns = [col for col in lotto_columns if col not in df_filtered_by_date.columns]
    if missing_columns:
        st.error(f"오류: 로또 번호 컬럼 중 다음이 누락되었습니다: {', '.join(missing_columns)}")
        st.write("사용 가능한 컬럼:")
        st.write(df_filtered_by_date.columns.tolist())
        return

    df_cleaned = df_filtered_by_date.dropna(subset=lotto_columns)
    
    if df_cleaned.empty:
        st.warning("경고: 선택된 기간에 로또 번호 컬럼에 유효한 데이터가 없어 분석을 계속할 수 없습니다.")
        return

    for col in lotto_columns:
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
    
    df_cleaned = df_cleaned.dropna(subset=lotto_columns)
    
    if df_cleaned.empty:
        st.warning("경고: 숫자형 변환 및 NaN 제거 후 데이터가 비어 있어 분석을 계속할 수 없습니다.")
        return
        
    df_cleaned[lotto_columns] = df_cleaned[lotto_columns].astype(int)

    try:
        all_lotto_numbers = df_cleaned[lotto_columns].melt(var_name='NumberType', value_name='LottoNumber')['LottoNumber']
    except Exception as e:
        st.error(f"로또 번호 통합 중 오류가 발생했습니다: {e}")
        return

    if all_lotto_numbers.empty:
        st.warning("경고: 통합된 로또 번호 시리즈가 비어 있어 출현 횟수를 계산할 수 없습니다.")
        return

    number_counts = all_lotto_numbers.value_counts().sort_values(ascending=False)

    st.subheader("로또 번호 출현 횟수 (많이 나온 순)")
    if number_counts.empty:
        st.warning("경고: 계산된 번호 출현 횟수가 비어 있어 그래프를 생성할 수 없습니다.")
        return

    try:
        fig, ax = plt.subplots(figsize=(15, 8))
        sns.barplot(x=number_counts.index, y=number_counts.values, palette='viridis', ax=ax)
        plt.xticks(rotation=90)

        ax.set_title('로또 당첨번호 출현 횟수', fontsize=16)
        ax.set_xlabel('로또 번호', fontsize=12)
        ax.set_ylabel('출현 횟수', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"막대 그래프 생성 중 오류가 발생했습니다: {e}")

    st.subheader("로또 번호 출현 횟수 데이터")
    st.dataframe(number_counts, use_container_width=False) 

    # --- 로또 당첨번호 예측 기능 추가 ---
    st.subheader("이번 주 로또 당첨번호 예측 (5세트)")
    st.info("이 예측은 과거 당첨번호의 출현 빈도에 기반한 통계적 추정이며, 실제 당첨을 보장하지 않습니다. 로또는 무작위 게임입니다.")

    if not number_counts.empty:
        all_possible_numbers = number_counts.index.tolist()
        
        # 예측에 사용할 번호 풀 (가장 많이 나온 번호들 상위 30개)
        # 전체 번호 개수보다 많아지지 않도록 min 함수 사용
        prediction_pool_size = min(30, len(all_possible_numbers)) 
        prediction_pool = number_counts.head(prediction_pool_size).index.tolist()

        predicted_sets = []
        num_sets_to_predict = 5
        numbers_per_set = 6

        # 5세트의 예측 번호 생성
        while len(predicted_sets) < num_sets_to_predict:
            if len(prediction_pool) < numbers_per_set:
                # 예측 풀이 충분하지 않으면 전체 로또 번호에서 무작위 선택
                current_set = sorted(random.sample(range(1, 46), numbers_per_set)) # 로또 번호는 1-45
            else:
                # 예측 풀에서 무작위 선택
                current_set = sorted(random.sample(prediction_pool, numbers_per_set))
            
            # 생성된 세트가 이미 예측된 세트 목록에 없는지 확인 (중복 방지)
            if current_set not in predicted_sets:
                predicted_sets.append(current_set)

        # 예측 결과 출력
        for i, lotto_set in enumerate(predicted_sets):
            st.write(f"**예측 {i+1}**: {', '.join(map(str, lotto_set))}")
    else:
        st.warning("경고: 로또 번호 출현 횟수 데이터가 없어 예측을 생성할 수 없습니다.")

if __name__ == '__main__':
    app()
