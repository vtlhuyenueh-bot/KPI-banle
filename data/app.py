import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# CẤU HÌNH CHUNG
# =========================
st.set_page_config(page_title="KPI Tracker", layout="wide")

st.title("📊 Bảng theo dõi KPI nhóm")

# =========================
# TẠO 2 TAB
# =========================
tab1, tab2 = st.tabs(["📂 Import KPI Data", "📈 Dashboard"])

# =========================
# TAB 1: IMPORT DỮ LIỆU
# =========================
with tab1:
    st.header("Tải file KPI")

    uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.success("✅ File đã tải thành công")
            st.dataframe(df.head())

            # Gợi ý map tên cột
            columns = df.columns.tolist()

            col_chitieu = st.selectbox("Chọn cột Chỉ tiêu", columns)
            col_kehoach = st.selectbox("Chọn cột Kế hoạch", columns)
            col_thuchien = st.selectbox("Chọn cột Thực hiện", columns)

            # Lưu vào session_state
            st.session_state["data"] = {
                "df": df,
                "cols": {
                    "Chỉ tiêu": col_chitieu,
                    "Kế hoạch": col_kehoach,
                    "Thực hiện": col_thuchien
                }
            }

        except Exception as e:
            st.error(f"Lỗi khi đọc file: {e}")

# =========================
# TAB 2: DASHBOARD KPI
# =========================
with tab2:
    st.header("Dashboard KPI")

    if "data" in st.session_state:
        df = st.session_state["data"]["df"]
        cols = st.session_state["data"]["cols"]

        # Chuẩn hóa lại tên cột
        df_chart = df[[cols["Chỉ tiêu"], cols["Kế hoạch"], cols["Thực hiện"]]]
        df_chart = df_chart.rename(columns={
            cols["Chỉ tiêu"]: "Chỉ tiêu",
            cols["Kế hoạch"]: "Kế hoạch",
            cols["Thực hiện"]: "Thực hiện"
        })

        # Hiển thị thống kê
        st.subheader("📌 Tổng quan dữ liệu")
        st.write(f"Số dòng dữ liệu: {df_chart.shape[0]}")
        st.write(f"Số cột dữ liệu: {df_chart.shape[1]}")

        # Vẽ biểu đồ
        st.subheader("📊 So sánh Kế hoạch vs Thực hiện")
        fig = px.bar(
            df_chart,
            x="Chỉ tiêu",
            y=["Kế hoạch", "Thực hiện"],
            barmode="group",
            text_auto=True,
            color_discrete_sequence=["#636EFA", "#EF553B"]
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tính % hoàn thành
        df_chart["% Hoàn thành"] = (df_chart["Thực hiện"] / df_chart["Kế hoạch"] * 100).round(2)
        st.subheader("📈 Tỷ lệ hoàn thành (%)")
        st.dataframe(df_chart)

    else:
        st.warning("⚠️ Vui lòng import file ở tab 'Import KPI Data' trước.")
