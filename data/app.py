# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

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
    "chitieu": ["chi tieu", "chitieu", "chi tieu", "chi-tieu", "kpi", "ten chi tieu", "ten"],
    "kehoach": ["ke hoach", "kehoach", "kế hoạch", "ke-hoach", "target", "plan"],
    "thuchien": ["thuc hien", "thuchien", "thực hiện", "thuc-hien", "actual", "achieved", "result"]
}

def find_best_header_row(df_sheet, max_rows=20):
    # scan first max_rows rows to find a row containing many token matches
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
    # choose row with highest score (require at least 1 match)
    best = max(scores, key=lambda x: x[1])
    return best[0] if best[1] > 0 else None

def auto_map_columns(cols):
    # cols: list of actual column names
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
    st.header("Tải file KPI (Excel)")
    uploaded_file = st.file_uploader("Upload file KPI (.xlsx) — không cần chỉnh header", type=["xlsx"])

    if uploaded_file:
        try:
            # read all sheets without header to inspect raw rows
            sheets = pd.read_excel(uploaded_file, sheet_name=None, header=None)
            first_sheet = list(sheets.keys())[0]
            raw = sheets[first_sheet]

            # try to find header row
            header_row = find_best_header_row(raw, max_rows=30)
            if header_row is not None:
                df = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=header_row)
                st.success(f"Đã tự động phát hiện header ở hàng {header_row+1}")
            else:
                # fallback: read with default header=0
                df = pd.read_excel(uploaded_file, sheet_name=first_sheet, header=0)
                st.warning("Không xác định được header tự động — dùng hàng đầu tiên làm header (bạn có thể map cột tay).")

            # show sample and columns
            st.subheader("Preview (5 dòng đầu)")
            st.dataframe(df.head())

            st.subheader("Tên cột hiện có (raw)")
            col_list = df.columns.tolist()
            col_display = {c: normalize_text(c) for c in col_list}
            st.write(col_display)

            # try auto-mapping
            auto_map = auto_map_columns(col_list)
            st.subheader("Auto-mapping (gợi ý)")
            st.write(auto_map)

            # if any missing mapping, allow manual select from columns
            need = []
            for key in ["chitieu", "kehoach", "thuchien"]:
                if not auto_map.get(key):
                    need.append(key)

            # UI to confirm/adju
