# Technical Documentation: Simple Lead Management UI

## 1. Introduction

This document provides a detailed technical overview of the Simple Lead Management UI application. The application's primary goal is to offer a straightforward web-based interface for sales teams to view, filter, manage, and assign leads. It features role-based access control for Managers and Sales Representatives.

## 2. Project Structure

The project is organized as follows:

*   **`app.py`**: The main Streamlit application script. It handles:
    *   User authentication.
    *   Display of the main lead dashboard.
    *   Lead filtering logic.
    *   Lead assignment functionality for Managers.
    *   Initial data loading (currently hardcoded).
*   **`config.yaml`**: Configuration file storing:
    *   User credentials: usernames, emails, display names, hashed passwords, and roles.
    *   Cookie settings for `streamlit-authenticator` (name, key, expiry).
    *   A `preauthorized` email list (a feature of `streamlit-authenticator`).
*   **`generate_hashes.py`**: A utility script used to generate bcrypt password hashes for storing in `config.yaml`.
*   **`pages/`**: A directory containing additional Streamlit pages, which appear as separate sections in the UI's sidebar.
    *   **`02_My_Assigned_Leads.py`**: This page allows users to view leads that have been assigned. Managers can see all assigned leads and to whom they are assigned, while Representatives can only see leads assigned directly to them. Managers also have an option to clear all assigned leads.
    *   **`02_Selected_Leads.py`**: This page displays all leads that have been "moved" or processed from the main list (i.e., all leads present in `st.session_state.moved_leads_df`). It also provides a button to clear all these "moved" leads.
*   **`requirements.txt`**: Lists all Python package dependencies required to run the application (e.g., `streamlit`, `pandas`, `pyyaml`, `streamlit-authenticator`).
*   **`.gitignore`**: Specifies intentionally untracked files that Git should ignore (e.g., virtual environment directories, Python cache files).
*   **`README.md`**: Provides a general overview of the project, key features, and instructions for setup and basic usage, including how to manage users.
*   **`DOCUMENTATION.md`**: This document, offering in-depth technical details about the application's architecture and functionality.

## 3. Authentication System

User authentication is managed by the `streamlit-authenticator` library.

*   **Configuration**: User profiles are defined in `config.yaml` under the `credentials.usernames` key. Each user entry includes:
    *   `email`: User's email address.
    *   `name`: User's display name.
    *   `password`: The bcrypt hashed password.
    *   `role`: Defines the user's role within the application.
*   **Roles**:
    *   **`Manager`**:
        *   Can view all leads in the main dashboard (`app.py`).
        *   Can filter leads.
        *   Can select leads and assign them to users with the 'Representative' role.
        *   Can view all assigned leads on the 'My Assigned Leads' page, including who they are assigned to.
        *   Can clear all assigned leads from the 'My Assigned Leads' page.
    *   **`Representative`**:
        *   Can view all leads in the main dashboard (`app.py`).
        *   Can filter leads.
        *   Can view leads specifically assigned to them on the 'My Assigned Leads' page.
*   **Session Management**: `streamlit-authenticator` uses cookies to manage sessions, configured via the `cookie` section in `config.yaml`.

## 4. Data Management & Flow

*   **Lead Data Source**:
    *   Currently, lead data is hardcoded within the `get_leads()` function in `app.py`, which returns a Pandas DataFrame.
    *   This is intended as a placeholder. For a production environment, this function should be modified to fetch data from a persistent storage solution like a SQL database (e.g., PostgreSQL, MySQL) or a NoSQL database.
*   **Session State Variables**: Streamlit's session state (`st.session_state`) is used extensively to manage data across user interactions and pages:
    *   `st.session_state.leads`: Stores the main DataFrame of all leads, loaded by `get_leads()`.
    *   `st.session_state.checked_lead_ids`: A set containing the `lead_id` of leads that are currently selected (checked) by the user in the main lead table in `app.py`.
    *   `st.session_state.moved_leads_df`: A Pandas DataFrame that accumulates leads when they are assigned by a Manager.
        *   When leads are assigned, they are copied from `st.session_state.leads` to this DataFrame.
        *   Additional columns, `selection_date` (date of assignment) and `assigned_to` (username of the representative), are added to these records.
        *   This DataFrame serves as the data source for both `pages/02_My_Assigned_Leads.py` and `pages/02_Selected_Leads.py`.

## 5. Core Application Logic (`app.py`)

*   **Initialization**:
    *   Sets page config (`st.set_page_config(layout="wide")`).
    *   Initializes the `streamlit-authenticator` instance using credentials from `config.yaml`.
*   **Login**:
    *   The `authenticator.login()` method renders a login form.
    *   Upon successful authentication, session state variables like `authentication_status`, `name`, and `username` are populated.
*   **Main Lead Display (Authenticated Users)**:
    *   A sidebar welcome message and logout button are displayed.
    *   Session state variables (`leads`, `checked_lead_ids`, `moved_leads_df`) are initialized if they don't exist.
    *   **Filtering**:
        *   Leads already present in `st.session_state.moved_leads_df` (i.e., already assigned) are excluded from the main display.
        *   A two-step filtering mechanism is provided in the sidebar:
            1.  **Filter by Category**: A `st.selectbox` allows users to choose a column to filter by (e.g., 'branche', 'size_kategorie'). This dropdown is populated with object-type columns from the original dataset that have more than one unique value.
            2.  **Select Value(s)**: Based on the selected category, a `st.multiselect` box appears, populated with unique values from that category in the original dataset. Users can select one or more values to filter the displayed leads.
    *   **Lead Table**:
        *   Leads are displayed using `st.data_editor`.
        *   A 'Select' checkbox column (type `st.column_config.CheckboxColumn`) is inserted at the beginning of the table to allow users to select leads.
        *   The `lead_id` column is hidden from display.
        *   All other data columns are set to `disabled=True` to make them non-editable in this view.
        *   Selected lead IDs are stored in `st.session_state.checked_lead_ids`.
