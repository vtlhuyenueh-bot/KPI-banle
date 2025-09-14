import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard KPI", layout="wide")

st.title("📊 Dashboard KPI - Cá nhân & Xếp hạng")

uploaded_file = st.file_uploader("📂 Tải file Excel KPI", type=["xlsx"])

if uploaded_file:
    try:
        # Đọc toàn bộ sheet
        xls = pd.ExcelFile(uploaded_file)
        all_sheets = xls.sheet_names

        data_nhanvien = {}

        for sheet in all_sheets:
            df = pd.read_excel(uploaded_file, sheet_name=sheet)

            # Chuẩn hóa header
            df.columns = df.columns.str.strip().str.lower()

            # Mapping linh hoạt
            mapping = {
                "chỉ tiêu": ["chỉ tiêu"],
                "trọng số": ["trọng số", "trọng số (%)"],
                "kế hoạch": ["kế hoạch"],
                "thực hiện": ["thực hiện"]
            }

            col_map = {}
            for std_col, variants in mapping.items():
                for v in variants:
                    if v in df.columns:
                        col_map[v] = std_col
                        break

            if len(set(col_map.values())) < 4:
                st.error(f"❌ Sheet '{sheet}' thiếu cột. Header thực tế: {list(df.columns)}")
                st.stop()

            df = df.rename(columns={k: v for k, v in col_map.items()})

            # Tính toán
            df["% Hoàn thành"] = df["thực hiện"] / df["kế hoạch"] * 100
            df["Điểm"] = df["% Hoàn thành"] * df["trọng số"] / 100

            # Làm đẹp số liệu
            for col in ["trọng số", "kế hoạch", "thực hiện", "% Hoàn thành", "Điểm"]:
                df[col] = df[col].astype(float).round(2)

            data_nhanvien[sheet] = df

        # Chọn nhân viên
        nhan_vien = st.selectbox("👤 Chọn nhân viên", list(data_nhanvien.keys()))

        if nhan_vien:
            df_nv = data_nhanvien[nhan_vien]

            st.subheader(f"📌 KPI chi tiết - {nhan_vien}")
            st.dataframe(df_nv.style.format({
                "trọng số": "{:.2f}",
                "kế hoạch": "{:.2f}",
                "thực hiện": "{:.2f}",
                "% Hoàn thành": "{:.2f}",
                "Điểm": "{:.2f}"
            }))

            # Biểu đồ
            fig = px.bar(
                df_nv,
                x="chỉ tiêu",
                y=["kế hoạch", "thực hiện"],
                barmode="group",
                title=f"So sánh Kế hoạch vs Thực hiện - {nhan_vien}"
            )
            fig.update_layout(yaxis_tickformat=".2f")
            st.plotly_chart(fig, use_container_width=True)

        # Xếp hạng toàn bộ
        st.subheader("🏆 Xếp hạng cán bộ")
        ranking = []
        for name, df in data_nhanvien.items():
            tong_diem = df["Điểm"].sum()
            ranking.append({"Nhân viên": name, "Tổng điểm": round(tong_diem, 2)})

        df_rank = pd.DataFrame(ranking).sort_values("Tổng điểm", ascending=False).reset_index(drop=True)
        st.dataframe(df_rank.style.format({"Tổng điểm": "{:.2f}"}))

    except Exception as e:
        st.error(f"⚠️ Lỗi xử lý file: {e}")
