from openpyxl import Workbook
from io import BytesIO
import pandas as pd
import streamlit as st

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'})
    worksheet.set_column('A:A', None, format1)
    writer.close()
    processed_data = output.getvalue()
    return processed_data

@st.cache_data
def convert_csv(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False)

@st.cache_data
def ler_arquivo(nome_df):
    df = pd.read_csv(f"{nome_df}").dropna(axis=1, how="any")
    return df