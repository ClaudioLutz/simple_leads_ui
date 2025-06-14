import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

st.set_page_config(layout="wide")

# --- Authentication (copied & adapted from app.py) ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("Configuration file (config.yaml) not found.")
    st.stop()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Check authentication status from session state
if st.session_state.get("authentication_status"):
    username = st.session_state['username']
    user_role = config['credentials']['usernames'][username].get('role', 'default_role')

    st.sidebar.title(f"Welcome *{st.session_state['name']}*")
    authenticator.logout(button_name='Logout', location='sidebar')

    st.title("My Assigned Leads")

    if 'moved_leads_df' not in st.session_state or st.session_state.moved_leads_df.empty:
        st.info("No leads have been assigned yet.")
    else:
        all_moved_leads = st.session_state.moved_leads_df

        if user_role == 'Manager':
            st.header("Manager View: All Assigned Leads")
            display_df = all_moved_leads
        else: # Representative View
            st.header("Leads Assigned To You")
            display_df = all_moved_leads[all_moved_leads['assigned_to'] == username]
        
        if display_df.empty:
            st.info("You do not have any assigned leads.")
        else:
            # Reorder columns for better display
            cols_to_show = ['name', 'number', 'email', 'ort', 'selection_date']
            # If manager, show who it's assigned to
            if user_role == 'Manager':
                # Get full names for display
                all_users = config['credentials']['usernames']
                display_df['assigned_to_name'] = display_df['assigned_to'].apply(
                    lambda x: all_users.get(x, {}).get('name', x)
                )
                cols_to_show.append('assigned_to_name')

            # Ensure all desired columns exist before trying to display them
            existing_cols = [col for col in cols_to_show if col in display_df.columns]
            st.dataframe(display_df[existing_cols], use_container_width=True, hide_index=True)

        if user_role == 'Manager' and st.button("Clear All Assigned Leads"):
            st.session_state.moved_leads_df = pd.DataFrame(columns=all_moved_leads.columns)
            st.success("All assigned leads have been cleared.")
            st.rerun()

elif st.session_state.get("authentication_status") is False:
    st.error('Username/password is incorrect. Please login on the main page.')
elif st.session_state.get("authentication_status") is None:
    st.warning('Please login on the main page to access this page.')
