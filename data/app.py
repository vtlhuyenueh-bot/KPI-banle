# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import unicodedata
import re
from io import BytesIO

st.set_page_config(page_title="KPI Dashboard - Robust Header", layout="wide")
st.title("📊 KPI Dashboard (Header normalization)")

def strip_accents(s: str) -> str:
    s = str(s)
    nk = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nk if not unicodedata.combining(c)])

def normalize_col(s: str) -> str:
    s = strip_accents(s).lower().strip()
    # remove common punctuation and percent/parenthesis chars -> replace by space
    s = re.sub(r'[%\(\)\[\]\{\}\-_/\\,;:\"]', ' ', s)
    # keep only alnum and spaces
    s = re.sub(r'[^0-9a-z\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str)
                         .str.replace(",", "", regex=False)
                         .str.replace("%", "", regex=False)
                         .str.strip(),
                         errors="coerce")

show_debug = st.sidebar.checkbox("Hiện debug header mapping", value=False)

uploaded_file = st.file_uploader("Tải file KPI (.xlsx) (mỗi sheet = 1 nhân viên)", type=["xlsx"])
if not uploaded_file:
    st.info("Upload file Excel chứa các sheet nhân viên để bắt đầu.")
    st.stop()

try:
    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names
    st.sidebar.success(f"File chứa {len(sheets)} sheet")
except Exception as e:
    st.error(f"Không đọc được file: {e}")
    st.stop()

all_dfs = []
summary_rows = []

for sheet in sheets:
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet)
    except Exception as e:
        st.error(f"Lỗi đọc sheet '{sheet}': {e}")
        st.stop()

    orig_cols = list(df.columns)
    norm_map = {orig: normalize_col(orig) for orig in orig_cols}

    if show_debug:
        st.sidebar.markdown(f"**Sheet:** {sheet}")
        st.sidebar.write("Headers (orig):", orig_cols)
        st.sidebar.write("Headers (normalized):", list(norm_map.values()))

    # tìm các cột cần thiết bằng cách dò substring trên tên đã chuẩn hóa
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
            # nếu không tìm thấy, show lỗi kèm thông tin debug
            raise ValueError(
                f"❌ Sheet '{sheet}' thiếu cột tương ứng với '{canonical}'.\n"
                f"Header thực tế: {orig_cols}\n"
                f"Header đã chuẩn hóa: {list(norm_map.values())}\n"
                f"Lưu ý: các tên cột hợp lệ ví dụ: 'Chỉ tiêu', 'Trọng số', 'Kế hoạch', 'Thực hiện' (các biến thể như 'Trọng số (%)' sẽ được nhận diện)."
            )
        col_rename[found] = canonical

    # rename sang tên chính thức
    df = df.rename(columns=col_rename)

    # convert numeric columns
    df["Trọng số"] = to_num(df["Trọng số"]).fillna(0)
    # Nếu tổng trọng số lớn hơn 1.1 -> có khả năng nhập dạng 30 (tức 30%) => chia 100
    if df["Trọng số"].sum() > 1.1:
        df["Trọng số"] = df["Trọng số"] / 100.0

    df["Kế hoạch"] = to_num(df["Kế hoạch"]).fillna(0)
    df["Thực hiện"] = to_num(df["Thực hiện"]).fillna(0)

    # tránh chia cho 0
    df["% hoàn thành"] = df.apply(lambda r: (r["Thực hiện"] / r["Kế hoạch"]) if r["Kế hoạch"] not in (0, np.nan) else 0, axis=1)
    df["% hoàn thành"] = df["% hoàn thành"].replace([np.inf, -np.inf], 0).fillna(0)

    # tính điểm (nếu column 'Điểm' đã có thì vẫn ghi đè để đảm bảo consistent)
    df["Điểm"] = df["% hoàn thành"] * df["Trọng số"]

    # lưu tên nhân viên từ sheet
    df["Nhân viên"] = sheet

    all_dfs.append(df)

    total_score = df["Điểm"].sum()
    total_plan = df["Kế hoạch"].sum()
    total_actual = df["Thực hiện"].sum()
    overall_pct = (total_actual / total_plan) if total_plan != 0 else 0

    summary_rows.append({
        "Nhân viên": sheet,
        "Điểm KPI": round(total_score, 6),
        "%HT chung": round(overall_pct * 100, 2),
        "Kế hoạch tổng": total_plan,
        "Thực hiện tổng": total_actual
    })

# gộp
full_df = pd.concat(all_dfs, ignore_index=True)
summary_df = pd.DataFrame(summary_rows).sort_values("Điểm KPI", ascending=False).reset_index(drop=True)

# hiển thị
st.subheader("📋 Bảng tổng hợp KPI")
st.dataframe(summary_df, use_container_width=True)

st.subheader("🏆 Ranking theo Điểm KPI")
fig_rank = px.bar(summary_df, x="Nhân viên", y="Điểm KPI", text="Điểm KPI")
st.plotly_chart(fig_rank, use_container_width=True)

st.subheader("🔎 Phân tích chi tiết")
sel = st.selectbox("Chọn nhân viên", summary_df["Nhân viên"].tolist())
if sel:
    dd = full_df[full_df["Nhân viên"] == sel].copy()
    st.markdown(f"### Chi tiết: **{sel}**")
    st.dataframe(dd, use_container_width=True)

    fig_cmp = px.bar(dd, x="Chỉ tiêu", y=["Kế hoạch", "Thực hiện"], barmode="group", text_auto=True,
                     title=f"So sánh Kế hoạch vs Thực hiện - {sel}")
    st.plotly_chart(fig_cmp, use_container_width=True)

# download tổng hợp
def to_excel_bytes(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Summary")
    return out.getvalue()

st.download_button("⬇️ Tải file tổng hợp (Excel)", data=to_excel_bytes(summary_df),
                   file_name="KPI_summary.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
