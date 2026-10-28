
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# RailEase Admin Dashboard
# Existing application files ko modify nahi karta
# --------------------------------------------------

st.set_page_config(
    page_title="RailEase Admin Dashboard",
    page_icon="🚆",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "railease.db"

st.title("🚆 RailEase Admin Dashboard")
st.caption("Train Booking Analytics & Insights")

st.divider()


# ---------- Database connection ----------

def get_connection():
    if not DB_PATH.exists():
        st.error(f"Database nahi mili: {DB_PATH}")
        st.info(
            "Pehle apni existing application se database create karo."
        )
        st.stop()

    return sqlite3.connect(DB_PATH)


# ---------- Database tables ----------

def get_tables():
    with get_connection() as conn:
        query = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
        """
        return pd.read_sql_query(query, conn)["name"].tolist()


def get_table_data(table_name):
    # Table names database se milte hain.
    # Identifier ko safely quote kiya gaya hai.
    safe_name = '"' + table_name.replace('"', '""') + '"'

    with get_connection() as conn:
        return pd.read_sql_query(
            f"SELECT * FROM {safe_name}",
            conn
        )


# ---------- Load database ----------

try:
    tables = get_tables()

    if not tables:
        st.warning("Database mein abhi koi table nahi mili.")
        st.stop()

    st.sidebar.header("Dashboard Settings")
    st.sidebar.success("Database connected")
    selected_table = st.sidebar.selectbox(
        "Table ka data dekhein",
        tables
    )

    # Saari tables ka data load karo
    table_data = {
        table: get_table_data(table)
        for table in tables
    }

except Exception as error:
    st.error("Database read karne mein problem hui.")
    st.code(str(error))
    st.stop()


# ---------- Database overview ----------

st.subheader("📊 Database Overview")

overview_cols = st.columns(3)

overview_cols[0].metric("Total Tables", len(tables))
overview_cols[1].metric(
    "Total Records",
    sum(len(df) for df in table_data.values())
)
overview_cols[2].metric(
    "Database",
    "Connected",
    delta="Ready"
)

st.divider()


# ---------- Table selector ----------

st.subheader("🗂️ Table Data")

current_df = table_data[selected_table]

st.write(f"**Selected table:** `{selected_table}`")
st.write(f"Total records: **{len(current_df)}**")

if current_df.empty:
    st.info("Is table mein abhi koi record nahi hai.")
else:
    st.dataframe(
        current_df,
        use_container_width=True,
        hide_index=True
    )


# ---------- Automatic chart generation ----------

st.divider()
st.subheader("📈 Data Visualizations")

if current_df.empty:
    st.info("Charts dikhane ke liye table mein records hone chahiye.")

else:
    # Numeric columns
    numeric_cols = current_df.select_dtypes(
        include="number"
    ).columns.tolist()

    # Text/category columns
    category_cols = [
        col for col in current_df.columns
        if col not in numeric_cols
        and current_df[col].nunique(dropna=True) <= 30
    ]

    # Numeric data ke charts
    if numeric_cols:
        st.markdown("### Numeric Analysis")

        selected_numeric = st.selectbox(
            "Numeric column select karo",
            numeric_cols,
            key="numeric_column"
        )

        numeric_values = pd.to_numeric(
            current_df[selected_numeric],
            errors="coerce"
        ).dropna()

        if not numeric_values.empty:
            chart_df = pd.DataFrame({
                "Record": range(1, len(numeric_values) + 1),
                selected_numeric: numeric_values.values
            })

            fig = px.bar(
                chart_df,
                x="Record",
                y=selected_numeric,
                title=f"{selected_numeric} Analysis",
                template="plotly_white"
            )

            st.plotly_chart(fig, use_container_width=True)

    # Category-wise charts
    if category_cols:
        st.markdown("### Category Analysis")

        selected_category = st.selectbox(
            "Category column select karo",
            category_cols,
            key="category_column"
        )

        category_counts = (
            current_df[selected_category]
            .fillna("Unknown")
            .astype(str)
            .value_counts()
            .reset_index()
        )

        category_counts.columns = [
            selected_category,
            "Count"
        ]

        left, right = st.columns(2)

        with left:
            fig_bar = px.bar(
                category_counts,
                x=selected_category,
                y="Count",
                title=f"{selected_category} Distribution",
                template="plotly_white"
            )

            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )

        with right:
            fig_pie = px.pie(
                category_counts,
                names=selected_category,
                values="Count",
                title=f"{selected_category} Breakdown"
            )

            st.plotly_chart(
                fig_pie,
                use_container_width=True
            )

    if not numeric_cols and not category_cols:
        st.info(
            "Is table mein automatic charts ke liye "
            "suitable numeric ya category columns nahi mile."
        )


# ---------- All database tables ----------

st.divider()
st.subheader("📋 All Database Tables")

for table_name, df in table_data.items():
    with st.expander(
        f"{table_name} — {len(df)} records"
    ):
        if df.empty:
            st.info("Table empty hai.")
        else:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )


# ---------- Footer ----------

st.divider()
st.caption(
    "RailEase | Admin Analytics Dashboard | "
    "Data source: Existing SQLite database"
)

