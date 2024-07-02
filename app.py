from dotenv import load_dotenv
import streamlit as st




load_dotenv()

st.set_page_config(page_title="Restaurant Bot", layout="wide", page_icon=":speech_baloon:")

st.title("Chat with Restaurant ChatBot")

with st.sidebar:
    st.subheader("Settings")
    st.write("This is an example code")
    