import streamlit as st
import requests
import pandas as pd
import shortuuid
import plotly.express as px
from datetime import datetime
from streamlit_lottie import st_lottie
from config import CATEGORIES, TYPES, MODES

# --- CONFIGURATION ---
PAGE_TITLE = "Finance Master"
PAGE_ICON = "💎"

# ⚠️ PASTE YOUR POWER AUTOMATE URLs HERE ⚠️
ADD_URL = "https://default791a43d78f384d67a109ddbaad8a2a.58.environment.api.powerplatform.com/powerautomate/automations/direct/workflows/c2b157c3ca81418b881bbe898b3c4d04/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=SILIfrPdhSFVq86qXkdWsFGi7S36NcqsJdVs3CAQI-E" 
UPDATE_URL = "https://default791a43d78f384d67a109ddbaad8a2a.58.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/74e15b2d357845fea40c6fafc749c517/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=SLH1WDz8tH17QV9b7_ivqPgEZGljFD806bqdwqnA-fY"

st.set_page_config(
    page_title=PAGE_TITLE, 
    page_icon=PAGE_ICON, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE ---
if 'session_log' not in st.session_state:
    st.session_state.session_log = []

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    /* Professional Clean Look */
    #MainMenu {visibility: visible;}
    header {visibility: visible;}
    footer {visibility: hidden;}
    
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 8px;
        color: #212529;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    @media (prefers-color-scheme: dark) {
        div[data-testid="metric-container"] {
            background-color: #262730;
            border: 1px solid #41424b;
            color: white;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def load_lottie(url):
    """Safe loader that prevents crashes if internet is slow or link is broken"""
    try:
        r = requests.get(url, timeout=3) # 3 second timeout to prevent hanging
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

def send_to_pa(url, data):
    try:
        response = requests.post(url, json=data)
        # Accept 200 (OK) or 202 (Accepted)
        return response.status_code in [200, 202]
    except:
        return False

def generate_id(category, date_obj):
    prefix = category[:3].upper()
    date_str = date_obj.strftime("%Y%m%d")
    random_str = shortuuid.ShortUUID().random(length=4).upper()
    return f"{prefix}-{date_str}-{random_str}"

# --- ASSETS (Professional Animations) ---
# We load these safely. If they fail, 'None' is returned.
anim_success = load_lottie("https://assets9.lottiefiles.com/packages/lf20_ttv0jibb.json") 
anim_wallet = load_lottie("https://assets10.lottiefiles.com/packages/lf20_pthhMw.json") 
anim_loading = load_lottie("https://assets4.lottiefiles.com/packages/lf20_jbrw3hcz.json") 

# --- SIDEBAR ---
with st.sidebar:
    st.title("Finance Master")
    
    # Safe render: Only show if loaded
    if anim_wallet:
        st_lottie(anim_wallet, height=150, key="sidebar_anim")
    
    st.divider()
    st.header("📂 Data Sync")
    st.caption("Upload 'Expenses.xlsx' to view the dashboard.")
    uploaded_file = st.file_uploader("Upload File", type=["xlsx"], label_visibility="collapsed")

# --- MAIN APP ---
# TABS
tab_add, tab_recent, tab_dash = st.tabs(["➕ Add Entry", "📝 Recent & Edit", "📊 Dashboard"])

# ==========================
# TAB 1: ADD ENTRY
# ==========================
with tab_add:
    st.subheader("New Transaction")
    
    with st.form("entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        date_entry = c1.date_input("Date")
        category = c2.selectbox("Category", CATEGORIES)
        
        c3, c4 = st.columns(2)
        amount = c3.number_input("Amount (₹)", min_value=0.0, step=10.0)
        mode = c4.selectbox("Mode", MODES)
        
        c5, c6 = st.columns(2)
        trans_type = c5.selectbox("Type", TYPES)
        notes = c6.text_input("Notes")
        
        # Submit Button inside the form
        submitted = st.form_submit_button("Log Transaction", type="primary")

        if submitted:
            unique_id = generate_id(category, date_entry)
            payload = {
                "date": str(date_entry), "category": category,
                "type": trans_type, "amount": amount,
                "mode": mode, "notes": notes, "id": unique_id
            }
            
            # Show a loading spinner
            with st.spinner("Syncing to Cloud..."):
                if send_to_pa(ADD_URL, payload):
                    st.success("Transaction Logged!")
                    if anim_success: 
                        st_lottie(anim_success, height=100, key="success_anim", loop=False)
                    st.session_state.session_log.insert(0, payload)
                else:
                    st.error("Connection Failed. Check your Internet or Power Automate URL.")

# ==========================
# TAB 2: RECENT LOG & QUICK EDIT
# ==========================
with tab_recent:
    st.subheader("Session History & Corrections")
    
    if not st.session_state.session_log:
        st.info("No transactions added in this session yet.")
    else:
        # Display Table
        df_log = pd.DataFrame(st.session_state.session_log)
        display_cols = ['category', 'amount', 'notes', 'date', 'mode']
        st.dataframe(df_log[display_cols], use_container_width=True)
        
        st.divider()
        st.write("#### ✏️ Quick Fix")
        
        # Create a dropdown of recent items
        options = {f"{item['category']} - ₹{item['amount']} ({item['notes']})": item for item in st.session_state.session_log}
        selected_label = st.selectbox("Select Transaction to Fix:", list(options.keys()))
        
        if selected_label:
            data_to_edit = options[selected_label]
            
            with st.form("quick_edit_form"):
                st.caption(f"Editing ID: {data_to_edit['id']}")
                
                # Parse date string back to object
                d_obj = datetime.strptime(data_to_edit['date'], '%Y-%m-%d').date()
                
                ec1, ec2 = st.columns(2)
                new_date = ec1.date_input("Date", d_obj)
                new_cat = ec2.selectbox("Category", CATEGORIES, index=CATEGORIES.index(data_to_edit['category']))
                
                ec3, ec4 = st.columns(2)
                new_amt = ec3.number_input("Amount", value=float(data_to_edit['amount']))
                new_mode = ec4.selectbox("Mode", MODES, index=MODES.index(data_to_edit['mode']))
                
                # FIX: This line was causing the TypeError before. It is now explicitly corrected.
                ec5, ec6 = st.columns(2)
                new_type = ec5.selectbox("Type", TYPES, index=TYPES.index(data_to_edit['type']))
                new_note = ec6.text_input("Notes", value=data_to_edit['notes'])
                
                update_btn = st.form_submit_button("Update Record", type="primary")
                
                if update_btn:
                    update_payload = {
                        "id": data_to_edit['id'],
                        "date": str(new_date),
                        "category": new_cat,
                        "amount": new_amt,
                        "mode": new_mode,
                        "type": new_type,
                        "notes": new_note
                    }
                    
                    with st.spinner("Updating Excel Row..."):
                        if send_to_pa(UPDATE_URL, update_payload):
                            st.success("Correction Sent!")
                            data_to_edit.update(update_payload)
                            st.rerun() 
                        else:
                            st.error("Update failed.")

# ==========================
# TAB 3: DASHBOARD
# ==========================
with tab_dash:
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            
            # Basic KPI Calculation
            inc = df[df['Type']=='Income']['Amount'].sum()
            exp = df[df['Type']=='Expense']['Amount'].sum()
            balance = inc - exp
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Income", f"₹{inc:,.0f}")
            c2.metric("Expense", f"₹{exp:,.0f}")
            c3.metric("Balance", f"₹{balance:,.0f}")
            
            st.divider()
            
            # Charts
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                st.subheader("Category Breakdown")
                # Donut Chart
                fig = px.pie(df[df['Type']=='Expense'], values='Amount', names='Category', hole=0.5)
                st.plotly_chart(fig, use_container_width=True)
                
            with c_chart2:
                st.subheader("Payment Mode Preference")
                # Bar Chart
                fig2 = px.bar(df[df['Type']=='Expense'], x='Mode', y='Amount', color='Category')
                st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            
    else:
        st.info("👆 Please upload your Excel file in the sidebar to view analytics.")