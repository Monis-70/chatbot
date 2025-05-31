import streamlit as st
import requests
from fpdf import FPDF
import base64

# --- CONFIGURATION ---
OLLAMA_MODEL = "mistral"

# --- PAGE SETUP ---
st.set_page_config(
    page_title="MISTRAL Chatbot",
    page_icon="🦙",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- THEME SWITCHER ---
st.sidebar.title("⚙️ Settings")
theme = st.sidebar.radio("Choose Theme", ["Light", "Dark"])
st.session_state.theme = theme

# --- CUSTOM CSS ---
if theme == "Dark":
    st.markdown("""
        <style>
        body { background-color: #1c1c1c; color: white; }
        .chat-bubble { 
            border-radius: 10px; 
            padding: 10px 15px; 
            margin: 8px 0;
            max-width: 80%;
        }
        .user { 
            background-color: #005f73; 
            color: white; 
            margin-left: 20%;
        }
        .assistant { 
            background-color: #264653; 
            color: #fff;
            margin-right: 20%;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        body { background-color: #fdf6e3; color: black; }
        .chat-bubble { 
            border-radius: 10px; 
            padding: 10px 15px; 
            margin: 8px 0;
            max-width: 80%;
        }
        .user { 
            background-color: #a8dadc; 
            color: black;
            margin-left: 20%;
        }
        .assistant { 
            background-color: #f1faee; 
            color: black;
            margin-right: 20%;
        }
        </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.markdown(
    "<h1 style='text-align: center;'>🦙 MISTRAL Chatbot</h1><p style='text-align: center; color: gray;'>Local • Private • Fast (Powered by Ollama)</p>",
    unsafe_allow_html=True
)
st.divider()

# --- CHAT SESSION ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- USER INPUT ---
user_input = st.chat_input("Ask me anything...")

if user_input:
    # Add user message to history and display
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(f"<div class='chat-bubble user'>{user_input}</div>", unsafe_allow_html=True)

    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "http://localhost:8000/chat",
                    json={"messages": st.session_state.chat_history},
                    timeout=30
                )
                response.raise_for_status()
                response_data = response.json()
                
                assistant_reply = response_data.get("response") or f"❌ Error: {response_data.get('error', 'Unknown error')}"
                    
            except requests.exceptions.RequestException as e:
                assistant_reply = f"❌ Connection error: {str(e)}"
            except Exception as e:
                assistant_reply = f"❌ Unexpected error: {str(e)}"

            st.markdown(f"<div class='chat-bubble assistant'>{assistant_reply}</div>", unsafe_allow_html=True)

# --- DISPLAY CHAT HISTORY ---
with st.expander("Full Chat History"):
    for msg in st.session_state.chat_history:
        role_class = "user" if msg["role"] == "user" else "assistant"
        st.markdown(f"<div class='chat-bubble {role_class}' style='opacity: 0.8;'>{msg['content']}</div>", 
                   unsafe_allow_html=True)
            

# --- EXPORT CHAT TO PDF ---
def export_chat_to_pdf(chat_history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        pdf.multi_cell(0, 10, f"{role}: {msg['content']}\n")

    pdf_file = "chat_history.pdf"
    pdf.output(pdf_file)

    with open(pdf_file, "rb") as f:
        pdf_data = f.read()
        b64 = base64.b64encode(pdf_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="chat_history.pdf">📄 Download Chat PDF</a>'
        st.sidebar.markdown(href, unsafe_allow_html=True)

# --- SIDEBAR: EXPORT ---
st.sidebar.markdown("### 📤 Export")
if st.sidebar.button("Export Chat to PDF"):
    export_chat_to_pdf(st.session_state.chat_history)
