import streamlit as st
import pandas as pd
import plotly.express as px

# Setting page configuration
st.set_page_config(page_title="South Korean Lotto Analysis", layout="wide")

# Adding title and description
st.title("South Korean Lotto Winning Numbers Analysis")
st.markdown("""
This app analyzes historical South Korean Lotto winning numbers (Draws 1 to 1144, up to November 2, 2024) 
and predicts numbers for the current week based on frequency.
""")

# Loading the Excel file
@st.cache_data
def load_data():
    file_path = "역대 로또 당첨번호(1회~1144회)(2024.11.02.).xlsx"
    df = pd.read_excel(file_path, sheet_name=0)
    return df

df = load_data()

# Processing winning numbers
def calculate_frequencies(df):
    # Extracting main numbers (첫번째 to 여섯번째) and bonus numbers
    main_numbers = df[['첫번째', '두번째', '세번째', '네번째', '다섯번째', '여섯번째']].values.flatten()
    bonus_numbers = df['보너스'].values
    
    # Counting frequencies for numbers 1 to 45
    main_freq = pd.Series(main_numbers).value_counts().sort_index()
    bonus_freq = pd.Series(bonus_numbers).value_counts().sort_index()
    
    # Creating a DataFrame for all numbers (1 to 45)
    freq_df = pd.DataFrame({'Number': range(1, 46), 'Main_Frequency': 0, 'Bonus_Frequency': 0})
    freq_df.set_index('Number', inplace=True)
    
    # Filling frequencies
    for num in range(1, 46):
        if num in main_freq.index:
            freq_df.loc[num, 'Main_Frequency'] = main_freq[num]
        if num in bonus_freq.index:
            freq_df.loc[num, 'Bonus_Frequency'] = bonus_freq[num]
    
    freq_df['Total_Frequency'] = freq_df['Main_Frequency'] + freq_df['Bonus_Frequency']
    return freq_df

freq_df = calculate_frequencies(df)

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

# Selecting top 6 main numbers and 1 bonus number
top_main_numbers = freq_df['Main_Frequency'].nlargest(6).index.tolist()
top_bonus_number = freq_df['Bonus_Frequency'].nlargest(1).index[0]

# Displaying predicted numbers
st.write("**Predicted Main Numbers**: " + ", ".join(map(str, sorted(top_main_numbers))))
st.write("**Predicted Bonus Number**: " + str(top_bonus_number))
st.markdown("""
*Note*: This prediction is based on historical frequency and does not guarantee a win, as lottery draws are random.
""")
