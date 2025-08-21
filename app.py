import streamlit as st
import pandas as pd

# --- App Configuration ---
st.set_page_config(page_title="Credentials Manager", layout="centered")

# --- Theme Toggle ---
st.sidebar.title("⚙️ Settings")
theme = st.sidebar.radio("Select Theme", ["Light", "Dark"])

# Apply theme
if theme == "Dark":
    st.markdown(
        """
        <style>
        body { background-color: #121212; color: #e0e0e0; }
        .stDataFrame { background-color: #1e1e1e; color: #fff; }
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
    st.session_state.credentials.pop(index)

def edit_credential(index, service, username, password):
    st.session_state.credentials[index] = {
        "Service": service,
        "Username": username,
        "Password": password,
    }

# --- UI ---
st.title("🔐 Credentials Manager")

with st.form("add_form", clear_on_submit=True):
    st.subheader("Add New Credential")
    service = st.text_input("Service Name")
    username = st.text_input("Username/Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Add Credential")
    if submitted and service and username and password:
        add_credential(service, username, password)
        st.success(f"Credential for '{service}' added!")

# --- Display Credentials ---
if st.session_state.credentials:
    st.subheader("Saved Credentials")
    df = pd.DataFrame(st.session_state.credentials)
    st.dataframe(df)

    selected = st.selectbox("Select Credential to Remove/Edit", range(len(df)))
    if st.button("Remove Selected"):
        remove_credential(selected)
        st.warning("Credential removed!")

    with st.expander("Edit Selected Credential"):
        svc = st.text_input("Edit Service", value=df.iloc[selected]["Service"])
        usr = st.text_input("Edit Username", value=df.iloc[selected]["Username"])
        pwd = st.text_input("Edit Password", value=df.iloc[selected]["Password"])
        if st.button("Save Changes"):
            edit_credential(selected, svc, usr, pwd)
            st.success("Credential updated!")

else:
    st.info("No credentials saved yet.")
