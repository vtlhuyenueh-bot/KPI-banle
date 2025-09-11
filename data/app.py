import streamlit as st
import pandas as pd
import json
import os
import bcrypt
import plotly.express as px
from datetime import datetime

DATA_FILE = "data/kpi_data.json"

# ------------------ Helper functions ------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "kpis": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

# ------------------ Auth ------------------
def register(username, password, role="staff"):
    data = load_data()
    if username in data["users"]:
        return False, "❌ Username đã tồn tại"
    data["users"][username] = {"password": hash_password(password), "role": role}
    save_data(data)
    return True, "✅ Đăng ký thành công!"

def login(username, password):
    data = load_data()
    if username not in data["users"]:
        return False, "❌ Sai username"
    user = data["users"][username]
    if not check_password(password, user["password"]):
        return False, "❌ Sai password"
    return True, user["role"]

# ------------------ KPI ------------------
def add_kpi(user, kpi_name, target, actual, month):
    data = load_data()
    data["kpis"].append({
        "user": user,
        "month": month,
        "kpi_name": kpi_name,
        "target": target,
        "actual": actual
    })
    save_data(data)

def get_user_kpis(user):
    data = load_data()
    return [k for k in data["kpis"] if k["user"] == user]

def get_all_kpis():
    data = load_data()
    return data["kpis"]

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="KPI Tracker", layout="wide")
st.title("📊 KPI Tracker App")

# Session
if "auth" not in st.session_state:
    st.session_state.auth = None
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None

# Tabs
tab_login, tab_input, tab_personal, tab_dashboard = st.tabs(
    ["🔑 Đăng nhập/Đăng ký", "📝 Nhập KPI", "🙋 KPI Cá nhân", "📈 Dashboard Nhóm"]
)

# ---- Tab Login ----
with tab_login:
    st.subheader("Đăng nhập")
    lg_user = st.text_input("Username", key="lg_user")
    lg_pass = st.text_input("Password", type="password", key="lg_pass")
    if st.button("Đăng nhập"):
        ok, msg = login(lg_user, lg_pass)
        if ok:
            st.success("Đăng nhập thành công")
            st.session_state.auth = True
            st.session_state.user = lg_user
            st.session_state.role = msg
        else:
            st.error(msg)

    st.subheader("Đăng ký")
    rg_user = st.text_input("New Username", key="rg_user")
    rg_pass = st.text_input("New Password", type="password", key="rg_pass")
    rg_role = st.selectbox("Role", ["staff", "manager"])
    if st.button("Đăng ký"):
        ok, msg = register(rg_user, rg_pass, rg_role)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

# ---- Tab Input ----
with tab_input:
    if not st.session_state.auth:
        st.warning("⚠️ Vui lòng đăng nhập trước")
    else:
        st.subheader("Nhập KPI cá nhân")
        kpi_name = st.text_input("Tên KPI")
        target = st.number_input("Chỉ tiêu (Target)", min_value=0.0)
        actual = st.number_input("Thực hiện (Actual)", min_value=0.0)
        month = st.text_input("Tháng (YYYY-MM)", value=datetime.today().strftime("%Y-%m"))
        if st.button("Lưu KPI"):
            add_kpi(st.session_state.user, kpi_name, target, actual, month)
            st.success("✅ KPI đã được lưu!")

# ---- Tab Personal ----
with tab_personal:
    if not st.session_state.auth:
        st.warning("⚠️ Vui lòng đăng nhập trước")
    else:
        st.subheader(f"KPI của {st.session_state.user}")
        user_kpis = get_user_kpis(st.session_state.user)
        if user_kpis:
            df = pd.DataFrame(user_kpis)
            st.dataframe(df)
            fig = px.bar(df, x="kpi_name", y=["target", "actual"], barmode="group", color_discrete_map={"target": "red", "actual": "green"})
            st.plotly_chart(fig)
        else:
            st.info("Chưa có KPI nào")

# ---- Tab Dashboard ----
with tab_dashboard:
    if not st.session_state.auth:
        st.warning("⚠️ Vui lòng đăng nhập trước")
    elif st.session_state.role != "manager":
        st.error("❌ Chỉ Manager mới xem được dashboard nhóm")
    else:
        st.subheader("Dashboard KPI Nhóm")
        all_kpis = get_all_kpis()
        if all_kpis:
            df = pd.DataFrame(all_kpis)
            st.dataframe(df)
            fig = px.bar(df, x="user", y="actual", color="kpi_name", barmode="group")
            st.plotly_chart(fig)
        else:
            st.info("Chưa có dữ liệu KPI")
