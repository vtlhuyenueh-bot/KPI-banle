import streamlit as st
import pandas as pd
import plotly.express as px

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
            # Đọc thử file Excel mà không chỉ định header
            df_raw = pd.read_excel(uploaded_file, None)

            # Lấy sheet đầu tiên
            first_sheet = list(df_raw.keys())[0]
            df = df_raw[first_sheet]

            # Tìm dòng nào chứa "Chỉ tiêu"
            header_row = None
            for i, row in df.iterrows():
                if "Chỉ tiêu" in row.values:
                    header_row = i
                    break

            if header_row is not None:
                # Đọc lại file với header đúng
                df = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=header_row)
                st.success("✅ File đã được tải lên thành công!")
                st.dataframe(df)
                st.session_state["kpi_data"] = df
            else:
                st.error("❌ Không tìm thấy dòng tiêu đề chứa 'Chỉ tiêu'. Vui lòng kiểm tra lại file.")
        except Exception as e:
            st.error(f"Lỗi khi đọc file: {e}")
    else:
        st.info("👉 Vui lòng upload file KPI (.xlsx hoặc .xls)")

# Tab 2: Dashboard KPI
with tab_dashboard:
    st.header("📊 Dashboard KPI")

    if "kpi_data" in st.session_state:
        df = st.session_state["kpi_data"]

        # Kiểm tra các cột cần thiết
        required_cols = ["Chỉ tiêu", "Kế hoạch", "Thực hiện"]
        if all(col in df.columns for col in required_cols):

            # Bộ lọc theo nhóm (nếu có cột 'Phân nhóm chỉ tiêu')
            if "Phân nhóm chỉ tiêu" in df.columns:
                nhom_options = df["Phân nhóm chỉ tiêu"].dropna().unique().tolist()
                nhom_selected = st.multiselect("🔎 Chọn nhóm chỉ tiêu", options=nhom_options, default=nhom_options)

                if nhom_selected:
                    df = df[df["Phân nhóm chỉ tiêu"].isin(nhom_selected)]

            # Hiển thị thống kê
            st.subheader("📌 Dữ liệu đã lọc")
            st.dataframe(df)

            # Biểu đồ
            st.subheader("📊 So sánh KPI")
            fig = px.bar(
                df,
                x="Chỉ tiêu",
                y=["Kế hoạch", "Thực hiện"],
                barmode="group",
                color_discrete_sequence=["#1f77b4", "#ff7f0e"],
                title="So sánh Kế hoạch và Thực hiện theo Chỉ tiêu"
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning(f"⚠️ File chưa có đủ cột {required_cols} để vẽ biểu đồ.")
    else:
        st.info("👉 Vui lòng import dữ liệu trước ở tab **Import KPI Data**.")
