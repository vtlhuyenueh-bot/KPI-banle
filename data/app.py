tab_import = st.tabs(["📂 Import KPI Data"])[0]

with tab_import:
    st.subheader("Import file kế hoạch & kết quả KPI")

    plan_file = st.file_uploader("Upload file kế hoạch (Plan)", type=["xlsx", "csv"], key="plan")
    actual_file = st.file_uploader("Upload file kết quả (Actual)", type=["xlsx", "csv"], key="actual")

    if plan_file and actual_file:
        # Đọc file kế hoạch
        if plan_file.name.endswith("csv"):
            df_plan = pd.read_csv(plan_file)
        else:
            df_plan = pd.read_excel(plan_file)

        # Đọc file kết quả
        if actual_file.name.endswith("csv"):
            df_actual = pd.read_csv(actual_file)
        else:
            df_actual = pd.read_excel(actual_file)

        # Kiểm tra cột
        required_plan = {"User", "Month", "KPI Name", "Target"}
        required_actual = {"User", "Month", "KPI Name", "Actual"}

        if not required_plan.issubset(df_plan.columns):
            st.error(f"❌ File kế hoạch phải có các cột: {required_plan}")
        elif not required_actual.issubset(df_actual.columns):
            st.error(f"❌ File kết quả phải có các cột: {required_actual}")
        else:
            # Merge dữ liệu
            df = pd.merge(df_plan, df_actual, on=["User", "Month", "KPI Name"], how="left")

            # Tính KPI %
            df["KPI Score (%)"] = (df["Actual"] / df["Target"] * 100).round(2)
            df["KPI Score (%)"] = df["KPI Score (%)"].apply(lambda x: min(x, 120) if pd.notnull(x) else 0)

            # Hiển thị
            st.subheader("📊 Kết quả KPI")
            st.dataframe(df)

            # Biểu đồ theo nhân viên
            fig = px.bar(df, x="KPI Name", y="KPI Score (%)", color="User", barmode="group", facet_col="Month")
            st.plotly_chart(fig)

            # Trung bình theo User
            avg_df = df.groupby("User")["KPI Score (%)"].mean().reset_index()
            st.subheader("📌 Điểm KPI trung bình theo nhân viên")
            st.dataframe(avg_df)
            fig2 = px.bar(avg_df, x="User", y="KPI Score (%)", color="User")
            st.plotly_chart(fig2)
