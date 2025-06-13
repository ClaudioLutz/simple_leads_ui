import streamlit_authenticator as stauth

hasher = stauth.Hasher()
hashed_password = hasher.hash('test')
print(hashed_password)
