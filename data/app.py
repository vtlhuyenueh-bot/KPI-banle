import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Kinh doanh", layout="wide")

st.title("📊 Dashboard Kinh doanh bán lẻ")

uploaded_file = st.file_uploader("Tải file Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Đọc tất cả sheet
        xls = pd.ExcelFile(uploaded_file)
        sheets = xls.sheet_names
        st.sidebar.success(f"Đã nhận file có {len(sheets)} sheet")

        all_data = []

        for sheet in sheets:
            df = pd.read_excel(uploaded_file, sheet_name=sheet)

            # Chuẩn hóa header
            df.columns = df.columns.str.strip().str.lower()

            # Các cột bắt buộc
            required_cols = ["chỉ tiêu", "trọng số", "kế hoạch", "thực hiện"]

            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(
                        f"❌ Sheet '{sheet}' thiếu cột '{col}'. "
                        f"Header thực tế: {df.columns.tolist()}"
                    )

            # Thêm cột tên sheet để phân biệt phòng/nhân viên
            df["nhân viên"] = sheet
            all_data.append(df)

        # Gộp toàn bộ dữ liệu
        data = pd.concat(all_data, ignore_index=True)

        # Tính % hoàn thành
        data["% hoàn thành"] = data["thực hiện"] / data["kế hoạch"] * 100

        # Hiển thị bảng
        st.subheader("📌 Dữ liệu tổng hợp")
        st.dataframe(data)

        # Vẽ biểu đồ
        st.subheader("📈 So sánh Kế hoạch vs Thực hiện")
        fig = px.bar(
            data,
            x="chỉ tiêu",
            y=["kế hoạch", "thực hiện"],
            color="nhân viên",
            barmode="group",
            title="So sánh kế hoạch - thực hiện theo nhân viên",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

        # Biểu đồ % hoàn thành
        st.subheader("🔥 Tỷ lệ hoàn thành")
        fig2 = px.bar(
            data,
            x="chỉ tiêu",
            y="% hoàn thành",
            color="nhân viên",
            title="% Hoàn thành theo nhân viên",
            text_auto=".1f"
        )
        st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi xử lý file: {e}")
else:
    st.info("👆 Vui lòng tải file Excel để bắt đầu")
