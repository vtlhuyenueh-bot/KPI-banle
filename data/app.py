import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
import traceback

st.set_page_config(page_title="KPI Tracker (auto-header)", layout="wide")
st.title("📈 KPI Tracker — tự động nhận header & map cột")

# ---------- helpers ----------
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

# tokens to detect each logical column
TOKENS = {
    "chitieu": ["chi tieu", "chitieu", "ten chi tieu", "ten", "kpi"],
    "kehoach": ["ke hoach", "kehoach", "ke-hoach", "target", "plan"],
    "thuchien": ["thuc hien", "thuchien", "thuc-hien", "actual", "achieved", "result"]
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

def validate_columns(df):
    required = ["Chỉ tiêu", "Kế hoạch", "Thực hiện"]
    missing = [c for c in required if c not in df.columns]
    return missing

# ---------- UI ----------
tabs = st.tabs(["📂 Import KPI Data", "📊 Dashboard"])

with tabs[0]:
    st.header("Tải file KPI (Excel)")
    uploaded_file = st.file_uploader("Upload file KPI (.xlsx)", type=["xlsx"])

    if uploaded_file:
        try:
            # đọc tất cả sheet không header
            sheets = pd.read_excel(uploaded_file, sheet_name=None, header=None)
            first_sheet = list(sheets.keys())[0]
            raw = sheets[first_sheet]

            # tìm header row
            header_row = find_best_header_row(raw, max_rows=30)
            if header_row is not None:
                df = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=header_row)
                st.success(f"✅ Đã tự động phát hiện header ở hàng {header_row+1}")
            else:
                df = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=0)
                st.warning("⚠️ Không tìm thấy header phù hợp — dùng hàng đầu tiên làm header.")

            st.subheader("📑 Preview (5 dòng đầu)")
            st.dataframe(df.head())

            st.subheader("Tên cột hiện có (raw)")
            col_list = df.columns.tolist()
            st.write(col_list)

            # auto map
            auto_map = auto_map_columns(col_list)
            st.subheader("Auto-mapping (gợi ý)")
            st.write(auto_map)

            # manual adjust
            st.subheader("Chọn lại cột (nếu cần)")
            col_chitieu = st.selectbox("Cột chỉ tiêu", col_list, index=col_list.index(auto_map["chitieu"]) if auto_map["chitieu"] else 0)
            col_kehoach = st.selectbox("Cột kế hoạch", col_list, index=col_list.index(auto_map["kehoach"]) if auto_map["kehoach"] else 0)
            col_thuchien = st.selectbox("Cột thực hiện", col_list, index=col_list.index(auto_map["thuchien"]) if auto_map["thuchien"] else 0)

            df = df.rename(columns={col_chitieu: "Chỉ tiêu", col_kehoach: "Kế hoạch", col_thuchien: "Thực hiện"})
            st.session_state["kpi_data"] = df
            st.success("🎉 Dữ liệu đã sẵn sàng, chuyển sang tab Dashboard để xem biểu đồ.")

        except Exception as e:
            st.error("❌ Lỗi khi đọc file.")
            st.code(traceback.format_exc())

with tabs[1]:
    st.header("📊 Dashboard KPI")

    if "kpi_data" not in st.session_state:
        st.info("👆 Hãy import file Excel ở tab **Import KPI Data** trước.")
    else:
        try:
            df = st.session_state["kpi_data"]

            missing = validate_columns(df)
            if missing:
                st.warning(f"⚠️ File thiếu cột: {', '.join(missing)}. Không thể vẽ biểu đồ.")
            else:
                # convert về số
                for col in ["Kế hoạch", "Thực hiện"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                df = df.dropna(subset=["Kế hoạch", "Thực hiện"])

                if df.empty:
                    st.error("❌ Không có dữ liệu hợp lệ sau khi làm sạch.")
                else:
                    # bar chart
                    fig = px.bar(
                        df,
                        x="Chỉ tiêu",
                        y=["Kế hoạch", "Thực hiện"],
                        barmode="group",
                        text_auto=True,
                        title="So sánh Kế hoạch vs Thực hiện"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # % completion
                    df["% Hoàn thành"] = (df["Thực hiện"] / df["Kế hoạch"] * 100).round(1)
                    fig2 = px.line(
                        df,
                        x="Chỉ tiêu",
                        y="% Hoàn thành",
                        markers=True,
                        title="% Hoàn thành KPI"
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                    st.subheader("📑 Bảng dữ liệu chi tiết")
                    st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error("❌ Có lỗi xảy ra trong quá trình xử lý dữ liệu.")
            st.code(traceback.format_exc())
