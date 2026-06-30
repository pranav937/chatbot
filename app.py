import streamlit as st
import importlib
import chatbot_engine
importlib.reload(chatbot_engine)
from chatbot_engine import ChatbotEngine
import datetime
import json
import os
import uuid

st.set_page_config(page_title="Database Chatbot", page_icon="🤖")

def get_chatbot_engine():
    return ChatbotEngine()

bot = get_chatbot_engine()

CHAT_HISTORY_FILE = "chat_history.json"

def load_chats():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_chats(chats):
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, indent=4)

# Load existing chats into session state if not there
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

# Define the questions for product search
SEARCH_QUESTIONS = {
    1: "Which main category are you looking for?",
    2: "Great! Which category within that?",
    3: "Please select a specific sub-category:",
    4: "Where are you located?",
    5: "What is your preferred price range?"
}

MAIN_MENU_OPTIONS = [
    "🔍 Search Products",
    "📝 Register a Complaint",
    "📦 Check Order Status",
    "💬 General Support / Help",
    "📞 Contact Sales / Agent",
    "🎁 View Offers / Discounts"
]

def get_time_based_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning!"
    elif hour < 17:
        return "Good afternoon!"
    else:
        return "Good evening!"

def create_new_chat():
    chat_id = str(uuid.uuid4())
    greeting = get_time_based_greeting()
    
    new_chat = {
        "title": f"New Chat {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "messages": [
            {"role": "assistant", "content": f"{greeting} Welcome to our support. I can help you with information about our products or other services."},
            {"role": "assistant", "content": "How can I help you today?"}
        ],
        "step": "MAIN_MENU",
        "filters": {}
    }
    
    st.session_state.chats[chat_id] = new_chat
    st.session_state.current_chat_id = chat_id
    save_chats(st.session_state.chats)

def update_current_chat():
    chat_id = st.session_state.current_chat_id
    if chat_id in st.session_state.chats:
        save_chats(st.session_state.chats)

def return_to_main_menu():
    chat_id = st.session_state.current_chat_id
    chat = st.session_state.chats[chat_id]
    
    chat["step"] = "MAIN_MENU"
    chat["filters"] = {}
    chat["messages"].append({"role": "assistant", "content": "How can I help you today?"})
    update_current_chat()

# Ensure we always have an active chat
if "current_chat_id" not in st.session_state:
    if st.session_state.chats:
        # Load the most recent chat
        st.session_state.current_chat_id = list(st.session_state.chats.keys())[-1]
    else:
        create_new_chat()

current_chat = st.session_state.chats[st.session_state.current_chat_id]

# Auto-title logic
def set_auto_title(text):
    if current_chat["title"].startswith("New Chat"):
        # Keep title short
        new_title = text[:30] + "..." if len(text) > 30 else text
        current_chat["title"] = new_title
        update_current_chat()

st.title("🤖 Live DB Support Chat")
st.caption("A chatbot that searches your live PostgreSQL database and provides support")

# Sidebar - ChatGPT style
with st.sidebar:
    st.header("Chat History")
    if st.button("➕ New Chat", type="primary", use_container_width=True):
        create_new_chat()
        st.rerun()
        
    st.markdown("---")
    
    # List historical chats
    for c_id, c_data in reversed(list(st.session_state.chats.items())):
        btn_label = c_data.get("title", "Untitled Chat")
        if c_id == st.session_state.current_chat_id:
            btn_label = f"📍 {btn_label}" # highlight current
            
        if st.button(btn_label, key=f"hist_{c_id}", use_container_width=True):
            st.session_state.current_chat_id = c_id
            st.rerun()

# Helper to append message
def append_message(role, content):
    current_chat["messages"].append({"role": role, "content": content})
    update_current_chat()

