import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
from datetime import datetime
import json

# === CONFIG ===
st.set_page_config(
    page_title="BookVerse - AI Book Shop",
    page_icon="📚",
    layout="wide"
)

# API Configuration
API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/IWConnect/Hackathon/BookAgentDriverTask"
API_TOKEN = "ckzEfqVw93EyQNzvazLZWa1vOcvNtZGn"

# === SIMPLE CSS ===
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stMetric > label {
        color: #4f46e5;
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# === BOOKS DATA ===
books_data = [
    {"id": 1, "title": "The Midnight Library", "author": "Matt Haig", "genre": "Fiction", "price": 18.99,
     "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=300"},
    {"id": 2, "title": "Dune", "author": "Frank Herbert", "genre": "Science Fiction", "price": 22.50,
     "image_url": "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=300"},
    {"id": 3, "title": "Atomic Habits", "author": "James Clear", "genre": "Self-Help", "price": 16.99,
     "image_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=300"},
    {"id": 4, "title": "Sapiens", "author": "Yuval Noah Harari", "genre": "History", "price": 19.99,
     "image_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=300"},
    {"id": 5, "title": "Project Hail Mary", "author": "Andy Weir", "genre": "Science Fiction", "price": 20.00,
     "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=300"},
    {"id": 6, "title": "Klara and the Sun", "author": "Kazuo Ishiguro", "genre": "Literary Fiction", "price": 21.50,
     "image_url": "https://images.unsplash.com/photo-1491841573334-9bde9f1709a0?w=300"},
    {"id": 7, "title": "The Psychology of Money", "author": "Morgan Housel", "genre": "Finance", "price": 17.99,
     "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f3abd8c?w=300"},
    {"id": 8, "title": "Educated", "author": "Tara Westover", "genre": "Memoir", "price": 18.99,
     "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300"},
    {"id": 9, "title": "1984", "author": "George Orwell", "genre": "Dystopian", "price": 12.99,
     "image_url": "https://images.unsplash.com/photo-1530538987395-7f02970410e0?w=300"},
    {"id": 10, "title": "The Alchemist", "author": "Paulo Coelho", "genre": "Fiction", "price": 14.99,
     "image_url": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=300"}
]

# Initialize session state
if "cart" not in st.session_state:
    st.session_state.cart = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# === API CALL - SENDS FULL MESSAGES ARRAY ===
def chat_with_backend_api(current_message: str, chat_history: list, cart: list):
    try:
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }

        # ✅ CREATE FULL MESSAGES ARRAY
        messages_array = []

        # Add all previous conversation (user prompt → assistant response)
        for i in range(0, len(chat_history) - 1, 2):  # Step by 2 to get user-assistant pairs
            if i < len(chat_history):
                # User message
                messages_array.append({
                    "role": "user",
                    "content": chat_history[i]["content"]
                })
            if i + 1 < len(chat_history):
                # Assistant response
                messages_array.append({
                    "role": "assistant",
                    "content": chat_history[i + 1]["content"]
                })

        # Add current user message (latest prompt)
        messages_array.append({
            "role": "user",
            "content": current_message
        })

        # ✅ FINAL PAYLOAD FORMAT
        payload = {
            "messages": messages_array,  # ✅ Array of {role, content} objects
            "cart": [{"title": item["title"], "quantity": item.get("quantity", 1)} for item in cart]
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()

        data = response.json()

        # Handle list response
        if isinstance(data, list) and len(data) > 0:
            return {
                "response": data[0].get("response", "I'm here to help with books!"),
                "recommendations": data[0].get("recommendations", [])
            }
        else:
            return {
                "response": data.get("response", "I'm here to help with books!"),
                "recommendations": data.get("recommendations", [])
            }

    except Exception:
        return {
            "response": "I'm having trouble connecting. Please try again!",
            "recommendations": []
        }


# === MAIN APP ===
col1, col2 = st.columns([3, 1])

with col1:
    st.title("📚 BookVerse")
    st.markdown("**AI-Powered Book Shop**")

with col2:
    st.metric("📖 Books", len(books_data))
    st.metric("🛒 Cart", sum(item.get("quantity", 0) for item in st.session_state.cart))

# === CLEAN SIDEBAR - NO CONTEXT INFO ===
with st.sidebar:
    st.header("⚡ Quick Actions")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Cart", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
    with col2:
        if st.button("💬 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    st.divider()
    st.markdown("""
    **Try asking:**
    • "Recommend cooking books"
    • "Find Dune"
    • "Sci-fi books"
    • "Best sellers"
    """)

# === TABS ===
tab1, tab2, tab3 = st.tabs(["📚 Browse", "🛒 Cart", "💬 AI Assistant"])

# === TAB 1: Browse ===
with tab1:
    st.header("🔍 Browse Books")

    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search = st.text_input("Search...")
    with col2:
        genre = st.selectbox("Genre", ["All"] + sorted(set(b["genre"] for b in books_data)))
    with col3:
        price = st.slider("Price", 0, 25, (0, 25))

    filtered = books_data
    if search:
        filtered = [b for b in filtered if
                    search.lower() in b["title"].lower() or search.lower() in b["author"].lower()]
    if genre != "All":
        filtered = [b for b in filtered if b["genre"] == genre]
    filtered = [b for b in filtered if price[0] <= b["price"] <= price[1]]

    if filtered:
        cols = st.columns(4)
        for i, book in enumerate(filtered):
            with cols[i % 4]:
                try:
                    img = Image.open(BytesIO(requests.get(book["image_url"], timeout=3).content))
                except:
                    img = Image.new('RGB', (200, 280), color='#e5e7eb')

                st.image(img, use_container_width=True)
                st.markdown(f"**{book['title']}**")
                st.caption(book['author'])
                st.markdown(f"${book['price']}")

                if st.button("🛒 Add", key=f"add_{book['id']}"):
                    for item in st.session_state.cart:
                        if item["id"] == book["id"]:
                            item["quantity"] += 1
                            st.success(f"Added another {book['title']}")
                            st.rerun()
                            break
                    else:
                        st.session_state.cart.append({
                            "id": book["id"], "title": book["title"],
                            "author": book["author"], "price": book["price"],
                            "quantity": 1, "image_url": book["image_url"]
                        })
                        st.success(f"{book['title']} added to cart!")
                        st.rerun()
    else:
        st.info("No books found")

# === TAB 2: Cart ===
with tab2:
    st.header("🛒 Shopping Cart")

    if st.session_state.cart:
        total = 0
        for i, item in enumerate(st.session_state.cart):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{item['title']}**")
                st.caption(item['author'])
            with col2:
                st.markdown(f"${item['price']}")
            with col3:
                qty = st.number_input("", min_value=1, value=item["quantity"], key=f"qty_{i}")
                if qty != item["quantity"]:
                    item["quantity"] = qty
                    st.rerun()
            with col4:
                if st.button("🗑️", key=f"del_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            total += item["price"] * item["quantity"]

        st.divider()
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### **Total: ${total:.2f}**")
        with col2:
            if st.button("💳 Checkout", type="primary"):
                st.success("🎉 Order placed successfully!")
                st.balloons()
                st.rerun()
    else:
        st.info("Your cart is empty")

# === TAB 3: AI CHAT WITH FULL MESSAGES ARRAY ===
with tab3:
    st.header("💬 BookSnap AI")

    # Show chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Simple chat input
    if prompt := st.chat_input("Ask about books..."):
        # 1. Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Get AI response WITH FULL MESSAGES ARRAY
        with st.chat_message("assistant"):
            response_data = chat_with_backend_api(
                prompt,  # Current message
                st.session_state.chat_history,  # Full history for array creation
                st.session_state.cart
            )
            st.markdown(response_data["response"])

        # 3. Add AI response to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response_data["response"]
        })

        # 4. Limit history to last 20 messages (10 conversations)
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[-20:]

        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6b7280; padding: 1rem;'>
        📚 **BookVerse** • Powered by BookSnap AI
    </div>
    """,
    unsafe_allow_html=True
)