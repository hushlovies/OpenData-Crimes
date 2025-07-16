import streamlit as st
import requests

st.title("Greeting App")

if st.button("Say Hello"):
    try:
        response = requests.get("http://127.0.0.1:5000/api/greet")
        if response.status_code == 200:
            data = response.json()
            st.success(data["message"])
        else:
            st.error("Error calling the API")
    except Exception as e:
        st.error(f"Failed to connect to the API: {e}")
