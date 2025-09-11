import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="KPI Tracker", layout="wide")

st.title("📈 Bảng theo dõi KPI nhóm")

# Tạo 2 tab
tab_import, tab_dashboard = st.tabs(["📂 Import KPI Data", "📊 Dashboard"])

# Tab 1: Import KPI
with tab_import:
    st.header("📂 Import file KPI")
    uploaded_file = st.file_uploader("Upload file KPI (Excel)", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)

            # Reset lại session_state để tránh DuplicateError
            st.session_state["kpi_data"] = df.copy()

            st.success("✅ File đã được tải lên thành công!")
            st.dataframe(df)

        except Exception as e:
            st.error(f"Lỗi khi đọc file: {e}")
    else:
        st.info("👉 Vui lòng upload file KPI (.xlsx hoặc .xls)")

# Tab 2: Dashboard KPI
with tab_dashboard:
    st.header("📊 Dashboard KPI")

    if "kpi_data" in st.session_state:
        df = st.session_state["kpi_data"]

        # Hiển thị thống kê cơ bản
        st.subheader("📌 Tổng quan dữ liệu")
        st.write(f"Số dòng dữ liệu: {df.shape[0]}")
        st.write(f"Số cột dữ liệu: {df.shape[1]}")

        # Kiểm tra đủ cột để vẽ biểu đồ
        if all(col in df.columns for col in ["Chỉ tiêu", "Kế hoạch", "Thực hiện"]):
            df_chart = df[["Chỉ tiêu", "Kế hoạch", "Thực hiện"]]

            st.subheader("📊 So sánh Kế hoạch vs Thực hiện")

            fig, ax = plt.subplots(figsize=(10, 5))
            width = 0.35
            x = range(len(df_chart))

            ax.bar([p - width/2 for p in x], df_chart["Kế hoạch"], width=width, label="Kế hoạch")
            ax.bar([p + width/2 for p in x], df_chart["Thực hiện"], width=width, label="Thực hiện")

            ax.set_xticks(x)
            ax.set_xticklabels(df_chart["Chỉ tiêu"], rotation=45, ha="right")
            ax.legend()

            st.pyplot(fig)
        else:
            st.warning("⚠️ File chưa có đủ cột 'Chỉ tiêu', 'Kế hoạch' và 'Thực hiện' để vẽ biểu đồ.")
    else:
        st.info("👉 Vui lòng import dữ liệu trước ở tab **Import KPI Data**.")
