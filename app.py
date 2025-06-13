import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

st.set_page_config(layout="wide")

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Dummy data for now, will be replaced with SQL Server data
def get_leads():
    data = {
        'name': ['Test Firma AG', 'Muster GmbH'],
        'number': ['12345', '67890'],
        'email': ['info@testfirma.ch', 'kontakt@muster.de'],
        'strasse': ['Teststrasse 1', 'Musterweg 2'],
        'plz': ['8000', '10115'],
        'ort': ['Zürich', 'Berlin'],
        'url': ['www.testfirma.ch', 'www.muster.de'],
        'branche': ['IT', 'Marketing'],
        'size_kategorie': ['KMU', 'Grossunternehmen'],
        'umsatz_kategorie': ['1-5 Mio', '10-50 Mio'],
        'bonität': ['A', 'B']
    }
    df = pd.DataFrame(data)
    df['lead_id'] = range(1, len(df) + 1)
    return df

def display_notes_modal():
    if 'selected_lead_id' not in st.session_state or st.session_state.selected_lead_id is None:
        return

    selected_lead = st.session_state.df_to_show[st.session_state.df_to_show['lead_id'] == st.session_state.selected_lead_id]

    if selected_lead.empty:
        st.error("Selected lead not found.")
        st.session_state.selected_lead_id = None # Reset to avoid error loop
        return

    lead_name = selected_lead.iloc[0]['name']
    current_lead_id = st.session_state.selected_lead_id
    print(f"[Modal Open] Current Lead ID: {current_lead_id}") # Test: Modal opening

    df_display = st.session_state.df_to_show # Use the filtered/searched df

    # Ensure lead_id column is of the same type as current_lead_id for comparison
    # This might not be strictly necessary if types are already consistent but good for robustness
    df_display['lead_id'] = df_display['lead_id'].astype(type(current_lead_id))

    all_lead_ids = df_display['lead_id'].tolist()

    current_idx = -1
    if current_lead_id in all_lead_ids:
        current_idx = all_lead_ids.index(current_lead_id)
    else:
        # This case should ideally not be reached if selected_lead_id is always valid
        st.error("Current lead ID not found in the list. Closing modal.")
        st.session_state.selected_lead_id = None
        st.rerun()
        return

    # Retrieve existing notes or default to empty string
    existing_notes = st.session_state.lead_notes.get(current_lead_id, "")
    print(f"[Modal Open] Existing notes for {current_lead_id}: '{existing_notes}'") # Test: Note loading

    modal_key = f"notes_modal_{current_lead_id}" # Unique key for the modal
    text_area_key = f"notes_text_area_{current_lead_id}" # Unique key for the text_area

    with st.modal(title=f"Notes for {lead_name}", key=modal_key):
        st.write(f"Lead ID: {current_lead_id}") # Display lead ID for context
        # The notes variable here is just to hold the widget, value is retrieved via its key from session_state
        st.text_area("Notes", value=existing_notes, height=200, key=text_area_key)
        # Test: Assert that the value passed to text_area is what we expect (on open/re-open)
        # This assertion is tricky due to Streamlit's execution. We rely on text_area_key being populated.
        if text_area_key in st.session_state:
             assert st.session_state[text_area_key] == existing_notes, \
                f"Text area content '{st.session_state[text_area_key]}' did not match loaded notes '{existing_notes}'"


        col1, col2, col3, col4 = st.columns([1,1,1,3]) # Adjust column ratios as needed

        with col1:
            if st.button("Save"):
                updated_notes = st.session_state[text_area_key]
                st.session_state.lead_notes[current_lead_id] = updated_notes
                # Test: Note Saving
                assert st.session_state.lead_notes.get(current_lead_id) == updated_notes, \
                    "Saved notes do not match notes in session state."
                print(f"[Save Clicked] Lead {current_lead_id}. Saved Notes: '{updated_notes}'")
                st.session_state.selected_lead_id = None
                st.rerun() # Rerun to close modal and refresh state

        with col2:
            # Disable button if at the first lead, otherwise handle click
            prev_button_disabled = current_idx <= 0
            if st.button("Previous", disabled=prev_button_disabled):
                if not prev_button_disabled:
                    expected_prev_lead_id = all_lead_ids[current_idx - 1]
                    old_lead_id = current_lead_id
                    st.session_state.selected_lead_id = expected_prev_lead_id
                    print(f"[Previous Clicked] Old Lead ID: {old_lead_id}, New Lead ID: {st.session_state.selected_lead_id}")
                    # Test: Previous Lead Functionality
                    assert st.session_state.selected_lead_id == expected_prev_lead_id, \
                        "Previous lead ID not set correctly."
                    st.rerun()

        with col3:
            # Disable button if at the last lead, otherwise handle click
            next_button_disabled = current_idx >= len(all_lead_ids) - 1
            if st.button("Next", disabled=next_button_disabled):
                if not next_button_disabled:
                    expected_next_lead_id = all_lead_ids[current_idx + 1]
                    old_lead_id = current_lead_id
                    st.session_state.selected_lead_id = expected_next_lead_id
                    print(f"[Next Clicked] Old Lead ID: {old_lead_id}, New Lead ID: {st.session_state.selected_lead_id}")
                    # Test: Next Lead Functionality
                    assert st.session_state.selected_lead_id == expected_next_lead_id, \
                        "Next lead ID not set correctly."
                    st.rerun()

        # Add a way to close the modal using the modal's default close button
        # This is handled by st.modal internally, but explicit close can be done by setting selected_lead_id to None


