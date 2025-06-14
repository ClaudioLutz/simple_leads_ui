# FILE: app.py
import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import date

# --- Page Config ---
st.set_page_config(layout="wide")

# --- Authentication ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- Data Loading ---
def get_leads():
    # In a real app, this would connect to a database
    data = {
        'name': ['Test Firma AG', 'Muster GmbH', 'Alpha Services', 'Beta Solutions', 'Gamma Innovations', 'Delta Consulting', 'Epsilon Enterprises', 'Zeta Corporation'],
        'number': ['12345', '67890', '11111', '22222', '33333', '44444', '55555', '66666'],
        'email': ['info@testfirma.ch', 'kontakt@muster.de', 'contact@alpha.com', 'info@beta.co', 'sales@gamma.net', 'support@delta.org', 'hello@epsilon.biz', 'admin@zeta.io'],
        'strasse': ['Teststrasse 1', 'Musterweg 2', 'Alpha Allee 3', 'Beta Boulevard 4', 'Gamma Gasse 5', 'Delta Damm 6', 'Epsilon Esplanade 7', 'Zeta Zeile 8'],
        'plz': ['8000', '10115', '20095', '50667', '60313', '80331', '10178', '40213'],
        'ort': ['Zürich', 'Berlin', 'Hamburg', 'Köln', 'Frankfurt', 'München', 'Berlin', 'Düsseldorf'],
        'url': ['www.testfirma.ch', 'www.muster.de', 'www.alpha.com', 'www.beta.co', 'www.gamma.net', 'www.delta.org', 'www.epsilon.biz', 'www.zeta.io'],
        'branche': ['IT', 'Marketing', 'Finanzen', 'Consulting', 'Technologie', 'Dienstleistung', 'E-Commerce', 'Industrie'],
        'size_kategorie': ['KMU', 'Grossunternehmen', 'KMU', 'KMU', 'Grossunternehmen', 'Mittelstand', 'Startup', 'Grossunternehmen'],
        'umsatz_kategorie': ['1-5 Mio', '10-50 Mio', '5-10 Mio', '1-5 Mio', '50-100 Mio', '10-50 Mio', '0-1 Mio', '100+ Mio'],
        'bonität': ['A', 'B', 'A', 'C', 'B', 'A', 'A', 'B']
    }
    df = pd.DataFrame(data)
    df['lead_id'] = [f"lead_{i+1}" for i in range(len(df))] # Add unique lead_id
    return df

# --- Main App Logic ---
name, authentication_status, username = authenticator.login()

if st.session_state["authentication_status"]:
    st.sidebar.title(f"Welcome *{st.session_state['name']}*")
    authenticator.logout(button_name='Logout', location='sidebar')

    # Initialize session state variables if they don't exist
    if 'leads' not in st.session_state:
        st.session_state.leads = get_leads()
    if 'checked_lead_ids' not in st.session_state:
        st.session_state.checked_lead_ids = set()
    if 'moved_leads_df' not in st.session_state:
        # Initialize with correct columns including 'selection_date'
        columns = st.session_state.leads.columns.tolist() + ['selection_date']
        st.session_state.moved_leads_df = pd.DataFrame(columns=columns)

    st.title("Lead Generation")

    # --- Filtering ---
    st.sidebar.header("Filter Leads")
    df_to_display = st.session_state.leads.copy()
    df_columns = df_to_display.columns.tolist()
    df_columns.remove('lead_id') # Don't filter by lead_id

    for column in df_columns:
        if df_to_display[column].nunique() > 1 and df_to_display[column].dtype == 'object':
            options = st.sidebar.multiselect(f"Filter by {column}", options=df_to_display[column].unique())
            if options:
                df_to_display = df_to_display[df_to_display[column].isin(options)]

    # Exclude leads that have already been moved
    moved_ids = st.session_state.moved_leads_df['lead_id'].unique()
    df_to_display = df_to_display[~df_to_display['lead_id'].isin(moved_ids)]

    # --- Move Selected Leads Button ---
    if st.button("Move Selected Leads to 'Selected Leads'"):
        if st.session_state.checked_lead_ids:
            leads_to_move = st.session_state.leads[st.session_state.leads['lead_id'].isin(st.session_state.checked_lead_ids)].copy()
            leads_to_move['selection_date'] = date.today()

            st.session_state.moved_leads_df = pd.concat([st.session_state.moved_leads_df, leads_to_move], ignore_index=True)
            st.session_state.checked_lead_ids.clear() # Clear selections after moving
            st.success(f"{len(leads_to_move)} leads moved successfully!")
            st.rerun()
        else:
            st.warning("No leads selected to move.")

    # --- Display Leads Table using st.data_editor ---
    # THIS IS THE REPLACEMENT FOR THE OLD st.columns-BASED TABLE
    if not df_to_display.empty:
        # Add a 'Select' column to the dataframe for the checkboxes
        df_to_display.insert(0, "Select", False)

        # Display the data editor
        edited_df = st.data_editor(
            df_to_display,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(required=True),
                "lead_id": None # Hide the lead_id column from the user
            },
            disabled=df_columns, # Make other columns non-editable
            use_container_width=True
        )

        # Update the session state with the selected lead IDs
        selected_rows = edited_df[edited_df.Select]
        st.session_state.checked_lead_ids = set(selected_rows['lead_id'])

    else:
        st.write("No leads to display based on current filters or data.")


elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
