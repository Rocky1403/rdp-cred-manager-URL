import streamlit as st
import pandas as pd

# --- App Configuration ---
st.set_page_config(page_title="Server Credentials Manager", layout="centered")

# --- Default Theme ---
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # light or dark

# --- Custom Styles ---
def apply_styles():
    if st.session_state.theme == "dark":
        bg_color = "#1e1e1e"
        text_color = "#ffffff"
        card_color = "#2c2c2c"
        button_color = "#5c5c5c"
        hover_color = "#777777"
    else:
        bg_color = "#f7f7f7"
        text_color = "#333333"
        card_color = "#ffffff"
        button_color = "#4CAF50"
        hover_color = "#45a049"

    st.markdown(
        f"""
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
        <style>
        body, .main {{
            font-family: 'Poppins', sans-serif;
            background-color: {bg_color};
            color: {text_color};
        }}
        .stDataFrame {{
            background-color: {card_color};
            border-radius: 10px;
            padding: 10px;
        }}
        h1, h2, h3, h4 {{
            color: {text_color};
        }}
        .stButton>button {{
            background-color: {button_color};
            color: white;
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: bold;
        }}
        .stButton>button:hover {{
            background-color: {hover_color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_styles()

# --- Data Storage ---
if "credentials" not in st.session_state:
    st.session_state.credentials = []
if "page" not in st.session_state:
    st.session_state.page = "menu"  # menu, add, view

# --- Functions ---
def add_credential(domain, ip, username, password):
    st.session_state.credentials.append(
        {"Domain": domain, "IP": ip, "User": username, "Password": password}
    )

def remove_credential(index):
    if 0 <= index < len(st.session_state.credentials):
        st.session_state.credentials.pop(index)

def edit_credential(index, domain, ip, username, password):
    if 0 <= index < len(st.session_state.credentials):
        st.session_state.credentials[index] = {
            "Domain": domain,
            "IP": ip,
            "User": username,
            "Password": password,
        }

# --- Theme Toggle Popup ---
with st.expander("🌗 Theme Settings", expanded=False):
    selected_theme = st.radio("Choose Theme", ["Light", "Dark"])
    if selected_theme.lower() != st.session_state.theme:
        st.session_state.theme = selected_theme.lower()
        st.experimental_rerun()

# --- Main Menu ---
if st.session_state.page == "menu":
    st.title("🌐 Server Credentials Manager")
    st.write("Manage your server credentials with style and ease.")

    if st.button("➕ Add New Credential"):
        st.session_state.page = "add"

    if st.button("📋 View/Edit/Remove Credentials"):
        st.session_state.page = "view"

# --- Add Credential Page ---
elif st.session_state.page == "add":
    st.title("➕ Add New Server Credential")
    with st.form("add_form", clear_on_submit=True):
        domain = st.text_input("Domain Name")
        ip = st.text_input("IP Address")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Add Credential")
        if submitted:
            if domain and ip and username and password:
                add_credential(domain, ip, username, password)
                st.success(f"Credential for **{domain}** added!")
            else:
                st.error("Please fill out all fields before adding.")

    if st.button("⬅️ Back to Menu"):
        st.session_state.page = "menu"

# --- View/Edit/Remove Page ---
elif st.session_state.page == "view":
    st.title("📋 Saved Credentials")
    if st.session_state.credentials:
        df = pd.DataFrame(st.session_state.credentials)
        st.dataframe(df, use_container_width=True)

        selected = st.selectbox(
            "Select a credential to Edit/Remove",
            options=range(len(df)),
            format_func=lambda i: f"{df.iloc[i]['Domain']} ({df.iloc[i]['IP']})"
        )

        st.subheader("✏️ Edit Selected Credential")
        dom = st.text_input("Edit Domain", value=df.iloc[selected]["Domain"])
        ip_edit = st.text_input("Edit IP", value=df.iloc[selected]["IP"])
        usr = st.text_input("Edit Username", value=df.iloc[selected]["User"])
        pwd = st.text_input("Edit Password", value=df.iloc[selected]["Password"])
        if st.button("Save Changes"):
            edit_credential(selected, dom, ip_edit, usr, pwd)
            st.success("Credential updated!")

        if st.button("Remove Selected Credential"):
            remove_credential(selected)
            st.warning("Credential removed!")
    else:
        st.info("No credentials saved yet.")

    if st.button("⬅️ Back to Menu"):
        st.session_state.page = "menu"