# Display chat messages
for message in current_chat["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input (Bottom) ---
requires_text = current_chat["step"] in ["COMPLAINT_2", "ORDER_1", "FEEDBACK_2"]
prompt_text = "Type your message or search for products here..."
if current_chat["step"] == "COMPLAINT_2":
    prompt_text = "Type your complaint description here..."
elif current_chat["step"] == "ORDER_1":
    prompt_text = "Enter your Order ID..."
elif current_chat["step"] == "FEEDBACK_2":
    prompt_text = "Enter your additional comments..."

prompt = st.chat_input(prompt_text)

if prompt:
    append_message("user", prompt)
    set_auto_title(prompt)
    
    # State machine routing for text inputs
    if current_chat["step"] == "COMPLAINT_2":
        append_message("assistant", f"Thank you. Your complaint has been registered with Ticket ID #APP-{len(prompt) + 10000}. We will resolve it soon.")
        current_chat["step"] = "END"
        
    elif current_chat["step"] == "ORDER_1":
        append_message("assistant", f"Checking... Order {prompt} is currently in transit and will be delivered within 2-3 business days.")
        current_chat["step"] = "END"
        
    elif current_chat["step"] == "FEEDBACK_2":
        append_message("assistant", "Thank you for your valuable feedback!")
        current_chat["step"] = "FINAL_END"
        
    else:
        # Process free-text chat/search as fallback
        response = bot.search_products_by_keyword(prompt)
        append_message("assistant", response)
        current_chat["step"] = "END"
        
    update_current_chat()
    st.rerun()

# --- Button UI Logic ---
if current_chat["step"] == "MAIN_MENU":
    st.write("### Please select an option:")
    cols = st.columns(3)
    for i, option in enumerate(MAIN_MENU_OPTIONS):
        col = cols[i % 3]
        if col.button(option, key=f"btn_main_{i}_{len(current_chat['messages'])}", use_container_width=True):
            append_message("user", option)
            set_auto_title(option)
            
            if "Search Products" in option:
                current_chat["step"] = "SEARCH_1"
                append_message("assistant", SEARCH_QUESTIONS[1])
            elif "Complaint" in option:
                current_chat["step"] = "COMPLAINT_1"
                append_message("assistant", "What type of complaint do you have?")
            elif "Order Status" in option:
                current_chat["step"] = "ORDER_1"
                append_message("assistant", "Please enter your Order ID in the chat box below.")
            elif "General Support" in option:
                current_chat["step"] = "SUPPORT_1"
                append_message("assistant", "What do you need help with?")
            elif "Sales" in option:
                current_chat["step"] = "SALES_1"
                append_message("assistant", "Are you a new customer or an existing customer?")
            elif "Offers" in option:
                append_message("assistant", "Here are our current offers:\n1. 10% off on all Construction materials.\n2. Free shipping on orders over ₹5,000.")
                current_chat["step"] = "END"
                
            update_current_chat()
            st.rerun()

elif current_chat["step"].startswith("SEARCH_"):
    search_step_num = int(current_chat["step"].split("_")[1])
    options = bot.get_options_for_step(search_step_num, current_chat["filters"])
    
    if not options:
        search_step_num += 1
        current_chat["step"] = f"SEARCH_{search_step_num}"
        update_current_chat()
        st.rerun()
        
    st.write("### Please select an option:")
    cols = st.columns(3)
    
    for i, option in enumerate(options):
        col = cols[i % 3]
        if col.button(option, key=f"btn_search_{search_step_num}_{i}_{len(current_chat['messages'])}", use_container_width=True):
            append_message("user", option)
            
            if search_step_num == 1:
                current_chat["filters"]["main_category"] = option
            elif search_step_num == 2:
                current_chat["filters"]["category"] = option
            elif search_step_num == 3:
                current_chat["filters"]["subcategory"] = option
            elif search_step_num == 4:
                current_chat["filters"]["location"] = option
            elif search_step_num == 5:
                current_chat["filters"]["budget"] = option
                
            search_step_num += 1
            
            if search_step_num <= 5:
                current_chat["step"] = f"SEARCH_{search_step_num}"
                append_message("assistant", SEARCH_QUESTIONS[search_step_num])
            else:
                response = bot.search_filtered_products(current_chat["filters"])
                append_message("assistant", response)
                current_chat["step"] = "END"
                
            update_current_chat()
            st.rerun()

elif current_chat["step"] == "COMPLAINT_1":
    st.write("### Please select a complaint type:")
    options = ["Product Quality", "Delivery Delay", "Billing Issue", "Other"]
    cols = st.columns(2)
    for i, option in enumerate(options):
        if cols[i % 2].button(option, key=f"btn_comp_{i}_{len(current_chat['messages'])}", use_container_width=True):
            append_message("user", option)
            current_chat["step"] = "COMPLAINT_2"
            append_message("assistant", "Please briefly describe your issue in the chat box below.")
            update_current_chat()
            st.rerun()

elif current_chat["step"] == "SUPPORT_1":
    st.write("### Please select a support topic:")
    options = ["Returns & Refunds", "Warranty Information", "Technical Support", "Speak to Agent"]
    cols = st.columns(2)
    for i, option in enumerate(options):
        if cols[i % 2].button(option, key=f"btn_sup_{i}_{len(current_chat['messages'])}", use_container_width=True):
            append_message("user", option)
            
            if "Returns" in option:
                reply = "We offer a 30-day return policy for unused products. Please email support@example.com."
            elif "Warranty" in option:
                reply = "Most of our products come with a 1-year manufacturer warranty."
            elif "Technical" in option:
                reply = "For technical support, please call 1-800-TECH-HELP."
            else:
                reply = "Transferring you to a human agent... (This is a demo!)"
                
            append_message("assistant", reply)
            current_chat["step"] = "END"
            update_current_chat()
            st.rerun()

elif current_chat["step"] == "SALES_1":
    st.write("### Please select your profile:")
    options = ["New Customer", "Existing Customer", "Partnership Inquiry"]
    cols = st.columns(3)
    for i, option in enumerate(options):
        if cols[i % 3].button(option, key=f"btn_sales_{i}_{len(current_chat['messages'])}", use_container_width=True):
            append_message("user", option)
            reply = f"Thank you, {option}. You can reach our sales team at sales@example.com or call +91-9876543210."
            append_message("assistant", reply)
            current_chat["step"] = "END"
            update_current_chat()
            st.rerun()

elif current_chat["step"] == "END":
    st.write("### How was your experience?")
    options = ["⭐⭐⭐⭐⭐ Excellent", "⭐⭐⭐ Average", "⭐ Poor"]
    cols = st.columns(3)
    for i, option in enumerate(options):
        if cols[i % 3].button(option, key=f"btn_feed_{i}_{len(current_chat['messages'])}", use_container_width=True):
            append_message("user", option)
            current_chat["step"] = "FEEDBACK_2"
            append_message("assistant", "Any additional comments? Please type them below.")
            update_current_chat()
            st.rerun()
            
    st.write("---")
    st.write("### Need something else?")
    if st.button("Main Menu", type="primary"):
        return_to_main_menu()
        st.rerun()

elif current_chat["step"] == "FINAL_END":
    st.write("### Need something else?")
    if st.button("Main Menu", type="primary"):
        return_to_main_menu()
        st.rerun()
