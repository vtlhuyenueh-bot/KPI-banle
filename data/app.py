# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

st.set_page_config(page_title="KPI Tracker", layout="wide")
st.title("📈 KPI Tracker — Auto Detect Header & Mapping")

# ---------- Helpers ----------
def normalize_text(s):
    if pd.isna(s):
        return ""
    s = str(s).strip()
    # remove unicode accents
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("-", " ").replace("_", " ").lower()
    s = " ".join(s.split())
    return s

# tokens để detect cột
TOKENS = {
    "chitieu": ["chi tieu", "chitieu", "kpi", "ten chi tieu", "ten"],
    "kehoach": ["ke hoach", "kehoach", "kế hoạch", "target", "plan"],
    "thuchien": ["thuc hien", "thuchien", "thực hiện", "actual", "achieved", "result"]
}

def find_best_header_row(df_sheet, max_rows=20):
    scores = []
    for i in range(min(max_rows, len(df_sheet))):
        row = df_sheet.iloc[i].astype(str).fillna("").tolist()
        norm_row = [normalize_text(c) for c in row]
        score = 0
        for token_list in TOKENS.values():
            for tok in token_list:
                if any(tok in cell for cell in norm_row):
                    score += 1
                    break
        scores.append((i, score))
    best = max(scores, key=lambda x: x[1])
    return best[0] if best[1] > 0 else None

def auto_map_columns(cols):
    norm_cols = [normalize_text(c) for c in cols]
    mapping = {}
    for logical, token_list in TOKENS.items():
        found = None
        for i, nc in enumerate(norm_cols):
            for tok in token_list:
                if tok in nc:
                    found = cols[i]
                    break
            if found:
                break
        mapping[logical] = found
    return mapping

# ---------- UI ----------
tab1, tab2 = st.tabs(["📂 Import KPI Data", "📊 Dashboard"])

with tab1:
    st.header("📂 Upload file KPI (Excel)")
    uploaded_file = st.file_uploader("Upload file KPI (.xlsx)", type=["xlsx"])

    if uploaded_file:
        try:
            # Đọc tất cả sheet không header để tìm dòng header
            sheets = pd.read_excel(uploaded_file, sheet_name=None, header=None)
            first_sheet = list(sheets.keys())[0]
            raw = sheets[first_sheet]

            # tìm header row
            header_row = find_best_header_row(raw, max_rows=30)
            if header_row is not None:
                df = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=header_row)
                st.success(f"✅ Đã phát hiện header ở dòng {header_row+1}")
            else:
                df = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=0)
                st.warning("⚠️ Không phát hiện header tự động — dùng dòng đầu tiên.")

            st.subheader("👀 Preview dữ liệu (5 dòng đầu)")
            st.dataframe(df.head())

            # hiển thị cột và auto-map
            col_list = df.columns.tolist()
            auto_map = auto_map_columns(col_list)

            st.subheader("🔎 Auto-mapping")
            st.write(auto_map)

            # Cho phép chỉnh tay nếu auto-map bị thiếu
            st.subheader("⚙️ Xác nhận cột")
            col_chitieu = st.selectbox("Chỉ tiêu", options=col_list, index=col_list.index(auto_map["chitieu"]) if auto_map["chitieu"] else 0)
            col_kehoach = st.selectbox("Kế hoạch", options=col_list, index=col_list.index(auto_map["kehoach"]) if auto_map["kehoach"] else 0)
            col_thuchien = st.selectbox("Thực hiện", options=col_list, index=col_list.index(auto_map["thuchien"]) if auto_map["thuchien"] else 0)

            if st.button("Lưu dữ liệu"):
                df_mapped = df.rename(columns={
                    col_chitieu: "Chỉ tiêu",
                    col_kehoach: "Kế hoạch",
                    col_thuchien: "Thực hiện"
                })
                st.session_state["kpi_data"] = df_mapped
                st.success("📥 Dữ liệu đã được lưu, sang tab Dashboard để xem báo cáo.")

        except Exception as e:
            st.error(f"❌ Lỗi khi đọc file: {e}")

with tab2:
    st.header("📊 Dashboard KPI")

    if "kpi_data" in st.session_state:
        df = st.session_state["kpi_data"]

        st.subheader("📋 Dữ liệu chuẩn hóa")
        st.dataframe(df.head())

        st.subheader("📌 Tổng quan")
        st.write(f"- Số dòng dữ liệu: {df.shape[0]}")
        st.write(f"- Số cột dữ liệu: {df.shape[1]}")

        # Biểu đồ
        if all(col in df.columns for col in ["Chỉ tiêu", "Kế hoạch", "Thực hiện"]):
            st.subheader("📈 Biểu đồ so sánh KPI")

            fig = px.bar(
                df,
                x="Chỉ tiêu",
                y=["Kế hoạch", "Thực hiện"],
                barmode="group",
                text_auto=True,
                title="So sánh Kế hoạch vs Thực hiện"
            )
            st.plotly_chart(fig, use_container_width=True)

            # % Hoàn thành
            st.subheader("✅ Tỉ lệ hoàn thành")
            df["% Hoàn thành"] = (df["Thực hiện"] / df["Kế hoạch"] * 100).round(2)
            st.dataframe(df[["Chỉ tiêu", "Kế hoạch", "Thực hiện", "% Hoàn thành"]])

            # Cho phép download file kết quả
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Tải file kết quả (.csv)", data=csv, file_name="kpi_result.csv", mime="text/csv")

        else:
            st.warning("⚠️ File chưa có đủ cột 'Chỉ tiêu', 'Kế hoạch', 'Thực hiện'.")
    else:
        st.info("👉 Vui lòng import dữ liệu trước ở tab **📂 Import KPI Data**.")
