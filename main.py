import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def app():
    st.set_page_config(layout="wide") # 전체 화면 폭 사용 설정
    st.title("역대 로또 당첨번호 분석")
    st.write("로또 당첨번호를 많이 나온 횟수 순으로 막대그래프로 보여줍니다.")

    # 1. 데이터 로드
    st.subheader("1. 데이터 로드")
    try:
        df = pd.read_csv('lotto_data.csv')
        st.success("lotto_data.csv 파일이 성공적으로 로드되었습니다.")
        st.write("로드된 데이터의 첫 5행:")
        st.dataframe(df.head())
        st.write(f"로드된 데이터의 행/열: {df.shape}")
    except FileNotFoundError:
        st.error("오류: 'lotto_data.csv' 파일을 찾을 수 없습니다. 파일이 앱과 같은 디렉토리에 있는지 확인하세요.")
        return
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return

    # 2. 로또 번호 컬럼 선택 및 전처리
    st.subheader("2. 로또 번호 컬럼 선택 및 전처리")
    lotto_columns = ['첫번째', '두번째', '세번째', '네번째', '다섯번째', '여섯번째', '보너스']
    
    # 실제 데이터에 lotto_columns가 있는지 확인
    missing_columns = [col for col in lotto_columns if col not in df.columns]
    if missing_columns:
        st.error(f"오류: 로또 번호 컬럼 중 다음이 누락되었습니다: {', '.join(missing_columns)}")
        st.write("사용 가능한 컬럼:")
        st.write(df.columns.tolist())
        return

    # NaN 값 제거
    initial_rows = df.shape[0]
    df_cleaned = df.dropna(subset=lotto_columns)
    rows_after_dropna = df_cleaned.shape[0]
    st.info(f"로또 번호 컬럼에 NaN 값이 있는 {initial_rows - rows_after_dropna}개 행을 제거했습니다.")
    if df_cleaned.empty:
        st.warning("경고: NaN 값이 제거된 후 데이터가 비어 있습니다. 로또 번호 컬럼에 유효한 데이터가 있는지 확인하세요.")
        return
    st.write("NaN 값 제거 후 데이터의 첫 5행:")
    st.dataframe(df_cleaned.head())
    st.write(f"NaN 값 제거 후 데이터의 행/열: {df_cleaned.shape}")

    # 숫자형으로 변환 (오류가 있는 경우 NaN으로 처리)
    for col in lotto_columns:
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
    
    # 숫자형 변환 후 다시 NaN 제거 (변환 실패한 값 제거)
    initial_rows_convert = df_cleaned.shape[0]
    df_cleaned = df_cleaned.dropna(subset=lotto_columns)
    rows_after_convert_dropna = df_cleaned.shape[0]
    st.info(f"숫자형 변환 실패로 인해 {initial_rows_convert - rows_after_convert_dropna}개 행을 추가로 제거했습니다.")
    
    if df_cleaned.empty:
        st.warning("경고: 숫자형 변환 및 NaN 제거 후 데이터가 비어 있습니다. 로또 번호 컬럼의 데이터 형식을 확인하세요.")
        return
        
    df_cleaned[lotto_columns] = df_cleaned[lotto_columns].astype(int)
    st.success("로또 번호 컬럼이 성공적으로 숫자형으로 변환되었습니다.")

    # 3. 모든 로또 번호를 하나의 컬럼으로 모으기 (Melt)
    st.subheader("3. 로또 번호 통합")
    try:
        all_lotto_numbers = df_cleaned[lotto_columns].melt(var_name='NumberType', value_name='LottoNumber')['LottoNumber']
        st.success("모든 로또 번호가 하나의 시리즈로 통합되었습니다.")
        st.write("통합된 로또 번호 시리즈의 첫 10개:")
        st.write(all_lotto_numbers.head(10))
    except Exception as e:
        st.error(f"로또 번호 통합 중 오류가 발생했습니다: {e}")
        return

    # 4. 각 번호의 출현 횟수 계산
    st.subheader("4. 번호별 출현 횟수 계산")
    if all_lotto_numbers.empty:
        st.warning("경고: 통합된 로또 번호 시리즈가 비어 있어 출현 횟수를 계산할 수 없습니다.")
        return

    number_counts = all_lotto_numbers.value_counts().sort_values(ascending=False)
    st.success("각 로또 번호의 출현 횟수가 계산되었습니다.")
    st.write("로또 번호 출현 횟수 (상위 10개):")
    st.dataframe(number_counts.head(10))

    # 5. 막대 그래프 생성
    st.subheader("5. 로또 번호 출현 횟수 막대 그래프")
    if number_counts.empty:
        st.warning("경고: 계산된 번호 출현 횟수가 비어 있어 그래프를 생성할 수 없습니다.")
        return

    try:
        fig, ax = plt.subplots(figsize=(15, 8))
        sns.barplot(x=number_counts.index, y=number_counts.values, palette='viridis', ax=ax)
        ax.set_title('역대 로또 당첨번호 출현 횟수', fontsize=16)
        ax.set_xlabel('로또 번호', fontsize=12)
        ax.set_ylabel('출현 횟수', fontsize=12)
        plt.xticks(rotation=90)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
        st.success("막대 그래프가 성공적으로 생성되었습니다.")
    except Exception as e:
        st.error(f"막대 그래프 생성 중 오류가 발생했습니다: {e}")

    st.subheader("전체 로또 번호 출현 횟수 데이터")
    st.dataframe(number_counts)

if __name__ == '__main__':
    app()
