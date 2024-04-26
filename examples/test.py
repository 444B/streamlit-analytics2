import streamlit as st
import os
import streamlit_analytics2 as streamlit_analytics
# Function to retrieve the password securely
def get_password():
    # Try retrieving from Streamlit secrets
    password = st.secrets.get("SA2_PASSWORD")
    if password is None:
        print("Password not found in Streamlit secrets.")
        # Fallback to environment variable
        password = os.getenv("SA2_PASSWORD")
        print("Password found in environment variable.")
    return password

def main():
    # Authenticate user
    password = get_password()
    if password is None:
        st.error("Password configuration not found. Please set up 'SA2_PASSWORD'.")
        return

    # Password input from user
    password_input = st.text_input("Enter your password", type="password")

    # Verify password and start tracking if correct
    if password_input == password:
        with streamlit_analytics.track():
            st.success("Authentication successful. Displaying secure analytics data.")
            # Place your secure or admin-only content here
    else:
        st.error("Incorrect password. Please try again.")

if __name__ == "__main__":
    main()
