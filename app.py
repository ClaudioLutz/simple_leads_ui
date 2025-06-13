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
    return pd.DataFrame(data)

authenticator.login(location='main')

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

        st.dataframe(st.session_state.df_to_show, use_container_width=True)
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
