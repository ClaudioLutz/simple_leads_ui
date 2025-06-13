import streamlit as st
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from datetime import date # Added for selection_date

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

    with st.expander(f"Notes for {lead_name}", expanded=True):
        st.write(f"Lead ID: {current_lead_id}") # Display lead ID for context
        # The notes variable here is just to hold the widget, value is retrieved via its key from session_state
        st.text_area("Notes", value=existing_notes, height=200, key=text_area_key)
        # Test: Assert that the value passed to text_area is what we expect (on open/re-open)
        # This assertion is tricky due to Streamlit's execution. We rely on text_area_key being populated.
        #if text_area_key in st.session_state:
        #     assert st.session_state[text_area_key] == existing_notes, \
        #        f"Text area content '{st.session_state[text_area_key]}' did not match loaded notes '{existing_notes}'"


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
                st.rerun() # Rerun to close expander and refresh state

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

        # Add a way to close the expander using the expander's default close button
        # This is handled by st.expander internally, but explicit close can be done by setting selected_lead_id to None


# Fixed the login call - removed the conflicting 'Login' parameter
name, authentication_status, username = authenticator.login(location='main')

# Initialize session state for lead notes if it doesn't exist
if 'lead_notes' not in st.session_state:
    st.session_state.lead_notes = {}

if st.session_state.get("authentication_status"):
    authenticator.logout(button_name='Logout', location='sidebar')
    st.write(f'Welcome *{st.session_state["name"]}*')
    st.title('Lead Generator')

    df = get_leads()

    # Initialize session state
    if 'df_to_show' not in st.session_state:
        st.session_state.df_to_show = df
    
    # Initialize moved_leads_df
    if 'moved_leads_df' not in st.session_state:
        temp_leads_df = get_leads() # Call get_leads to get structure
        lead_columns = temp_leads_df.columns.tolist() + ['selection_date']
        st.session_state.moved_leads_df = pd.DataFrame(columns=lead_columns)

    # Initialize checked_lead_ids for checkbox selection
    if 'checked_lead_ids' not in st.session_state:
        st.session_state.checked_lead_ids = set()

    # Lead selection dropdown for notes
    options = [(row['name'], row['lead_id']) for _, row in st.session_state.df_to_show.iterrows()]
    selected_name = st.selectbox("Select lead for notes", [opt[0] for opt in options], key="lead_select")
    if st.button("Open Notes", key="open_notes_btn"):
        for name, lid in options:
            if name == selected_name:
                st.session_state.selected_lead_id = lid
                break
        st.rerun()

    # Note: Streamlit's st.dataframe does not support selection_mode or key parameters.
    # To implement row selection, consider using st_aggrid or other third-party components.
    # For now, we remove the selection handling code to avoid errors.

    # if 'df_to_show_selection' in st.session_state:
    #     selection = st.session_state.df_to_show_selection.get('selection', {})
    #     selected_rows = selection.get('rows', [])
    #     if selected_rows:
    #         selected_row_index = selected_rows[0]
    #         if 'lead_id' in st.session_state.df_to_show.columns:
    #             newly_selected_lead_id = st.session_state.df_to_show.iloc[selected_row_index]['lead_id']
    #             st.session_state.selected_lead_id = newly_selected_lead_id
    #             # Test: Lead Selection
    #             assert st.session_state.selected_lead_id is not None, "selected_lead_id was not set after row selection."
    #             print(f"[Row Selected] Lead ID: {st.session_state.selected_lead_id}")
    #             # Do not call rerun here, selection itself triggers it via on_select='rerun'
    #         else:
    #             print("Error: 'lead_id' column not found in DataFrame.")

    # Display the modal if a lead is selected
    if 'selected_lead_id' in st.session_state and st.session_state.selected_lead_id is not None:
        display_notes_modal()

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

        # Checkbox-based selection system
        if not st.session_state.df_to_show.empty:
            df_to_display = st.session_state.df_to_show
            df_columns = df_to_display.columns.tolist()
            
            # Header row with "Select All" checkbox
            # Column widths: Checkbox column, then others
            header_column_widths = [0.2] + [1.5] * len(df_columns) 
            header_cols = st.columns(header_column_widths)

            # "Select All" checkbox logic
            all_visible_lead_ids = set(df_to_display['lead_id'].tolist())
            
            def on_select_all_change():
                # This function is now correctly defined and will be used by the select_all_checkbox_instance
                if st.session_state.select_all_checkbox_instance: # If checked
                    st.session_state.checked_lead_ids.update(all_visible_lead_ids)
                else: # If unchecked
                    st.session_state.checked_lead_ids.difference_update(all_visible_lead_ids)

            # Re-evaluating "are_all_selected" for the checkbox state
            # This must be based on current `checked_lead_ids` and `all_visible_lead_ids`
            is_select_all_checked_value = all_visible_lead_ids.issubset(st.session_state.checked_lead_ids) if all_visible_lead_ids else False
            
            # The "Select All" checkbox in the header
            header_cols[0].checkbox(" ", value=is_select_all_checked_value, key="select_all_checkbox_instance", on_change=on_select_all_change, help="Select/Deselect all visible leads")


            for i, col_name in enumerate(df_columns):
                header_cols[i+1].markdown(f"**{col_name}**")

            # Display individual lead rows with checkboxes
            for index, row_data in df_to_display.iterrows():
                lead_id = row_data['lead_id']
                is_checked = lead_id in st.session_state.checked_lead_ids
                
                row_cols = st.columns(header_column_widths) # Same widths as header

                def on_checkbox_change(current_lead_id):
                    if st.session_state[f"cb_{current_lead_id}"]: # If checked
                        st.session_state.checked_lead_ids.add(current_lead_id)
                    else: # If unchecked
                        st.session_state.checked_lead_ids.discard(current_lead_id)
                
                # Individual checkbox for the lead
                row_cols[0].checkbox(" ", value=is_checked, key=f"cb_{lead_id}", on_change=on_checkbox_change, args=(lead_id,))

                for i, col_name in enumerate(df_columns):
                    row_cols[i+1].write(str(row_data[col_name]))
            
            st.markdown("---") # Separator

            # "Move Checked Leads" button
            if st.button("Move Checked Leads to Selected List"):
                if not st.session_state.checked_lead_ids:
                    st.warning("No leads selected to move.")
                else:
                    leads_to_move_df = df_to_display[df_to_display['lead_id'].isin(st.session_state.checked_lead_ids)].copy()
                    if not leads_to_move_df.empty:
                        leads_to_move_df['selection_date'] = date.today().strftime("%Y-%m-%d")

                        for col in leads_to_move_df.columns:
                            if col not in st.session_state.moved_leads_df.columns:
                                st.session_state.moved_leads_df[col] = pd.NA
                        
                        st.session_state.moved_leads_df = pd.concat([st.session_state.moved_leads_df, leads_to_move_df], ignore_index=True)
                        
                        if 'lead_id' in st.session_state.moved_leads_df.columns:
                            st.session_state.moved_leads_df.drop_duplicates(subset=['lead_id'], keep='last', inplace=True)
                        
                        st.success(f"{len(leads_to_move_df)} checked leads moved to selected list.")
                        st.session_state.checked_lead_ids.clear() # Clear selection after moving
                        # The "Select All" checkbox will update its visual state on rerun
                        # because is_select_all_checked_value will be False after clearing checked_lead_ids.
                        st.rerun()
                    else:
                        st.warning("Selected leads not found in the current view. This shouldn't happen.")
        
        else: # If df_to_show is empty
            st.write("No leads to display based on current filters or data.")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