authenticator.login(location='main')

# Initialize session state for lead notes if it doesn't exist
if 'lead_notes' not in st.session_state:
    st.session_state.lead_notes = {}

if st.session_state.get("authentication_status"):
    authenticator.logout('Logout', 'sidebar')
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Lead Generator')

    df = get_leads()

    # Initialize session state
    if 'df_to_show' not in st.session_state:
        st.session_state.df_to_show = df

    # Search functionality within an expander
    with st.expander("Suchen und Filtern", expanded=True):
        col1, col2, col3, col4 = st.columns([3, 2, 1, 2])

        with col1:
            search_term = st.text_input('Suchen', label_visibility="collapsed", placeholder="Test Firma AG")
        with col2:
            # Set 'name' as default search category
            default_category_index = list(df.columns).index('name') if 'name' in df.columns else 0
            search_category = st.selectbox('Suchen in', df.columns, label_visibility="collapsed", index=default_category_index)
        with col3:
            if st.button('Suchen'):
                if search_term:
                    st.session_state.df_to_show = df[df[search_category].astype(str).str.contains(search_term, case=False)]
                else:
                    st.session_state.df_to_show = df
        with col4:
            if st.button('Filter entfernen'):
                st.session_state.df_to_show = df

        st.dataframe(
            st.session_state.df_to_show,
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun",
            key='df_to_show_selection'
        )

        if st.session_state.df_to_show_selection:
            selected_rows = st.session_state.df_to_show_selection['rows']
            if selected_rows:
                selected_row_index = selected_rows[0]
                if 'lead_id' in st.session_state.df_to_show.columns:
                    newly_selected_lead_id = st.session_state.df_to_show.iloc[selected_row_index]['lead_id']
                    st.session_state.selected_lead_id = newly_selected_lead_id
                    # Test: Lead Selection
                    assert st.session_state.selected_lead_id is not None, "selected_lead_id was not set after row selection."
                    print(f"[Row Selected] Lead ID: {st.session_state.selected_lead_id}")
                    # Do not call rerun here, selection itself triggers it via on_select='rerun'
                else:
                    print("Error: 'lead_id' column not found in DataFrame.")

    # Display the modal if a lead is selected
    if 'selected_lead_id' in st.session_state and st.session_state.selected_lead_id is not None:
        display_notes_modal()

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
