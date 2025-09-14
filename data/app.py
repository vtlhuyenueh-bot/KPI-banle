import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import unicodedata
import re
from io import BytesIO

st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("📊 KPI Dashboard - Bán lẻ")

# ====== HÀM HỖ TRỢ ======
def strip_accents(s: str) -> str:
    nk = unicodedata.normalize("NFKD", str(s))
    return "".join([c for c in nk if not unicodedata.combining(c)])

def normalize_col(s: str) -> str:
    s = strip_accents(s).lower().strip()
    s = re.sub(r'[%\(\)\[\]\{\}\-_/\\,;:\"]', ' ', s)
    s = re.sub(r'[^0-9a-z\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str)
                         .str.replace(",", "", regex=False)
                         .str.replace("%", "", regex=False)
                         .str.strip(),
                         errors="coerce")

# ====== UPLOAD FILE ======
uploaded_file = st.file_uploader("📂 Tải file Excel KPI (mỗi sheet = 1 cán bộ)", type=["xlsx"])
if not uploaded_file:
    st.info("👆 Vui lòng upload file Excel để bắt đầu.")
    st.stop()

try:
    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names
    st.sidebar.success(f"📑 File có {len(sheets)} sheet (cán bộ).")
except Exception as e:
    st.error(f"❌ Không đọc được file: {e}")
    st.stop()

# ====== ĐỌC DỮ LIỆU ======
all_dfs = []
summary_rows = []

for sheet in sheets:
    df = pd.read_excel(uploaded_file, sheet_name=sheet)
    orig_cols = list(df.columns)
    norm_map = {orig: normalize_col(orig) for orig in orig_cols}

    required_lookup = {
        "chi tieu": "Chỉ tiêu",
        "trong so": "Trọng số",
        "ke hoach": "Kế hoạch",
        "thuc hien": "Thực hiện"
    }

    col_rename = {}
    for req_norm, canonical in required_lookup.items():
        found = next((orig for orig, n in norm_map.items() if req_norm in n), None)
        if not found:
            st.error(f"❌ Sheet '{sheet}' thiếu cột '{canonical}'. Header: {orig_cols}")
            st.stop()
        col_rename[found] = canonical

    df = df.rename(columns=col_rename)

    # Chuẩn hóa dữ liệu số
    df["Trọng số"] = to_num(df["Trọng số"]).fillna(0)
    if df["Trọng số"].sum() > 1.1:  # nếu nhập 30 thay vì 0.3
        df["Trọng số"] = df["Trọng số"] / 100.0

    df["Kế hoạch"] = to_num(df["Kế hoạch"]).fillna(0)
    df["Thực hiện"] = to_num(df["Thực hiện"]).fillna(0)

    # % hoàn thành
    df["%HT"] = df.apply(
        lambda r: (r["Thực hiện"] / r["Kế hoạch"]) if r["Kế hoạch"] else 0,
        axis=1
    )
    df["%HT"] = df["%HT"].replace([np.inf, -np.inf], 0).fillna(0)

    # Điểm = min(%HT,1) * Trọng số
    df["Điểm"] = df.apply(lambda r: min(r["%HT"], 1) * r["Trọng số"], axis=1)

    df["Nhân viên"] = sheet
    all_dfs.append(df)

    # Tổng hợp cho CB
    summary_rows.append({
        "Nhân viên": sheet,
        "Điểm KPI": round(df["Điểm"].sum(), 4),
        "%HT chung": round((df["Thực hiện"].sum() / df["Kế hoạch"].sum() * 100) if df["Kế hoạch"].sum() else 0, 2),
        "Kế hoạch tổng": df["Kế hoạch"].sum(),
        "Thực hiện tổng": df["Thực hiện"].sum()
    })

full_df = pd.concat(all_dfs, ignore_index=True)
summary_df = pd.DataFrame(summary_rows).sort_values("Điểm KPI", ascending=False).reset_index(drop=True)

# ====== DASHBOARD ======
st.subheader("🏆 Bảng xếp hạng KPI")
st.dataframe(summary_df, use_container_width=True)

# Biểu đồ Top 5
st.subheader("🥇 Top 5 cán bộ")
fig_top = px.bar(summary_df.head(5), x="Nhân viên", y="Điểm KPI", text="Điểm KPI", color="Nhân viên")
st.plotly_chart(fig_top, use_container_width=True)

# Biểu đồ Bottom 5
if len(summary_df) > 5:
    st.subheader("⚠️ Bottom 5 cán bộ")
    fig_bottom = px.bar(summary_df.tail(5), x="Nhân viên", y="Điểm KPI", text="Điểm KPI", color="Nhân viên")
    st.plotly_chart(fig_bottom, use_container_width=True)

# Chi tiết từng CB
st.subheader("🔎 Phân tích chi tiết")
sel = st.selectbox("Chọn nhân viên", summary_df["Nhân viên"].tolist())
if sel:
    dd = full_df[full_df["Nhân viên"] == sel].copy()
    st.markdown(f"### 📌 Chi tiết KPI: **{sel}**")
    st.dataframe(dd[["Chỉ tiêu","Trọng số","Kế hoạch","Thực hiện","%HT","Điểm"]], use_container_width=True)

    fig_cmp = px.bar(dd, x="Chỉ tiêu", y=["Kế hoạch","Thực hiện"],
                     barmode="group", text_auto=True,
                     title=f"So sánh Kế hoạch vs Thực hiện - {sel}")
    st.plotly_chart(fig_cmp, use_container_width=True)

# ====== DOWNLOAD ======
def to_excel_bytes(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Summary")
    return out.getvalue()

st.download_button("⬇️ Tải file tổng hợp (Excel)", data=to_excel_bytes(summary_df),
                   file_name="KPI_summary.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
