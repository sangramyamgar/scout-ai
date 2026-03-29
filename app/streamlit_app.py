"""
Streamlit UI for FinSolve AI Assistant.
Provides a chat interface with role-based authentication.
"""

import os
import sys
from pathlib import Path

import requests
import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================
# Configuration
# ============================================

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ============================================
# Page Config
# ============================================

st.set_page_config(
    page_title="FinSolve AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================
# Custom CSS
# ============================================

st.markdown(
    """
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .source-box {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin-top: 0.5rem;
        font-size: 0.85rem;
    }
    .role-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================
# Session State
# ============================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.role_name = ""
    st.session_state.access = []
    st.session_state.messages = []


# ============================================
# Helper Functions
# ============================================


def login(username: str, password: str) -> bool:
    """Authenticate with the API."""
    try:
        response = requests.get(
            f"{API_URL}/login",
            auth=(username, password),
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.password = password  # Store for API calls
            st.session_state.role = data.get("role", "")
            st.session_state.role_name = data.get("role_name", "")
            st.session_state.access = data.get("access", [])
            return True
        else:
            return False
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server. Make sure it's running.")
        return False
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return False


def send_message(message: str) -> dict:
    """Send a message to the chat API."""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            auth=(st.session_state.username, st.session_state.password),
            json={"message": message, "include_sources": True},
            timeout=60,
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return {"response": "⚠️ Rate limit exceeded. Please try again later.", "sources": []}
        else:
            return {"response": f"Error: {response.status_code}", "sources": []}
    except requests.exceptions.ConnectionError:
        return {"response": "⚠️ Cannot connect to API server.", "sources": []}
    except Exception as e:
        return {"response": f"Error: {str(e)}", "sources": []}


def get_usage() -> dict:
    """Get usage statistics."""
    try:
        response = requests.get(
            f"{API_URL}/usage",
            auth=(st.session_state.username, st.session_state.password),
            timeout=10,
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}


def logout():
    """Clear session state."""
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.password = ""
    st.session_state.role = ""
    st.session_state.role_name = ""
    st.session_state.access = []
    st.session_state.messages = []


# ============================================
# Login Page
# ============================================


def show_login():
    """Display login form."""
    st.title("🤖 FinSolve AI Assistant")
    st.markdown("### Internal Knowledge Base Chatbot")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")
        st.markdown("#### Login")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if username and password:
                    if login(username, password):
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    st.warning("Please enter username and password")

        st.markdown("---")
        st.markdown("#### Demo Accounts")

        demo_accounts = {
            "Engineering": ("Tony", "password123"),
            "Finance": ("Sam", "financepass"),
            "HR": ("Natasha", "hrpass123"),
            "Marketing": ("Bruce", "securepass"),
            "C-Level (Full Access)": ("Nick", "director123"),
            "Employee": ("Happy", "employee123"),
        }

        st.markdown("| Role | Username | Password |")
        st.markdown("|------|----------|----------|")
        for role, (user, pwd) in demo_accounts.items():
            st.markdown(f"| {role} | `{user}` | `{pwd}` |")


# ============================================
# Chat Page
# ============================================


def show_chat():
    """Display chat interface."""
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown(f"**Role:** {st.session_state.role_name}")

        st.markdown("---")
        st.markdown("#### 📂 Data Access")
        for collection in st.session_state.access:
            st.markdown(f"- {collection.title()}")

        st.markdown("---")

        # Usage stats
        usage = get_usage()
        if usage:
            st.markdown("#### 📊 Usage Today")
            remaining = usage.get("remaining_requests", 0)
            total = usage.get("max_requests_per_day", 100)
            st.progress(1 - (remaining / total) if total > 0 else 0)
            st.markdown(f"{remaining}/{total} requests remaining")

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()

    # Main chat area
    st.title("🤖 FinSolve AI Assistant")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Show sources if available
            if msg.get("sources"):
                with st.expander("📚 Sources"):
                    for source in msg["sources"]:
                        st.markdown(
                            f"**[{source['index']}] {source['department'].title()}** - {source['filename']}"
                        )
                        st.markdown(f"_{source['chunk']}_")
                        st.markdown("---")

    # Chat input
    if prompt := st.chat_input("Ask a question about FinSolve..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = send_message(prompt)

            st.markdown(result.get("response", "Error"))

            # Show sources
            sources = result.get("sources", [])
            if sources:
                with st.expander("📚 Sources"):
                    for source in sources:
                        st.markdown(
                            f"**[{source['index']}] {source['department'].title()}** - {source['filename']}"
                        )
                        st.markdown(f"_{source['chunk']}_")
                        st.markdown("---")

        # Save assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("response", ""),
            "sources": sources,
        })


# ============================================
# Main
# ============================================


def main():
    """Main application entry point."""
    if st.session_state.authenticated:
        show_chat()
    else:
        show_login()


if __name__ == "__main__":
    main()
