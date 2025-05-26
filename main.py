import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import font_manager, rc
from datetime import datetime, date

# emoji 라이브러리 임포트 (설치 필요)
try:
    import emoji
except ImportError:
    st.error("오류: 'emoji' 라이브러리가 설치되어 있지 않습니다. 다음 명령으로 설치해주세요: pip install emoji")
    st.stop() # 라이브러리가 없으면 앱 실행 중단

# 숫자를 이모지 문자열로 변환하는 함수
def number_to_emoji_str(number):
    s = str(number)
    emoji_str = ""
    for digit in s:
        # emoji.emojize를 사용하여 숫자 이모지로 변환
        # 예: '1' -> '1️⃣', '0' -> '0️⃣'
        emoji_str += emoji.emojize(f":keycap_digit_{digit}:")
    return emoji_str

def app():
    st.set_page_config(layout="wide")
    st.title("역대 로또 당첨번호 분석")
    st.write("로또 당첨번호를 많이 나온 횟수 순으로 막대그래프로 보여줍니다.")

    # Matplotlib 한글 폰트 및 이모지 폰트 설정
    font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    korean_font_name = None
    
    # 폰트 우선순위: Malgun Gothic (Windows), AppleGothic (macOS), NanumGothic (다용도)
    possible_korean_fonts = ['Malgun Gothic', 'AppleGothic', 'NanumGothic', 'NanumSquare', 'NanumBarunGothic']
    
    for font_name_attempt in possible_korean_fonts:
        for font_path in font_paths:
            fp = font_manager.FontProperties(fname=font_path)
            if font_name_attempt.lower() in fp.get_name().lower():
                korean_font_name = fp.get_name()
                break
        if korean_font_name:
            break

    # 이모지 폰트를 fallback으로 설정
    # 'Segoe UI Emoji'는 Windows, 'Apple Color Emoji'는 macOS에서 이모지를 지원합니다.
    # 'DejaVu Sans'는 리눅스 등에서 사용될 수 있는 일반 폰트입니다.
    if korean_font_name:
        plt.rcParams['font.family'] = [korean_font_name, 'Segoe UI Emoji', 'Apple Color Emoji', 'DejaVu Sans', 'sans-serif']
    else:
        st.warning("경고: 한국어 폰트를 찾을 수 없습니다. 그래프의 한글 텍스트가 깨질 수 있습니다. '나눔고딕' 폰트(무료)를 설치하고 시스템에 반영(재부팅 또는 캐시 업데이트)하시는 것을 권장합니다.")
        plt.rcParams['font.family'] = ['Segoe UI Emoji', 'Apple Color Emoji', 'DejaVu Sans', 'sans-serif'] # 한국어 폰트 없어도 이모지 시도
    
    plt.rcParams['axes.unicode_minus'] = False # 한글 폰트 사용 시 마이너스 부호 깨짐 방지


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
        min_date = df['추첨일'].min().date()
        max_date = df['추첨일'].max().date()

        st.sidebar.header("기간 선택")
        selected_start_date = st.sidebar.date_input("시작일", value=min_date, min_value=min_date, max_value=max_date)
        selected_end_date = st.sidebar.date_input("종료일", value=max_date, min_value=min_date, max_value=max_date)

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
        
        # X축 라벨을 이모지 숫자로 변환
        emoji_labels = [number_to_emoji_str(num) for num in number_counts.index]
        ax.set_xticks(np.arange(len(number_counts))) # 틱 위치 설정
        ax.set_xticklabels(emoji_labels, rotation=90) # 이모지 라벨 적용

        ax.set_title('로또 당첨번호 출현 횟수', fontsize=16)
        ax.set_xlabel('로또 번호', fontsize=12)
        ax.set_ylabel('출현 횟수', fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"막대 그래프 생성 중 오류가 발생했습니다: {e}")
        st.warning("경고: 이모지 폰트 설정이 올바르지 않거나 시스템에서 이모지 폰트를 찾을 수 없어 이모지가 깨져 보일 수 있습니다.")


    st.subheader("로또 번호 출현 횟수 데이터")
    st.dataframe(number_counts, use_container_width=False) 

if __name__ == '__main__':
    app()
