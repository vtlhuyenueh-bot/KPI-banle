import streamlit as st
import pandas as pd

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
            st.success("✅ File đã được tải lên thành công!")
            st.dataframe(df)  # Hiển thị trước dữ liệu
            st.session_state["kpi_data"] = df  # Lưu vào session_state để Dashboard dùng
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

        # Nếu có cột "Chỉ tiêu" và "Thực hiện", vẽ biểu đồ
        if "Chỉ tiêu" in df.columns and "Thực hiện" in df.columns:
            import matplotlib.pyplot as plt

            st.subheader("📊 So sánh KPI")

            fig, ax = plt.subplots()
            df.set_index("Chỉ tiêu")[["Thực hiện"]].plot(kind="bar", ax=ax)
            st.pyplot(fig)
        else:
            st.warning("⚠️ File chưa có đủ cột 'Chỉ tiêu' và 'Thực hiện' để vẽ biểu đồ.")
    else:
        st.info("👉 Vui lòng import dữ liệu trước ở tab **Import KPI Data**.")
