# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="KPI Dashboard", layout="wide")
st.title("📊 KPI Dashboard - Tổng hợp & Ranking")

def to_num(s):
    return pd.to_numeric(s.astype(str)
                         .str.replace(",", "", regex=False)
                         .str.replace("%", "", regex=False),
                         errors="coerce")

def read_kpi_excel(f):
    # đọc tất cả sheet -> dict of DataFrames
    xl = pd.read_excel(f, sheet_name=None)
    results = {}
    for sheet, df in xl.items():
        df = df.copy()
        df.columns = [c.strip() for c in df.columns]
        # Chuẩn hóa các cột bắt buộc
        for col in ["Chỉ tiêu", "Trọng số", "Kế hoạch", "Thực hiện"]:
            if col not in df.columns:
                raise ValueError(f"Sheet '{sheet}' thiếu cột '{col}'")
        # numeric convert
        df["Trọng số"] = to_num(df["Trọng số"]).fillna(0)
        df["Kế hoạch"] = to_num(df["Kế hoạch"]).fillna(0)
        df["Thực hiện"] = to_num(df["Thực hiện"]).fillna(0)
        # Nếu trọng số ở dạng % (tổng >1) thì chia 100
        if df["Trọng số"].sum() > 1.1:
            df["Trọng số"] = df["Trọng số"] / 100.0
        # tính % hoàn thành & điểm
        df["%HT"] = df.apply(lambda r: (r["Thực hiện"]/r["Kế hoạch"])
                             if r["Kế hoạch"] and r["Kế hoạch"] != 0 else 0, axis=1)
        df["%HT"] = df["%HT"].replace([np.inf, -np.inf], 0).fillna(0)
        df["Điểm"] = df["%HT"] * df["Trọng số"]
        results[sheet] = df
    return results

# Upload file hoặc dùng file trong repo (nếu bạn lưu File KPI trong repo)
uploaded = st.file_uploader("Tải lên file KPI (.xlsx) (mỗi sheet = 1 nhân viên)", type=["xlsx"])
use_repo_file = st.checkbox("Hoặc dùng file: 'data/File KPI.xlsx' trong repo (nếu đã push lên GitHub)", value=False)

data_file = None
if uploaded:
    data_file = uploaded
elif use_repo_file:
    try:
        data_file = "data/File KPI.xlsx"
        open(data_file, "rb").close()
    except Exception:
        st.error("Không tìm thấy file data/File KPI.xlsx trong repo. Hãy upload hoặc push file vào repo.")
        st.stop()
else:
    st.info("Upload file mẫu (File KPI.xlsx) để bắt đầu.")
    st.stop()

# process
try:
    kpi_dict = read_kpi_excel(data_file)
except Exception as e:
    st.error(f"Lỗi đọc file: {e}")
    st.stop()

# build summary
rows = []
for nv, df in kpi_dict.items():
    total_score = df["Điểm"].sum()
    total_plan = df["Kế hoạch"].sum()
    total_actual = df["Thực hiện"].sum()
    overall_pct = (total_actual/total_plan) if total_plan != 0 else 0
    rows.append({
        "Nhân viên": nv,
        "Điểm KPI": round(total_score, 4),
        "%HT chung": round(overall_pct*100, 2),
        "Kế hoạch tổng": total_plan,
        "Thực hiện tổng": total_actual
    })
summary = pd.DataFrame(rows).sort_values("Điểm KPI", ascending=False).reset_index(drop=True)

# UI: Summary + ranking
st.subheader("📋 Bảng tóm tắt KPI")
st.dataframe(summary, use_container_width=True)

st.subheader("🏆 Ranking theo Điểm KPI")
fig = px.bar(summary, x="Nhân viên", y="Điểm KPI", text="Điểm KPI")
st.plotly_chart(fig, use_container_width=True)

# Drill-down nhân viên
st.subheader("🔎 Xem chi tiết nhân viên")
sel = st.selectbox("Chọn nhân viên", summary["Nhân viên"].tolist())
if sel:
    df_sel = kpi_dict[sel]
    st.markdown(f"### Chi tiết: **{sel}**")
    st.dataframe(df_sel, use_container_width=True)

    fig2 = px.bar(df_sel, x="Chỉ tiêu", y=["Kế hoạch", "Thực hiện"], barmode="group", text_auto=True,
                  title=f"So sánh Kế hoạch vs Thực hiện - {sel}")
    st.plotly_chart(fig2, use_container_width=True)

# Download summary
def to_excel_bytes(df):
    out = BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Summary")
    return out.getvalue()

st.download_button("⬇️ Tải về file tổng hợp (Excel)", data=to_excel_bytes(summary),
                   file_name="KPI_summary.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
