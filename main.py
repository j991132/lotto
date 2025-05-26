import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# Define a function to generate the Streamlit app code
def generate_streamlit_app_code():
    streamlit_code = """
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def app():
    st.title("역대 로또 당첨번호 분석")
    st.write("로또 당첨번호를 많이 나온 횟수 순으로 막대그래프로 보여줍니다.")

    # Load the data (assuming lotto_data.csv is in the same directory)
    try:
        df = pd.read_csv('lotto_data.csv')
    except FileNotFoundError:
        st.error("lotto_data.csv 파일을 찾을 수 없습니다. 파일이 앱과 같은 디렉토리에 있는지 확인하세요.")
        return

    # Select the columns containing lotto numbers and bonus number
    lotto_columns = ['첫번째', '두번째', '세번째', '네번째', '다섯번째', '여섯번째', '보너스']
    
    # Drop rows where any of the lotto number columns are NaN
    df_cleaned = df.dropna(subset=lotto_columns)

    # Convert lotto number columns to integer type, handling potential non-integer values
    for col in lotto_columns:
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')
    df_cleaned = df_cleaned.dropna(subset=lotto_columns)
    df_cleaned[lotto_columns] = df_cleaned[lotto_columns].astype(int)

    # Melt the DataFrame to get all lotto numbers in a single column
    all_lotto_numbers = df_cleaned[lotto_columns].melt(var_name='NumberType', value_name='LottoNumber')['LottoNumber']

    # Count the occurrences of each number
    number_counts = all_lotto_numbers.value_counts().sort_values(ascending=False)

    st.subheader("로또 번호 출현 횟수 (많이 나온 순)")

    # Create the bar chart
    fig, ax = plt.subplots(figsize=(15, 8))
    sns.barplot(x=number_counts.index, y=number_counts.values, palette='viridis', ax=ax)
    ax.set_title('역대 로또 당첨번호 출현 횟수', fontsize=16)
    ax.set_xlabel('로또 번호', fontsize=12)
    ax.set_ylabel('출현 횟수', fontsize=12)
    plt.xticks(rotation=90)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("출현 횟수 데이터")
    st.dataframe(number_counts)

if __name__ == '__main__':
    app()
"""
    return streamlit_code

# Generate the Streamlit app code
streamlit_app_code = generate_streamlit_app_code()

# Save the code to a file
with open('lotto_analyzer_app.py', 'w', encoding='utf-8') as f:
    f.write(streamlit_app_code)

print("Streamlit 앱 파일 'lotto_analyzer_app.py'가 생성되었습니다.")
