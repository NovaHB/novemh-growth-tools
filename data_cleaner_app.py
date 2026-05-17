import streamlit as st
import pandas as pd
import numpy as np
import io

# ============================================
# APP CONFIG
# ============================================
st.set_page_config(page_title="Data Cleaner Tool", page_icon="🧹", layout="wide")
st.title("🧹 Data Cleaning Tool")
st.caption("Upload a CSV or Excel file, choose your cleaning options, and download a clean dataset.")

# ============================================
# FILE UPLOAD
# ============================================
uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file:
    try:
        # --- Load CSV or Excel ---
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            excel_file = pd.ExcelFile(uploaded_file)
            if len(excel_file.sheet_names) > 1:
                sheet = st.selectbox("Select sheet to clean", excel_file.sheet_names)
            else:
                sheet = excel_file.sheet_names[0]
            df = pd.read_excel(uploaded_file, sheet_name=sheet)

        st.success(f"✅ File loaded — {df.shape[0]:,} rows, {df.shape[1]} columns")

        # Preview raw data
        with st.expander("👀 Preview Raw Data"):
            st.dataframe(df.head(20))

        # Raw data stats
        with st.expander("📊 Raw Data Summary"):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Rows", f"{df.shape[0]:,}")
            col2.metric("Total Columns", df.shape[1])
            col3.metric("Duplicate Rows", f"{df.duplicated().sum():,}")
            col4.metric("Missing Values", f"{df.isnull().sum().sum():,}")

        # ============================================
        # CLEANING OPTIONS
        # ============================================
        st.divider()
        st.subheader("🛠️ Cleaning Options")
        st.caption("Select what you want to apply to your dataset.")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown("**🔁 Duplicates**")
            remove_duplicates = st.checkbox("Remove duplicate rows")
            remove_empty_cols = st.checkbox("Remove columns that are mostly empty (>70% missing)")

        with col_b:
            st.markdown("**✂️ Whitespace & Text**")
            trim_whitespace = st.checkbox("Trim whitespace from text fields")
            fix_casing = st.checkbox("Standardize text casing")
            casing_option = st.selectbox(
                "Casing format",
                ["lowercase", "UPPERCASE", "Title Case"],
                disabled=not fix_casing
            )

        with col_c:
            st.markdown("**❓ Missing Values**")
            handle_missing = st.checkbox("Handle missing values")
            missing_option = st.selectbox(
                "Fill missing values with",
                ["Drop rows with missing values", "Fill numeric with mean", "Fill numeric with median", "Fill numeric with 0", "Fill text with 'Unknown'"],
                disabled=not handle_missing
            )

        st.divider()

        col_d, col_e = st.columns(2)

        with col_d:
            st.markdown("**📅 Date Formatting**")
            format_dates = st.checkbox("Standardize date columns")
            date_format = st.selectbox(
                "Date format",
                ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"],
                disabled=not format_dates
            )

        with col_e:
            st.markdown("**🔢 Data Types**")
            fix_numerics = st.checkbox("Convert numeric columns stored as text to numbers")
            remove_outliers = st.checkbox("Flag and remove outliers in numeric columns (3σ rule)")

        # ============================================
        # RUN CLEANING
        # ============================================
        st.divider()
        run_cleaning = st.button("🧹 Clean My Data", type="primary")

        if run_cleaning:
            cleaned_df = df.copy()
            cleaning_log = []
            errors_log = []

            # --- Remove duplicates ---
            if remove_duplicates:
                try:
                    before = len(cleaned_df)
                    cleaned_df = cleaned_df.drop_duplicates()
                    removed = before - len(cleaned_df)
                    cleaning_log.append(f"✅ Removed {removed:,} duplicate rows")
                except Exception as e:
                    errors_log.append(f"❌ Duplicate removal failed: {str(e)}")

            # --- Remove mostly empty columns ---
            if remove_empty_cols:
                try:
                    before_cols = cleaned_df.shape[1]
                    threshold = 0.7
                    cleaned_df = cleaned_df.loc[:, cleaned_df.isnull().mean() < threshold]
                    removed_cols = before_cols - cleaned_df.shape[1]
                    cleaning_log.append(f"✅ Removed {removed_cols} mostly empty columns")
                except Exception as e:
                    errors_log.append(f"❌ Empty column removal failed: {str(e)}")

            # --- Trim whitespace ---
            if trim_whitespace:
                try:
                    text_cols = cleaned_df.select_dtypes(include='object').columns
                    for col in text_cols:
                        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    cleaning_log.append(f"✅ Trimmed whitespace from {len(text_cols)} text columns")
                except Exception as e:
                    errors_log.append(f"❌ Whitespace trimming failed: {str(e)}")

            # --- Fix casing ---
            if fix_casing:
                try:
                    text_cols = cleaned_df.select_dtypes(include='object').columns
                    for col in text_cols:
                        if casing_option == "lowercase":
                            cleaned_df[col] = cleaned_df[col].str.lower()
                        elif casing_option == "UPPERCASE":
                            cleaned_df[col] = cleaned_df[col].str.upper()
                        elif casing_option == "Title Case":
                            cleaned_df[col] = cleaned_df[col].str.title()
                    cleaning_log.append(f"✅ Applied {casing_option} to {len(text_cols)} text columns")
                except Exception as e:
                    errors_log.append(f"❌ Casing fix failed: {str(e)}")

            # --- Handle missing values ---
            if handle_missing:
                try:
                    before_missing = cleaned_df.isnull().sum().sum()
                    numeric_cols = cleaned_df.select_dtypes(include=np.number).columns
                    text_cols = cleaned_df.select_dtypes(include='object').columns

                    if missing_option == "Drop rows with missing values":
                        cleaned_df = cleaned_df.dropna()
                    elif missing_option == "Fill numeric with mean":
                        cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(cleaned_df[numeric_cols].mean())
                    elif missing_option == "Fill numeric with median":
                        cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(cleaned_df[numeric_cols].median())
                    elif missing_option == "Fill numeric with 0":
                        cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(0)
                    elif missing_option == "Fill text with 'Unknown'":
                        cleaned_df[text_cols] = cleaned_df[text_cols].fillna('Unknown')

                    after_missing = cleaned_df.isnull().sum().sum()
                    cleaning_log.append(f"✅ Handled missing values — {before_missing - after_missing:,} values resolved")
                except Exception as e:
                    errors_log.append(f"❌ Missing value handling failed: {str(e)}")

            # --- Format dates ---
            if format_dates:
                try:
                    date_cols = []
                    for col in cleaned_df.columns:
                        if 'date' in col.lower() or 'time' in col.lower():
                            date_cols.append(col)

                    fmt_map = {
                        "YYYY-MM-DD": "%Y-%m-%d",
                        "DD/MM/YYYY": "%d/%m/%Y",
                        "MM/DD/YYYY": "%m/%d/%Y"
                    }

                    for col in date_cols:
                        # Parse to datetime first, then sort, then format
                        parsed = pd.to_datetime(cleaned_df[col], errors='coerce', dayfirst=(date_format == "DD/MM/YYYY"))
                        cleaned_df[col] = parsed
                        cleaned_df = cleaned_df.sort_values(by=col).reset_index(drop=True)
                        cleaned_df[col] = cleaned_df[col].dt.strftime(fmt_map[date_format])

                    cleaning_log.append(f"✅ Formatted and sorted {len(date_cols)} date columns chronologically to {date_format}")
                except Exception as e:
                    errors_log.append(f"❌ Date formatting failed: {str(e)}")

            # --- Fix numeric columns ---
            if fix_numerics:
                try:
                    fixed = 0
                    for col in cleaned_df.select_dtypes(include='object').columns:
                        converted = pd.to_numeric(cleaned_df[col], errors='coerce')
                        if converted.notna().sum() > len(cleaned_df) * 0.8:
                            cleaned_df[col] = converted
                            fixed += 1
                    cleaning_log.append(f"✅ Converted {fixed} text columns to numeric")
                except Exception as e:
                    errors_log.append(f"❌ Numeric conversion failed: {str(e)}")

            # --- Remove outliers ---
            if remove_outliers:
                try:
                    before = len(cleaned_df)
                    numeric_cols = cleaned_df.select_dtypes(include=np.number).columns
                    for col in numeric_cols:
                        mean = cleaned_df[col].mean()
                        std = cleaned_df[col].std()
                        cleaned_df = cleaned_df[
                            (cleaned_df[col] >= mean - 3 * std) &
                            (cleaned_df[col] <= mean + 3 * std)
                        ]
                    removed = before - len(cleaned_df)
                    cleaning_log.append(f"✅ Removed {removed:,} outlier rows (3σ rule)")
                except Exception as e:
                    errors_log.append(f"❌ Outlier removal failed: {str(e)}")

            # ============================================
            # RESULTS
            # ============================================
            st.divider()
            st.subheader("📋 Cleaning Report")

            for log in cleaning_log:
                st.write(log)

            if errors_log:
                st.warning("⚠️ Some steps had issues:")
                for err in errors_log:
                    st.write(err)

            # Before vs After
            st.divider()
            st.subheader("📊 Before vs After")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Rows Before", f"{df.shape[0]:,}")
            col2.metric("Rows After", f"{cleaned_df.shape[0]:,}", f"{cleaned_df.shape[0] - df.shape[0]:,}")
            col3.metric("Columns Before", df.shape[1])
            col4.metric("Columns After", cleaned_df.shape[1], f"{cleaned_df.shape[1] - df.shape[1]}")

            with st.expander("👀 Preview Cleaned Data"):
                st.dataframe(cleaned_df.head(20))

            # Download
            st.divider()
            cleaned_csv = cleaned_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Cleaned CSV",
                data=cleaned_csv,
                file_name="cleaned_data.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Could not read file: {str(e)}")
        st.info("Make sure your file is a valid CSV or Excel file and try again.")
