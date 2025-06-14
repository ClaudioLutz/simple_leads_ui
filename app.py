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
name, authentication_status, username = authenticator.login() # User note: Ignore Pylance error "Argument missing for parameter 'form_name'"

if st.session_state["authentication_status"]:
    st.sidebar.title(f"Welcome *{st.session_state['name']}*")
    authenticator.logout(button_name='Logout', location='sidebar')

    # Initialize session state variables if they don't exist
    if 'leads' not in st.session_state:
        st.session_state.leads = get_leads()
    if 'checked_lead_ids' not in st.session_state:
        st.session_state.checked_lead_ids = set()
    if 'moved_leads_df' not in st.session_state:
        # Initialize with correct columns including 'selection_date' and 'assigned_to'
        columns = st.session_state.leads.columns.tolist() + ['selection_date', 'assigned_to']
        st.session_state.moved_leads_df = pd.DataFrame(columns=columns)

    st.title("Lead Generation")

    # --- Filtering ---
    st.sidebar.header("Filter Leads")
    df_to_display = st.session_state.leads.copy()
    
    # df_columns is defined here for st.data_editor's 'disabled' parameter later.
    # It contains all data column names from the original dataframe except 'lead_id'.
    df_columns = df_to_display.columns.tolist()
    df_columns.remove('lead_id') 

    # New two-step filtering logic
    all_lead_columns = st.session_state.leads.columns.tolist()
    filterable_categories = ["None"] # Start with "None" option to disable category filter

    for col_name in all_lead_columns:
        if col_name == 'lead_id': # Skip lead_id for filtering categories
            continue
        # A column is filterable if it's of object type and has more than one unique value in the original dataset
        if st.session_state.leads[col_name].nunique() > 1 and st.session_state.leads[col_name].dtype == 'object':
            filterable_categories.append(col_name)

    selected_category = st.sidebar.selectbox(
        "Filter by Category:",
        options=filterable_categories,
        index=0 # Default to "None"
    )

    if selected_category != "None":
        # Get unique values from the original dataset for the selected category
        # Convert to list and sort for consistent display in multiselect
        unique_values_for_category = sorted(list(st.session_state.leads[selected_category].unique()))
        
        selected_values = st.sidebar.multiselect(
            f"Select {selected_category} value(s):",
            options=unique_values_for_category
        )
        if selected_values: # If the user selected some values for the chosen category
            df_to_display = df_to_display[df_to_display[selected_category].isin(selected_values)]
    # End of new filtering logic

    # Exclude leads that have already been moved
    moved_ids = st.session_state.moved_leads_df['lead_id'].unique()
    df_to_display = df_to_display[~df_to_display['lead_id'].isin(moved_ids)]

    # --- Assignment Logic for Manager ---
    user_role = config['credentials']['usernames'][username].get('role', 'default_role')

    if user_role == 'Manager':
        st.sidebar.markdown("---")
        st.sidebar.header("Lead Assignment")

        representatives = {
            user: details['name']
            for user, details in config['credentials']['usernames'].items()
            if details.get('role') == 'Representative'
        }

        if not representatives:
            st.sidebar.warning("No representatives found in config.yaml.")
        else:
            selected_rep_name = st.sidebar.selectbox(
                "Assign selected leads to:",
                options=list(representatives.values())
            )
            
            selected_rep_username = [user for user, name in representatives.items() if name == selected_rep_name][0]

            if st.button(f"Assign to {selected_rep_name}"):
                if st.session_state.checked_lead_ids:
                    leads_to_move = st.session_state.leads[st.session_state.leads['lead_id'].isin(st.session_state.checked_lead_ids)].copy()
                    leads_to_move['selection_date'] = date.today().isoformat()
                    leads_to_move['assigned_to'] = selected_rep_username # Add the username of the rep

                    st.session_state.moved_leads_df = pd.concat([st.session_state.moved_leads_df, leads_to_move], ignore_index=True)
                    st.session_state.checked_lead_ids.clear()
                    
                    st.success(f"{len(leads_to_move)} leads assigned to {selected_rep_name} successfully!")
                    st.rerun()
                else:
                    st.warning("No leads selected to assign.")

    # --- Display Leads Table using st.data_editor ---
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
            disabled=df_columns, # Make data columns (all except 'Select' and 'lead_id') non-editable
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
