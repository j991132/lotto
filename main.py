import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Setting page configuration
st.set_page_config(page_title="South Korean Lotto Analysis", layout="wide")

# Adding title and description
st.title("South Korean Lotto Winning Numbers Analysis")
st.markdown("""
This app analyzes historical South Korean Lotto winning numbers (Draws 1 to 1144, up to November 2, 2024) 
and predicts numbers for the current week based on frequency.
""")

# Debugging: Display current working directory and file existence
st.write(f"Current working directory: {os.getcwd()}")
file_path = "lotto_data.csv"
st.write(f"Checking for CSV file at: {file_path}")
if os.path.exists(file_path):
    st.success("CSV file found!")
else:
    st.error(f"CSV file not found at: {file_path}. Please ensure it is uploaded to the repository root.")

# Loading the CSV file
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(file_path)
        st.success("CSV file loaded successfully!")
        st.write(f"Columns in CSV file: {list(df.columns)}")
        return df
    except FileNotFoundError:
        st.error(f"CSV file not found at: {file_path}. Please upload 'lotto_data.csv' to the repository.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

df = load_data()
if df is None:
    st.stop()

# Processing winning numbers
def calculate_frequencies(df):
    try:
        main_numbers = df[['첫번째', '두번째', '세번째', '네번째', '다섯번째', '여섯번째']].values.flatten()
        bonus_numbers = df['보너스'].values
        
        main_freq = pd.Series(main_numbers).value_counts().sort_index()
        bonus_freq = pd.Series(bonus_numbers).value_counts().sort_index()
        
        freq_df = pd.DataFrame({'Number': range(1, 46), 'Main_Frequency': 0, 'Bonus_Frequency': 0})
        freq_df.set_index('Number', inplace=True)
        
        for num in range(1, 46):
            if num in main_freq.index:
                freq_df.loc[num, 'Main_Frequency'] = main_freq[num]
            if num in bonus_freq.index:
                freq_df.loc[num, 'Bonus_Frequency'] = bonus_freq[num]
        
        freq_df['Total_Frequency'] = freq_df['Main_Frequency'] + freq_df['Bonus_Frequency']
        return freq_df
    except Exception as e:
        st.error(f"Error processing frequencies: {str(e)}")
        return None

freq_df = calculate_frequencies(df)
if freq_df is None:
    st.stop()

# Creating bar chart with Plotly
fig = px.bar(
    freq_df.reset_index(),
    x='Number',
    y='Main_Frequency',
    labels={'Main_Frequency': 'Frequency', 'Number': 'Lotto Number'},
    title='Frequency of Main Winning Numbers (Draws 1 to 1144)',
    color='Main_Frequency',
    color_continuous_scale='Viridis'
)
fig.update_layout(
    xaxis=dict(tickmode='linear', tick0=1, dtick=1),
    yaxis_title='Number of Appearances',
    xaxis_title='Lotto Number (1-45)',
    showlegend=False
)

# Displaying the bar chart
st.plotly_chart(fig, use_container_width=True)

# Predicting this week's numbers
st.subheader("Predicted Numbers for This Week")
st.markdown("Based on the most frequent numbers in historical draws.")

try:
    top_main_numbers = freq_df['Main_Frequency'].nlargest(6).index.tolist()
    top_bonus_number = freq_df['Bonus_Frequency'].nlargest(1).index[0]
    
    st.write("**Predicted Main Numbers**: " + ", ".join(map(str, sorted(top_main_numbers))))
    st.write("**Predicted Bonus Number**: " + str(top_bonus_number))
    st.markdown("""
    *Note*: This prediction is based on historical frequency and does not guarantee a win, as lottery draws are random.
    """)
except Exception as e:
    st.error(f"Error generating predictions: {str(e)}")
