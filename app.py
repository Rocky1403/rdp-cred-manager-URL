# app.py
import streamlit as st
from pathlib import Path
import re
import csv
import platform
import subprocess
import os
from datetime import datetime
from github import Github, InputGitTreeElement

APP_TITLE = "Credentials Manager (Streamlit)"
DEFAULT_FILE = "credentials.txt"  # stored in repo root

st.set_page_config(APP_TITLE, layout="wide")

# ----------------------------
# Data store (same behaviour)
# ----------------------------
class CredStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.creds = []
        self.load()

    def set_path(self, path: str):
        self.path = Path(path)
        self.load()

    def load(self):
        self.creds = []
        if not self.path.exists():
            return
        current = None
        with self.path.open(encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                if line.startswith("Credential #"):
                    if current:
                        self.creds.append(current)
                    current = {"domain":"", "ip":"", "user":"", "password":""}
                    continue
                if line.startswith("----------------------------------------"):
                    continue
                m = re.match(r"^(Domain|IP|User|Password)\s*:\s*(.*)$", line, flags=re.IGNORECASE)
                if m and current is not None:
                    key = m.group(1).lower()
                    val = m.group(2).strip()
                    if key == "domain":
                        current["domain"] = val
                    elif key == "ip":
                        current["ip"] = val
                    elif key == "user":
                        current["user"] = val
                    elif key == "password":
                        current["password"] = val
        if current:
            # If file ended without an explicit new "Credential #" (edge case)
            # make sure last block isn't empty before appending
            if any(current.values()):
                self.creds.append(current)

    def text(self):
        out = []
        for i, c in enumerate(self.creds, start=1):
            out.append("----------------------------------------")
            out.append(f"Credential #{i}")
            out.append(f"Domain   : {c.get('domain','')}")
            out.append(f"IP       : {c.get('ip','')}")
            out.append(f"User     : {c.get('user','')}")
            out.append(f"Password : {c.get('password','')}")
        return "\n".join(out) + ("\n" if out else "")

    def save_local(self):
        # Save to local filesystem (ephemeral on Streamlit Cloud)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            f.write(self.text())

    def add(self, domain, ip, user, password):
        self.creds.append({"domain":domain.strip(), "ip":ip.strip(), "user":user.strip(), "password":password})
        self.save_local()

    def update(self, index, domain, ip, user, password):
        self.creds[index] = {"domain":domain.strip(), "ip":ip.strip(), "user":user.strip(), "password":password}
        self.save_local()

    def remove(self, index):
        del self.creds[index]
        self.save_local()

# ----------------------------
# GitHub push helper (optional persistence)
# ----------------------------
def commit_to_github(repo_full_name: str, path_in_repo: str, content_bytes: bytes, commit_message: str, token: str) -> bool:
    """
    Commit a file to the repo using PyGithub.
    repo_full_name: "username/reponame"
    path_in_repo: path within repo, e.g. "credentials.txt"
    content_bytes: new file content bytes
    token: GitHub personal access token with repo access
    Returns True on success.
    """
    try:
        gh = Github(token)
        repo = gh.get_repo(repo_full_name)
        # try to get file; if exists, update; otherwise create
        try:
            contents = repo.get_contents(path_in_repo)
            repo.update_file(path_in_repo, commit_message, content_bytes.decode("utf-8"), contents.sha)
        except Exception:
            # file not found -> create
            repo.create_file(path_in_repo, commit_message, content_bytes.decode("utf-8"))
        return True
    except Exception as e:
        st.error(f"GitHub commit failed: {e}")
        return False

# ----------------------------
# UI / App
# ----------------------------
st.title(APP_TITLE)
st.markdown("Manage credentials. **Note:** On Streamlit Cloud, local files are ephemeral — see sidebar options for persistence (commit to GitHub or use external storage).")

# session store for store instance
if "store" not in st.session_state:
    st.session_state.store = CredStore(DEFAULT_FILE)

store: CredStore = st.session_state.store

# Sidebar - repo / persistence settings
st.sidebar.header("Persistence / Deployment")
st.sidebar.markdown("If you want edits to survive app restarts, either commit changes back to this GitHub repo or use external storage.")

repo_full = st.sidebar.text_input("GitHub repo (owner/repo)", value="")
token = st.sidebar.text_input("GitHub token (set via Secrets for production)", value="", type="password")
commit_on_change = st.sidebar.checkbox("Auto-commit changes to GitHub", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("**Storage file** (in app container):")
file_path = st.sidebar.text_input("Path", value=str(store.path))
if st.sidebar.button("Reload from path"):
    store.set_path(file_path)
    st.experimental_rerun()

# show table
st.subheader("Credentials")
if not store.creds:
    st.info("No credentials found (file empty). Add a new credential below.")
else:
    rows = []
    for i, c in enumerate(store.creds):
        rows.append({"No": i+1, "Domain": c["domain"], "IP": c["ip"], "User": c["user"]})
    st.dataframe(rows, use_container_width=True)

# select index
selected = st.selectbox("Select credential to edit/remove/show", options=list(range(len(store.creds))) if store.creds else [], format_func=lambda x: f"{x+1}" if isinstance(x,int) else x)

# Add / Edit form
with st.form("add_edit", clear_on_submit=False):
    st.markdown("### Add / Edit Credential")
    col1, col2 = st.columns(2)
    with col1:
        domain = st.text_input("Domain", value=(store.creds[selected]["domain"] if store.creds and isinstance(selected,int) else ""))
        ip = st.text_input("IP", value=(store.creds[selected]["ip"] if store.creds and isinstance(selected,int) else ""))
    with col2:
        user = st.text_input("User", value=(store.creds[selected]["user"] if store.creds and isinstance(selected,int) else ""))
        password = st.text_input("Password", value=(store.creds[selected]["password"] if store.creds and isinstance(selected,int) else ""), type="password")
    submitted = st.form_submit_button("Save / Add")
    if submitted:
        if not (domain and ip and user):
            st.warning("Domain, IP and User are required.")
        else:
            if store.creds and isinstance(selected,int) and selected < len(store.creds):
                # update
                store.update(selected, domain, ip, user, password)
                st.success("Updated credential locally.")
            else:
                store.add(domain, ip, user, password)
                st.success("Added credential locally.")
            # optionally commit to GitHub
            if commit_on_change and repo_full and (token or st.secrets.get("GITHUB_TOKEN")):
                token_to_use = token or st.secrets.get("GITHUB_TOKEN")
                commit_msg = f"Updated credentials (by Streamlit) {datetime.utcnow().isoformat()}Z"
                ok = commit_to_github(repo_full, Path(file_path).name, store.text().encode("utf-8"), commit_msg, token_to_use)
                if ok:
                    st.success("Committed changes to GitHub.")
            st.experimental_rerun()

# Show password
if st.button("Show selected password"):
    if store.creds:
        st.info(f"Password: `{store.creds[selected]['password'] or '(empty)'}`")
    else:
        st.warning("No entry selected.")

# Remove
if st.button("Remove selected"):
    if store.creds:
        store.remove(selected)
        st.success("Removed locally.")
        if commit_on_change and repo_full and (token or st.secrets.get("GITHUB_TOKEN")):
            token_to_use = token or st.secrets.get("GITHUB_TOKEN")
            commit_msg = f"Removed credential (by Streamlit) {datetime.utcnow().isoformat()}Z"
            ok = commit_to_github(repo_full, Path(file_path).name, store.text().encode("utf-8"), commit_msg, token_to_use)
            if ok:
                st.success("Committed deletion to GitHub.")
        st.experimental_rerun()
    else:
        st.warning("No credential to remove.")

# Export CSV
if st.button("Export as CSV (download)"):
    if not store.creds:
        st.warning("No data to export.")
    else:
        csv_out = "No,Domain,IP,User,Password\n"
        for i,c in enumerate(store.creds, start=1):
            csv_out += f"{i},{c['domain']},{c['ip']},{c['user']},{c['password']}\n"
        st.download_button("Download CSV", csv_out, file_name="credentials_export.csv", mime="text/csv")

# Launch RDP (Windows only)
if st.button("Launch RDP (Windows only)"):
    if not store.creds:
        st.warning("No selection.")
    else:
        ipaddr = store.creds[selected]["ip"].strip()
        if not ipaddr:
            st.error("Selected credential has no IP address.")
        elif os.name != "nt":
            st.error("RDP launch is only supported on Windows.")
        else:
            try:
                subprocess.Popen(["mstsc", f"/v:{ipaddr}"], shell=False)
                st.success(f"Launching RDP to {ipaddr}")
            except FileNotFoundError:
                st.error("mstsc not found on this system.")

# Status
st.markdown("---")
st.write(f"**Storage file (local):** `{store.path}`  |  **Total:** {len(store.creds)} credential(s)")

# Footer: hint about tokens
st.markdown("**Note**: For production auto-commit, create a GitHub Personal Access Token (repo scope) and add it to Streamlit app secrets as `GITHUB_TOKEN`. See Streamlit docs for secrets management.")