*   **Lead Assignment (Manager Role Only)**:
    *   If the logged-in user has the 'Manager' role, an "Lead Assignment" section appears in the sidebar.
    *   A `st.selectbox` lists all users with the 'Representative' role (names are fetched from `config.yaml`).
    *   An "Assign to [Representative Name]" button triggers the assignment:
        *   It checks if any leads are selected in `st.session_state.checked_lead_ids`.
        *   Selected leads are copied from `st.session_state.leads`.
        *   `selection_date` (current date) and `assigned_to` (username of the selected representative) are added as new columns.
        *   These processed leads are appended to `st.session_state.moved_leads_df`.
        *   `st.session_state.checked_lead_ids` is cleared.
        *   A success message is shown, and `st.rerun()` is called to refresh the page.

## 6. Page-Specific Details

*   **`pages/02_My_Assigned_Leads.py`**:
    *   Authenticates the user (authentication must occur on each Streamlit page).
    *   Displays a title "My Assigned Leads".
    *   Retrieves data from `st.session_state.moved_leads_df`.
    *   **Manager View**: If the user is a Manager, all leads from `st.session_state.moved_leads_df` are displayed. The assignee's full name (fetched from `config.yaml`) is added as a column for clarity.
    *   **Representative View**: If the user is a Representative, the DataFrame is filtered to show only those leads where the `assigned_to` column matches their `st.session_state['username']`.
    *   A subset of columns (`name`, `number`, `email`, `ort`, `selection_date`, and `assigned_to_name` for managers) is shown for brevity.
    *   **Clear Functionality (Manager Only)**: Managers see a "Clear All Assigned Leads" button. Clicking it re-initializes `st.session_state.moved_leads_df` to an empty DataFrame with the same columns, effectively clearing all records of assigned leads.
*   **`pages/02_Selected_Leads.py`**:
    *   Authenticates the user.
    *   Displays a title "Moved Leads".
    *   Shows all leads currently in `st.session_state.moved_leads_df` using `st.dataframe`.
    *   Includes a "Clear All Moved Leads" button. When clicked, this re-initializes `st.session_state.moved_leads_df` to an empty DataFrame. The logic for determining columns during reset aims to preserve the structure, falling back if necessary. This functionality is similar to the manager's clear button on the "My Assigned Leads" page and might be considered for consolidation or role-specific access in future updates.

## 7. Configuration (`config.yaml`) Details

The `config.yaml` file is central to user management and authentication settings.

*   **`credentials`**:
    *   **`usernames`**: A dictionary where each key is a unique username.
        *   Each username (e.g., `jsmith`) has sub-keys:
            *   `email`: String, user's email.
            *   `name`: String, user's full name for display.
            *   `password`: String, bcrypt hashed password.
            *   `role`: String, either 'Manager' or 'Representative'.
*   **`cookie`**: Settings for the authentication cookie:
    *   `expiry_days`: Integer, how long the login cookie remains valid.
    *   `key`: String, a secret key for signing the cookie.
    *   `name`: String, the name of the cookie.
*   **`preauthorized`**:
    *   `emails`: A list of email addresses. This is a feature of `streamlit-authenticator` that can be used for pre-authorizing sign-ups if the registration feature were enabled (it is not currently used in this application's workflow).

## 8. Password Management (`generate_hashes.py`)

This script simplifies the creation of secure password hashes for `config.yaml`.

*   **Usage**:
    1.  Run the script from the terminal: `python generate_hashes.py`
    2.  The script will prompt you to enter passwords one by one (it's currently set to hash one password: `['test']`). You would modify the list in `stauth.Hasher(['test']).generate()` to include the passwords you want to hash, or input them interactively if the script were modified to do so.
    3.  It uses `streamlit_authenticator.Hasher.generate()` which employs bcrypt.
    4.  The script prints the generated hash(es) to the console.
*   **Updating `config.yaml`**:
    *   Copy the generated hash.
    *   Paste it into the `password` field for the corresponding user in `config.yaml`.
    *   Example: `password: '$2b$12$LNYydJk3efqhEV9ZJpCNGeg4fm1pon19p4zsdV9zQ9pgrYTTvJtyy'`

## 9. Potential Future Enhancements

*   **Database Integration**: Replace the hardcoded `get_leads()` function with a robust database backend (e.g., PostgreSQL, MySQL, MongoDB) for persistent and scalable lead storage.
*   **Lead Editing**: Allow authorized users (e.g., Managers) to edit lead details directly within the UI.
*   **Advanced Analytics/Reporting**: Implement features to visualize lead data, track conversion rates, or generate reports.
*   **User Self-Service**: Add features like password reset or profile editing for users.
*   **File Uploads**: Allow uploading leads from CSV/Excel files.
*   **Enhanced UI/UX**: Further refine the user interface for better usability and modern aesthetics.
*   **Logging**: Implement comprehensive logging for application events and errors.
