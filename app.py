import streamlit as st
import pandas as pd

# --- App Configuration ---
st.set_page_config(page_title="Credentials Manager", layout="centered")

# --- Theme & Styles ---
st.markdown(
    """
    <style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .main {
        background-color: #f7f7f7;
    }
    .stDataFrame {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
    }
    h1, h2, h3, h4 {
        color: #333333;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Data Storage ---
if "credentials" not in st.session_state:
    st.session_state.credentials = []

# --- Functions ---
def add_credential(service, username, password):
    st.session_state.credentials.append(
        {"Service": service, "Username": username, "Password": password}
    )

def remove_credential(index):
    if 0 <= index < len(st.session_state.credentials):
        st.session_state.credentials.pop(index)

def edit_credential(index, service, username, password):
    if 0 <= index < len(st.session_state.credentials):
        st.session_state.credentials[index] = {
            "Service": service,
            "Username": username,
            "Password": password,
        }

# --- UI ---
st.title("🔐 Credentials Manager")
st.write("Manage your credentials with ease — add, edit, or remove them below.")

# --- Add Credential Form ---
with st.form("add_form", clear_on_submit=True):
    st.subheader("➕ Add New Credential")
    service = st.text_input("Service Name")
    username = st.text_input("Username/Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Add Credential")
    if submitted:
        if service and username and password:
            add_credential(service, username, password)
            st.success(f"Credential for **{service}** added!")
        else:
            st.error("Please fill out all fields before adding.")

# --- Display Credentials ---
if st.session_state.credentials:
    st.subheader("📋 Saved Credentials")
    df = pd.DataFrame(st.session_state.credentials)
    st.dataframe(df, use_container_width=True)

    selected = st.selectbox(
        "Select a credential to Edit/Remove",
        options=range(len(df)),
        format_func=lambda i: df.iloc[i]["Service"]
    )

    # --- Edit Section ---
    st.markdown("---")
    st.subheader("✏️ Edit Selected Credential")
    svc = st.text_input("Edit Service", value=df.iloc[selected]["Service"])
    usr = st.text_input("Edit Username", value=df.iloc[selected]["Username"])
    pwd = st.text_input("Edit Password", value=df.iloc[selected]["Password"])
    if st.button("Save Changes"):
        edit_credential(selected, svc, usr, pwd)
        st.success("Credential updated!")

    # --- Remove Button ---
    if st.button("Remove Selected Credential"):
        remove_credential(selected)
        st.warning("Credential removed!")
else:
    st.info("No credentials saved yet.")
