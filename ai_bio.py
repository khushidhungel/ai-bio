import streamlit as st
import requests
import json
import bcrypt
import google.generativeai as genai
from streamlit_option_menu import option_menu
import streamlit_authenticator as stauth

# ==============================
# CONFIGURATION
# ==============================
st.set_page_config(page_title="🧬 BioAI Explorer", page_icon="🧬", layout="wide")
genai.configure(api_key=st.secrets["api"]["gemini_key"])

# ==============================
# LOAD OR INITIALIZE USER DATA
# ==============================
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

users = load_users()

# ==============================
# SIGNUP FUNCTION
# ==============================
def signup(email, password):
    if email in users:
        return False, "User already exists!"
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[email] = hashed_pw
    save_users(users)
    return True, "Account created successfully!"

# ==============================
# LOGIN FUNCTION
# ==============================
def login(email, password):
    if email not in users:
        return False, "No account found!"
    stored_hash = users[email].encode()
    if bcrypt.checkpw(password.encode(), stored_hash):
        return True, "Login successful!"
    return False, "Invalid password!"

# ==============================
# AUTH SECTION
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if not st.session_state.logged_in:
    st.title("🧬 BioAI Explorer Login Portal")

    tab1, tab2 = st.tabs(["🔑 Login", "🧾 Sign Up"])

    with tab1:
        email = st.text_input("📧 Email", key="login_email")
        password = st.text_input("🔒 Password", type="password", key="login_pw")
        if st.button("Login"):
            success, msg = login(email, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user = email
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with tab2:
        new_email = st.text_input("📨 Create Email", key="signup_email")
        new_password = st.text_input("🔐 Create Password", type="password", key="signup_pw")
        if st.button("Sign Up"):
            success, msg = signup(new_email, new_password)
            if success:
                st.success(msg)
            else:
                st.error(msg)

else:
    # ==============================
    # MAIN DASHBOARD
    # ==============================
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/1/1e/Protein_structure.png", use_container_width=True)
        st.title(f"Welcome, {st.session_state.user.split('@')[0].capitalize()} 👋")
        choice = option_menu(
            "Navigation",
            ["Home", "Protein Explorer", "AI Assistant", "Logout"],
            icons=["house", "dna", "robot", "box-arrow-right"],
            menu_icon="cast",
            default_index=0,
        )

    if choice == "Home":
        st.title("🧬 BioAI Explorer")
        st.markdown("""
        Welcome to **BioAI Explorer** — your smart AI companion for bioinformatics exploration.

        🔹 **Search Proteins** from UniProt  
        🔹 **Ask AI** about biological terms or drug/herbal insights  
        🔹 **Visualize** sequences, IDs, and functions  

        ---
        """)

    elif choice == "Protein Explorer":
        st.header("🔍 Explore Protein Data from UniProt")
        protein_id = st.text_input("Enter a UniProt ID (e.g., P69905 for Hemoglobin alpha):")
        if st.button("Fetch Data"):
            if protein_id:
                url = f"https://rest.uniprot.org/uniprotkb/{protein_id}.json"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    st.subheader("Protein Information:")
                    st.json({
                        "Protein Name": data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value"),
                        "Organism": data.get("organism", {}).get("scientificName"),
                        "Length": data.get("sequence", {}).get("length"),
                        "Sequence": data.get("sequence", {}).get("value")[:300] + "..."
                    })
                else:
                    st.error("Protein not found in UniProt.")
            else:
                st.warning("Please enter a UniProt ID.")

    elif choice == "AI Assistant":
        st.header("🤖 BioAI Chat Assistant")
        query = st.text_area("Ask anything about bioinformatics, herbs, or proteins:")
        if st.button("Ask AI"):
            if query.strip():
                model = genai.GenerativeModel("gemini-pro")
                response = model.generate_content(query)
                st.write(response.text)
            else:
                st.warning("Please enter a question.")

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = None
        st.success("You have been logged out successfully!")
        st.rerun()
