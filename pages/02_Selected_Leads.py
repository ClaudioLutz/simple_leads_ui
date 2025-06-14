import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
# from datetime import date # Not strictly needed here unless manipulating dates

st.set_page_config(layout="wide")

# --- Authentication (copied & adapted from app.py) ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("Configuration file (config.yaml) not found. Please ensure it's in the root directory (c:/Codes/SIMPLE_LEAD_GENERATOR).")
    st.stop()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

if st.session_state.get("authentication_status"):
    st.sidebar.title(f"Welcome *{st.session_state['name']}*")
    authenticator.logout(button_name='Logout', location='sidebar')

    st.title("Moved Leads")

    if 'moved_leads_df' not in st.session_state or st.session_state.moved_leads_df.empty:
        st.info("No leads have been moved yet.")
    else:
        # Ensure 'selection_date' is displayed correctly
        display_df = st.session_state.moved_leads_df.copy()
        if 'selection_date' in display_df.columns:
             # Ensure it's a string for display; already stored as string
             display_df['selection_date'] = display_df['selection_date'].astype(str)

        st.dataframe(display_df, use_container_width=False) # Changed to False to allow horizontal scrolling

        if st.button("Clear All Moved Leads"):
            # Re-initialize moved_leads_df with correct columns
            if 'df_to_show' in st.session_state and not st.session_state.df_to_show.empty:
                # Base columns on the main leads DataFrame structure
                lead_columns_for_reset = st.session_state.df_to_show.columns.tolist() + ['selection_date']
            elif not st.session_state.moved_leads_df.empty:
                # Fallback: use columns from current moved_leads_df if df_to_show is not available
                lead_columns_for_reset = st.session_state.moved_leads_df.columns.tolist()
            else:
                # Absolute fallback: define a minimal structure.
                # This case should be rare if app.py initializes moved_leads_df correctly.
                # Consider calling a utility function that defines lead structure if this becomes an issue.
                lead_columns_for_reset = ['lead_id', 'name', 'selection_date'] # Example minimal

            st.session_state.moved_leads_df = pd.DataFrame(columns=lead_columns_for_reset)
            st.success("All moved leads have been cleared.")
            st.rerun()

elif st.session_state.get("authentication_status") is False:
    st.error('Username/password is incorrect. Please login on the main page (app.py).')
elif st.session_state.get("authentication_status") is None:
    st.warning('Please login on the main page (app.py) to access this page.')
