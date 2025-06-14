# Simple Lead Management UI

A Streamlit web application for managing, filtering, and assigning sales leads.

## Key Features

*   **User Authentication**: Secure login for Managers and Representatives with distinct roles.
*   **Lead Display & Filtering**: View a list of leads and dynamically filter them by various attributes like industry, company size, etc.
*   **Lead Assignment**: Managers can assign leads to Sales Representatives.
*   **Dedicated Lead Views**:
    *   **My Assigned Leads**: Representatives see leads assigned specifically to them. Managers see all assigned leads.
    *   **Selected Leads**: A view of all leads that have been processed or "moved" from the main list.

## Technologies Used

*   **Streamlit**: For creating the interactive web application.
*   **Pandas**: For data manipulation and management.
*   **PyYAML**: For managing configuration (user credentials, etc.).
*   **streamlit-authenticator**: For handling user authentication.

## Setup and Run

1.  **Prerequisites**:
    *   Python 3.8+

2.  **Clone the Repository**:
    ```bash
    git clone <your-repository-url>
    cd simple_leads_ui
    ```

3.  **Create a Virtual Environment (Recommended)**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the Application**:
    ```bash
    streamlit run app.py
    ```
    The application should now be open in your web browser.

## User Management

Users, their roles (Manager or Representative), and their hashed passwords are defined in the `config.yaml` file.

**To add a new user or change a password**:

1.  **Generate Password Hash**:
    Run the `generate_hashes.py` script:
    ```bash
    python generate_hashes.py
    ```
    Enter the desired password when prompted. The script will output a hashed version of the password.

2.  **Update `config.yaml`**:
    Open `config.yaml` and add or update the user details under the `credentials.usernames` section. For example:
    ```yaml
    credentials:
      usernames:
        newuser: # This is the username
          email: newuser@example.com
          name: New User Name
          password: 'generated_hash_goes_here' # Paste the hash from step 1
          role: 'Representative' # Or 'Manager'
    # ... other users and configurations
    ```

    Ensure the `password` field contains the generated hash. Save the file. The changes will take effect the next time the application is run or when the authentication module reloads its configuration (typically on app restart).
