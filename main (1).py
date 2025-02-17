import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="KYC Process Dashboard", layout="wide")

# Función para cargar datos con cache
@st.cache_data
def load_data():
    df = pd.read_csv('data.csv')
    df.columns = df.columns.str.strip().str.lower()  # Normalizar nombres de columnas
    
    # Convertir fecha si existe la columna
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce').dt.tz_localize(None)
    else:
        st.error("⚠️ The dataset is missing the 'created_at' column for filtering by date.")
    
    return df

# Cargar datos
data = load_data()

# Verificación de columnas esenciales
required_columns = {'case_id', 'cases_status', 'check_type', 'check_status', 'entity_type', 'country', 'risk_level', 'created_at'}
missing_columns = required_columns - set(data.columns)
if missing_columns:
    st.error(f"⚠️ Missing columns in dataset: {', '.join(missing_columns)}")

# 📌 **Sidebar - Filtros**
st.sidebar.header("🔍 Filters")

# Filtro de rango de fechas predefinido
date_filter = st.sidebar.selectbox("📅 Select Date Range", 
                                   ["Historical Data", "Last Day", "Last Week", "Last 15 Days", "Last Month"])

# Obtener la fecha actual
today = datetime.today()

# Filtrar datos según la opción seleccionada
filtered_data = data.copy()
if date_filter == "Last Day":
    filtered_data = filtered_data[filtered_data["created_at"] >= today - timedelta(days=1)]
elif date_filter == "Last Week":
    filtered_data = filtered_data[filtered_data["created_at"] >= today - timedelta(weeks=1)]
elif date_filter == "Last 15 Days":
    filtered_data = filtered_data[filtered_data["created_at"] >= today - timedelta(days=15)]
elif date_filter == "Last Month":
    filtered_data = filtered_data[filtered_data["created_at"] >= today - timedelta(days=30)]

# Dropdowns para filtros adicionales
case_status_filter = st.sidebar.selectbox("📂 Case Status", ["All"] + list(filtered_data["cases_status"].dropna().unique()))
check_type_filter = st.sidebar.selectbox("✅ Check Type", ["All"] + list(filtered_data["check_type"].dropna().unique()))
risk_level_filter = st.sidebar.selectbox("⚠️ Risk Level", ["All"] + list(filtered_data["risk_level"].dropna().unique()))
country_filter = st.sidebar.selectbox("🌍 Country", ["All"] + list(filtered_data["country"].dropna().unique()))

# Aplicar filtros solo si no es "All"
if case_status_filter != "All":
    filtered_data = filtered_data[filtered_data["cases_status"] == case_status_filter]
if check_type_filter != "All":
    filtered_data = filtered_data[filtered_data["check_type"] == check_type_filter]
if risk_level_filter != "All":
    filtered_data = filtered_data[filtered_data["risk_level"] == risk_level_filter]
if country_filter != "All":
    filtered_data = filtered_data[filtered_data["country"] == country_filter]

# 📊 **KPIs**
total_kyc_cases = filtered_data['case_id'].nunique()
completed_kyc_cases = filtered_data[filtered_data['cases_status'] == 'open']['case_id'].nunique()
aml_alerts = filtered_data[(filtered_data['check_type'] == 'aml') & (filtered_data['check_status'] == 'need_review') & 
                           (filtered_data['cases_status'].isin(['open', 'approved']))]['check_id'].nunique()
idv_alerts = filtered_data[(filtered_data['check_type'] == 'id_verification') & (filtered_data['check_status'] == 'need_review') & 
                           (filtered_data['cases_status'] == 'open')]['check_id'].nunique()

individual_types = {"POA Lookback (1.14.2025)", "Individual", "True Match - PEP", "Employee", "VIP_Customer"}
document_alerts = filtered_data[(filtered_data['check_type'].isin(['id_document', 'document'])) & 
                                (filtered_data['check_status'] == 'need_review') & 
                                (filtered_data['cases_status'] == 'open') & 
                                (filtered_data['entity_type'].apply(lambda x: any(ind in x for ind in individual_types)))]['check_id'].nunique()
document_alerts_companies = filtered_data[(filtered_data['check_type'] == 'document') & 
                                          (filtered_data['check_status'] == 'need_review') & 
                                          (filtered_data['cases_status'] == 'open') & 
                                          (filtered_data['entity_type'] == 'business')]['check_id'].nunique()

# 📊 **Dashboard Principal**
st.title("📊 KYC Process Dashboard")
st.markdown(f"### 📌 Overview of KYC Cases and Alerts ({date_filter})")

col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

col1.metric("🆔 Users Starting KYC", total_kyc_cases)
col2.metric("📄 Completed KYC (In Review)", completed_kyc_cases)
col3.metric("🚨 AML Alerts", aml_alerts)
col4.metric("🛂 IDV Alerts", idv_alerts)
col5.metric("📑 Document Alerts (Individuals)", document_alerts)
col6.metric("🏢 Document Alerts (Companies)", document_alerts_companies)

# 📋 **Datos Filtrados**
st.markdown("### 📋 Filtered Data")
st.dataframe(filtered_data)

# 📥 **Descargar datos filtrados**
st.download_button("📥 Download Filtered Data", filtered_data.to_csv(index=False).encode('utf-8'), "filtered_data.csv", "text/csv")
