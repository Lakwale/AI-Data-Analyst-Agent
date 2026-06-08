import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
import google.generativeai as genai

#-------------------------------
#GEMINI CONFIG(SECURE)
#-------------------------------

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.title("CSV Data Analyzer")

uploaded_file = st.file_uploader("Upload a CSV File", type=["csv"])

if uploaded_file is not None:

    #-----------------
    # Read CSV
    #-----------------
    df = pd.read_csv(uploaded_file)

    #----------------------
    # Fiters
    #----------------------

    st.subheader("Filters")
  
    filter_column = st.selectbox(
            "Select Column to Filter", 
             df.columns
    )

    filter_values = df[filter_column].unique()

    selected_value = st.selectbox(
             "Select Value",
              filter_values
    )

    filtered_df = df[df[filter_column] == selected_value]

    #-------------------
    # Data Quality
    #-------------------
    st.subheader("Data Preview")
    st.dataframe(filtered_df)

    st.subheader("Data Quality Report")

    missing_values = filtered_df.isnull().sum()

    st.dataframe(
         missing_values.reset_index().rename( 
                 columns={
                     "index" :"Column",
                       0:"Missing Values"
                  }
          )
     )

    #---------------------
    # Data Information
    #---------------------

    st.subheader("Dataset Information")
    st.write("Rows:", df.shape[0])
    st.write("Columns:", df.shape[1])

    #------------------------
    # KPI Section
    #------------------------

    st.subheader("Summary Statistics")
    st.write(df.describe())

    st.subheader("Dashbroad KPI's")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric( "Rows" , filtered_df.shape[0])
    col2.metric("Columns" , filtered_df.shape[1])
    col3.metric("Missing Values" , filtered_df.isnull().sum().sum())

    numeric_cols=filtered_df.select_dtypes(include="number").columns

    if len(numeric_cols) > 0:
          total_value = filtered_df[numeric_cols[0]].sum()

          col4.metric(
                 "Total",f"{total_value:,.0f}"
          )

    #------------------
    # Chart Section
    #------------------

    columns = filtered_df.columns.tolist()

    x_axis = st.selectbox("Select X-Axis", columns)
    y_axis = st.selectbox("Select Y-Axis", columns)

    chart_type = st.selectbox(
        "Select Chart Type",
        ["Bar Chart", "Line Chart", "Pie Chart"]
    )

    if chart_type == "Bar Chart":
        fig = px.bar(df, x=x_axis, y=y_axis)

    elif chart_type == "Line Chart":
        fig = px.line(df, x=x_axis, y=y_axis)

    else:
        fig = px.pie(df, names=x_axis, values=y_axis)

    left_col, right_col = st.columns(2)
     
    with left_col: 
         st.plotly_chart(fig, use_container_width=True)
   
    with right_col:

         if len(numeric_cols) > 0:
               
             pie_fig = px.pie(
                  filtered_df,
                  names=x_axis,
                  values=y_axis
             )

             st.plotly_chart(
                    pie_fig,
                   use_container_width=True
             )

    #---------------
    # SQL Section
    #---------------

    st.subheader("Run SQL Query")

    conn = sqlite3.connect(":memory:")

    df.to_sql(
        "sales_data",
        conn,
        index=False,
        if_exists="replace"
    )

    query = st.text_area(
        "Enter SQL Query",
        "SELECT * FROM sales_data LIMIT 5"
    )

    if st.button("Run Query"):

        try:
            result = pd.read_sql_query(query, conn)
            st.dataframe(result)

            csv = result.to_csv(index=False)
     
            st.download_button(
                  label="Download Results",
                  data=csv,
                  file_name="query_results.csv",
                  mime="text/csv"
             )

        except Exception as e:
            st.error(str(e))

    #------------------
    # Natural Language
    #------------------
   
    st.subheader("Natural Language to SQL")

    user_request = st.text_input(
         "Ask for data in plain English"
    )
     
    if st.button("Generate SQL") :

        request = user_request.lower()

        if "top 5 " in request and "sales" in request:

             generate_sql = """
             SELECT Product,
             SUM(Sales) AS TotalSales
             FROM sales_data
             GROUP BY Product
             ORDER BY TotalSales DESC
             LIMIT 5
             """
        elif "all data" in request:
 
              generated_sql = """
                SELECT * FROM sales_data
                """

        else:
           
              generated_sql = """
                SELECT * FROM sales_data LIMIT 10
                 """
        st.code(generated_sql)

        result = pd.read_sql_query(
              generated_sql,
              conn
        )
   
        st.dataframe(result)       

    #--------------------
    #AI insights section
    #--------------------

    st.subheader("AI Insights")

    numeric_columns = df.select_dtypes(include="number").columns

    if len(numeric_columns)>0:
 
           selected_column = st.selectbox(
                  "Select  Numeric Column", 
                   numeric_columns
             )
 
           total = df[selected_column].sum()
           avg = df[selected_column].mean()
           maximum = df[selected_column].max()
           minimum = df[selected_column].min()

           st.write(f"Total {selected_column}:{total:,.2f}")
           st.write(f"Average { selected_column} : {avg:,.2f}")
           st.write(f"Highest {selected_column} : {maximum:,.2f}")
           st.write(f"Lowest {selected_column} : {minimum:,.2f}")
    
    else:
      st.warning("No numeric columns found in the dataset.")
    
    #-------------------------
    # Gemini AI Section
    #-------------------------

    st.subheader("Ask AI About Your Data")
    user_question = st.text_input(
            "Ask a question about your dataset"
    )
    #Gemini AI

    if st.button("Gen AI Answer"):

      model = genai.GenerativeModel(
           "models/gemini-2.0-flash-lite"
    )

    prompt = f"""
    Dataset Columns:
    {df.columns.tolist()}

    Sample Data:
    {df.head().to_string()}

    User Question:
    {user_question}
    """

    try:
        response = model.generate_content(prompt)
        st.write(response.text)

    except Exception as e:
        st.error(f"Gemini Error: {str(e)}")