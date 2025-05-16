import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import requests

st.set_page_config(layout="wide")
st.title("Healthcare Risk Explorer – Upload, URL, or Local")

# Define headers for UCI Heart Disease Dataset
default_headers = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"
]

# --- Upload Method Selection ---
st.sidebar.header(" Select Data Source")
data_source = st.sidebar.radio(
    "How would you like to load your data?",
    options=["Upload CSV file", "Paste CSV URL", "Use local default"],
)

df = None

# --- Load Data ---
if data_source == "Upload CSV file":
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file, header=None)
        if df.shape[1] == 14:
            df.columns = default_headers
        st.success(" File uploaded successfully!")

elif data_source == "Paste CSV URL":
    csv_url = st.sidebar.text_input("🔗 Enter the public CSV URL")
    if csv_url:
        try:
            response = requests.get(csv_url)
            response.raise_for_status()
            df = pd.read_csv(io.StringIO(response.text), header=None)
            if df.shape[1] == 14:
                df.columns = default_headers
            st.success(" CSV loaded from URL!")
        except Exception as e:
            st.error(f" Failed to load CSV: {e}")

elif data_source == "Use local default":
    try:
        df = pd.read_csv("heart.csv", header=None)
        if df.shape[1] == 14:
            df.columns = default_headers
        st.success(" Loaded default local file: heart.csv")
    except FileNotFoundError:
        st.error(" Default file 'heart.csv' not found in your directory.")

# --- Proceed if DataFrame is valid ---
if df is not None:
    st.markdown(f"###  Dataset Preview ({df.shape[0]} rows, {df.shape[1]} columns)")
    st.dataframe(df, use_container_width=True)

    # --- Filters ---
    st.sidebar.header(" Filter Columns")
    filtered_df = df.copy()

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            min_val, max_val = float(df[col].min()), float(df[col].max())
            selected_range = st.sidebar.slider(f"{col}", min_val, max_val, (min_val, max_val))
            filtered_df = filtered_df[(filtered_df[col] >= selected_range[0]) & (filtered_df[col] <= selected_range[1])]

        elif col == "sex":
            selected_sex = st.sidebar.selectbox("Sex (0 = Female, 1 = Male)", options=sorted(df[col].unique()))
            filtered_df = filtered_df[filtered_df["sex"] == selected_sex]

        else:
            unique_vals = sorted(df[col].dropna().unique())
            selected_vals = st.sidebar.multiselect(f"{col}", unique_vals, default=unique_vals)
            if selected_vals:
                filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

    st.markdown(f"###  Filtered Data: {filtered_df.shape[0]} rows")
    st.dataframe(filtered_df, use_container_width=True)

    # --- Visualization ---
    st.markdown("##  Visualize Your Data")
    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("Select X-axis", options=filtered_df.columns)
    with col2:
        y_col = st.selectbox("Select Y-axis (optional)", options=[None] + list(filtered_df.columns))

    chart_type = st.selectbox(" Select Chart Type", ["Histogram", "Boxplot", "Barplot", "Scatterplot"])

    fig, ax = plt.subplots(figsize=(10, 5))
    try:
        if chart_type == "Histogram":
            sns.histplot(filtered_df[x_col], kde=True, ax=ax)
        elif chart_type == "Boxplot":
            sns.boxplot(x=filtered_df[x_col], y=filtered_df[y_col] if y_col else None, ax=ax)
        elif chart_type == "Barplot":
            sns.barplot(x=x_col, y=y_col, data=filtered_df, ax=ax)
        elif chart_type == "Scatterplot" and y_col:
            sns.scatterplot(data=filtered_df, x=x_col, y=y_col, ax=ax)
        st.pyplot(fig)
    except Exception as e:
        st.error(f" Error plotting chart: {e}")

    # --- Download Filtered Data ---
    st.markdown("###  Download Filtered Dataset")
    st.download_button(
        label="Download CSV",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_data.csv",
        mime="text/csv",
    )
else:
    st.info("Please upload or load a CSV to begin.")

