import streamlit as st
import pandas as pd
import io
import plotly.express as px

# ----------------- Page Config -----------------
st.set_page_config(page_title="📊 Transaction Analyzer", layout="wide")

st.title("📊 Transaction Analyzer")
st.markdown("Analyze transaction amounts by **Account Code**, with filters, pivot tables, charts, and Excel export.")

# ----------------- File Upload -----------------
uploaded_file = st.file_uploader("📁 Upload Excel File", type=["xlsx"])

if uploaded_file:
    # Load and clean
    df = pd.read_excel(uploaded_file, sheet_name="Sheet1")
    df = df.dropna(subset=['Transaction Date', 'Account Code', 'Base Amount'])

    # Date processing
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
    df['Year'] = df['Transaction Date'].dt.year
    df['Month'] = df['Transaction Date'].dt.strftime('%b')
    df['Month_Num'] = df['Transaction Date'].dt.month

    # ----------------- Sidebar Filters -----------------
    with st.sidebar:
        st.header("🔍 Filters")

        selected_year = st.selectbox("Select Year", sorted(df['Year'].unique(), reverse=True))
        df_year = df[df['Year'] == selected_year]

        account_codes = sorted(df_year['Account Code'].unique())
        selected_codes = st.multiselect("Select Account Codes", account_codes, default=account_codes)

        month_options = df_year['Month'].unique()
        month_map = dict(zip(df_year['Month'], df_year['Month_Num']))
        sorted_months = sorted(month_options, key=lambda m: month_map[m])
        selected_months = st.multiselect("Select Months", sorted_months, default=sorted_months)

    # ----------------- Filtered Data -----------------
    filtered_df = df_year[
        (df_year['Account Code'].isin(selected_codes)) &
        (df_year['Month'].isin(selected_months))
    ]

    # ----------------- KPIs -----------------
    st.markdown("### 📌 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("🔢 Total Transactions", f"{len(filtered_df):,}")
    col2.metric("💰 Total Amount", f"${filtered_df['Base Amount'].sum():,.2f}")
    col3.metric("📈 Avg per Transaction", f"${filtered_df['Base Amount'].mean():,.2f}")

    st.divider()

    # ----------------- Pivot Table -----------------
    st.subheader(f"📆 Pivot Table for {selected_year}")
    pivot = pd.pivot_table(
        filtered_df,
        index='Account Code',
        columns='Month',
        values='Base Amount',
        aggfunc='sum',
        fill_value=0
    )
    pivot = pivot.reindex(columns=sorted_months, fill_value=0)
    pivot['Total'] = pivot.sum(axis=1)
    st.dataframe(pivot.style.format("{:,.2f}"), use_container_width=True)

    # ----------------- Bar Chart -----------------
    st.subheader("📊 Monthly Total Amount")
    monthly_totals = filtered_df.groupby('Month').agg({'Base Amount': 'sum'}).reset_index()
    monthly_totals['Month_Num'] = monthly_totals['Month'].map(month_map)
    monthly_totals = monthly_totals.sort_values(by='Month_Num')

    bar_fig = px.bar(
        monthly_totals,
        x='Month',
        y='Base Amount',
        text_auto='.2s',
        color='Month',
        title="Monthly Transaction Amounts",
        labels={'Base Amount': 'Amount'},
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    # ----------------- Pie Chart -----------------
    st.subheader("📎 Amount Distribution by Account Code")
    code_totals = filtered_df.groupby('Account Code').agg({'Base Amount': 'sum'}).reset_index()
    pie_fig = px.pie(
        code_totals,
        names='Account Code',
        values='Base Amount',
        title="Contribution by Account Code",
        hole=0.4
    )
    st.plotly_chart(pie_fig, use_container_width=True)

    # ----------------- Excel Export -----------------
    st.divider()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pivot.to_excel(writer, sheet_name=f"Pivot_{selected_year}")
    output.seek(0)

    st.download_button(
        label="📥 Download Pivot Table as Excel",
        data=output,
        file_name=f"pivot_{selected_year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Please upload an Excel file with your transaction data.")
