import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import font_manager, rc # 폰트 설정을 위한 모듈 임포트

def app():
    st.set_page_config(layout="wide") # 전체 화면 폭 사용 설정
    st.title("역대 로또 당첨번호 분석")
    st.write("로또 당첨번호를 많이 나온 횟수 순으로 막대그래프로 보여줍니다.")

    # Matplotlib 한글 폰트 설정
    # 시스템에 설치된 한글 폰트들을 확인하여 설정합니다.
    font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    korean_font_name = None

    # 여러 한글 폰트 이름을 시도하여 사용 가능한 폰트를 찾습니다.
    # 우선 순위: Malgun Gothic (Windows), AppleGothic (macOS), NanumGothic (다용도)
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
        plt.rcParams['axes.unicode_minus'] = False # 한글 폰트 사용 시 마이너스 부호 깨짐 방지
        # st.info(f"한글 폰트 '{korean_font_name}'를 설정했습니다.") # 디버깅 메시지 제거 요청으로 주석 처리
    else:
        st.warning("경고: 한국어 폰트를 찾을 수 없습니다. 그래프의 한글 텍스트가 깨질 수 있습니다. '나눔고딕' 폰트(무료)를 설치하고 시스템에 반영(재부팅 또는 캐시 업데이트)하시는 것을 권장합니다.")
        plt.rcParams['font.family'] = 'sans-serif' # 기본 폰트 유지
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

    lotto_columns = ['첫번째', '두번째', '세번째', '네번째', '다섯번째', '여섯번째', '보너스']
    
    # 실제 데이터에 lotto_columns가 있는지 확인
    missing_columns = [col for col in lotto_columns if col not in df.columns]
    if missing_columns:
        st.error(f"오류: 로또 번호 컬럼 중 다음이 누락되었습니다: {', '.join(missing_columns)}")
        st.write("사용 가능한 컬럼:")
        st.write(df.columns.tolist())
        return

    # NaN 값 제거 및 숫자형으로 변환
    df_cleaned = df.dropna(subset=lotto_columns)
    
    if df_cleaned.empty:
        st.warning("경고: 로또 번호 컬럼에 유효한 데이터가 없어 분석을 계속할 수 없습니다.")
        return

    for col in lotto_columns:
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
    
    df_cleaned = df_cleaned.dropna(subset=lotto_columns)
    
    if df_cleaned.empty:
        st.warning("경고: 숫자형 변환 및 NaN 제거 후 데이터가 비어 있어 분석을 계속할 수 없습니다.")
        return
        
    df_cleaned[lotto_columns] = df_cleaned[lotto_columns].astype(int)

    # 모든 로또 번호를 하나의 컬럼으로 모으기 (Melt)
    try:
        all_lotto_numbers = df_cleaned[lotto_columns].melt(var_name='NumberType', value_name='LottoNumber')['LottoNumber']
    except Exception as e:
        st.error(f"로또 번호 통합 중 오류가 발생했습니다: {e}")
        return

    if all_lotto_numbers.empty:
        st.warning("경고: 통합된 로또 번호 시리즈가 비어 있어 출현 횟수를 계산할 수 없습니다.")
        return

    # 각 번호의 출현 횟수 계산
    number_counts = all_lotto_numbers.value_counts().sort_values(ascending=False)

    # 막대 그래프 생성
    st.subheader("로또 번호 출현 횟수 (많이 나온 순)")
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
    except Exception as e:
        st.error(f"막대 그래프 생성 중 오류가 발생했습니다: {e}")

    st.subheader("전체 로또 번호 출현 횟수 데이터")
    st.dataframe(number_counts)

if __name__ == '__main__':
    app()
