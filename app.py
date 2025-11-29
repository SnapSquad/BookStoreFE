import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
import json
import uuid

# === CONFIG ===
st.set_page_config(
    page_title="BookVerse - AI Book Shop",
    page_icon="📚",
    layout="wide"
)

# API Configurations
BOOKS_API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/IWConnect/Hackathon/RetriveAllBooksTask"
BOOKS_API_TOKEN = "eNBKWJ5rIaphA2tRzQVacKRCU4BJwjHQ"
CHAT_API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/IWConnect/Hackathon/BookAgentDriverTask"
CHAT_API_TOKEN = "ckzEfqVw93EyQNzvazLZWa1vOcvNtZGn"


# === FETCH BOOKS FROM API ===
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_books_from_api():
    try:
        headers = {
            "Authorization": f"Bearer {BOOKS_API_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.get(BOOKS_API_URL, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            # Assume API returns list of books or {"books": [...]}
            if isinstance(data, list):
                books = data
            elif isinstance(data, dict) and "books" in data:
                books = data["books"]
            else:
                books = []

            # Convert to consistent format if needed
            formatted_books = []
            for book in books:
                if isinstance(book, dict):
                    formatted_books.append({
                        "id": book.get("id", len(formatted_books) + 1),
                        "title": book.get("title", "Unknown Title"),
                        "author": book.get("author", "Unknown Author"),
                        "genre": book.get("genre", "Unknown"),
                        "price": book.get("price", 0.0),
                        "image_url": book.get("image_url", "")
                    })

            st.success(f"✅ Loaded {len(formatted_books)} books from API!")
            return formatted_books
        else:
            st.warning(f"⚠️ API returned status {response.status_code}. Using sample data.")
            return []  # Or load sample data
    except Exception as e:
        st.error(f"❌ Failed to fetch books: {str(e)}. Using sample data.")
        return []  # Fallback to empty or sample


# === FALLBACK SAMPLE DATA ===
SAMPLE_BOOKS = [
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

# Load books
books_data = fetch_books_from_api()
if not books_data:
    books_data = SAMPLE_BOOKS
    st.info("📚 Using sample data. API fetch failed.")

# Initialize session state
if "cart" not in st.session_state:
    st.session_state.cart = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# === Add book to cart function ===
def add_book_to_cart(book_info):
    title = book_info.get('title', 'Unknown Book')
    book_id = book_info.get('id')

    # Check if book already exists in cart
    for item in st.session_state.cart:
        if item.get("original_id") == book_id or (item.get("title") == title and item.get("original_id") is None):
            item["quantity"] += 1
            return f"✅ Added another **{title}** to cart! (Qty: {item['quantity']})"

    # Add new book
    new_item = {
        "id": f"{book_id}_{uuid.uuid4().hex[:8]}" if book_id else f"chat_{uuid.uuid4().hex[:8]}",
        "original_id": book_id,
        "title": title,
        "author": book_info.get('author', 'Unknown Author'),
        "price": book_info.get('price', 0.0),
        "quantity": 1,
        "image_url": book_info.get('image_url', ''),
        "genre": book_info.get('genre', 'Unknown')
    }

    st.session_state.cart.append(new_item)
    return f"✅ **{title}** added to cart!"


# === API CALL ===
def chat_with_backend_api(current_message: str, chat_history: list, cart: list):
    try:
        headers = {
            "Authorization": f"Bearer {CHAT_API_TOKEN}",
            "Content-Type": "application/json"
        }

        messages_array = []
        for i in range(0, len(chat_history), 2):
            if i < len(chat_history):
                messages_array.append({"role": "user", "content": chat_history[i]["content"]})
            if i + 1 < len(chat_history):
                messages_array.append({"role": "assistant", "content": chat_history[i + 1]["content"]})

        messages_array.append({"role": "user", "content": current_message})

        payload = {
            "messages": messages_array,
            "cart": [{"title": item["title"], "quantity": item.get("quantity", 1)} for item in cart]
        }

        response = requests.post(CHAT_API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            return {
                "response": "I'm having trouble connecting. Let me show you some great books! 📚",
                "books": [books_data[0], books_data[1]]
            }

        data = response.json()
        response_text = "I'm here to help you find great books!"
        books_list = []

        # Handle nested structure
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            if isinstance(first_item, dict) and "response" in first_item:
                nested_response = first_item["response"]
                if isinstance(nested_response, dict):
                    response_text = nested_response.get("response", response_text)
                    books_list = nested_response.get("books", [])
                else:
                    response_text = str(nested_response)
            elif isinstance(first_item, dict):
                response_text = first_item.get("response", response_text)
                books_list = first_item.get("books", [])

        elif isinstance(data, dict):
            if "response" in data:
                nested_response = data["response"]
                if isinstance(nested_response, dict):
                    response_text = nested_response.get("response", response_text)
                    books_list = nested_response.get("books", [])
                else:
                    response_text = str(nested_response)
            else:
                response_text = data.get("response", response_text)
                books_list = data.get("books", [])

        response_text = str(response_text)

        return {
            "response": response_text,
            "books": books_list
        }

    except Exception:
        return {
            "response": "I'm having a moment! 😅 Let me recommend some amazing books:",
            "books": [books_data[0], books_data[1]]
        }


# === Book cards in chat ===
def display_book_cards_in_chat(books, message_index):
    if not books:
        return

    st.markdown("**📚 Recommended Books:**")

    for i, book_info in enumerate(books):
        unique_key = f"chat_book_{message_index}_{i}_{book_info.get('id', i)}"

        col1, col2 = st.columns([1, 4])

        with col1:
            image_url = book_info.get('image_url', '')
            try:
                if image_url:
                    img = Image.open(BytesIO(requests.get(image_url, timeout=5).content))
                    st.image(img, width=80)
                else:
                    st.image(Image.new('RGB', (80, 120), color='#e5e7eb'), width=80)
            except:
                st.image(Image.new('RGB', (80, 120), color='#e5e7eb'), width=80)

        with col2:
            title = book_info.get('title', 'Unknown Book')
            author = book_info.get('author', 'Unknown Author')
            price = book_info.get('price')
            genre = book_info.get('genre', 'Unknown')

            st.markdown(f"**{title}**")
            st.markdown(f"✍️ *{author}*")
            if price:
                st.markdown(f"💰 **${float(price):.2f}**")
            st.caption(f"📂 {genre}")

            if st.button("🛒 Add to Cart", key=unique_key, use_container_width=True):
                success_message = add_book_to_cart(book_info)
                st.success(success_message)
                st.rerun()

        st.markdown("─" * 60)


# === MAIN APP ===
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📚 BookVerse")
    st.markdown("**AI-Powered Book Shop**")
with col2:
    st.metric("📖 Books", len(books_data))
    st.metric("🛒 Cart", sum(item.get("quantity", 0) for item in st.session_state.cart))

# Sidebar
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

tab1, tab2, tab3 = st.tabs(["📚 Browse", "🛒 Cart", "💬 AI Assistant"])

# === BROWSE TAB - DYNAMIC FROM API ===
with tab1:
    st.header("🔍 Browse Books")

    # Search and Filter
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        search = st.text_input("🔍 Search by title or author...")
    with col2:
        genre = st.selectbox("📂 Filter by genre", ["All"] + sorted(set(b["genre"] for b in books_data)))
    with col3:
        price = st.slider("💰 Price range", 0, 50, (0, 50))

    # Filter books
    filtered = books_data
    if search:
        filtered = [b for b in filtered if
                    search.lower() in b["title"].lower() or search.lower() in b["author"].lower()]
    if genre != "All":
        filtered = [b for b in filtered if b["genre"] == genre]
    filtered = [b for b in filtered if price[0] <= b["price"] <= price[1]]

    st.success(f"✅ Found {len(filtered)} books")

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
                st.caption(f"✍️ {book['author']} | 📂 {book['genre']}")
                st.markdown(f"💰 **${book['price']}**")

                if st.button("🛒 Add to Cart", key=f"browse_add_{book['id']}"):
                    success_message = add_book_to_cart(book)
                    st.success(success_message)
                    st.rerun()
    else:
        st.info("No books found matching your criteria. Try adjusting filters!")

# === CART TAB ===
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
                qty = st.number_input("Qty", min_value=1, value=item["quantity"], key=f"qty_{i}")
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
            if st.button("💳 Checkout", type="primary", use_container_width=True):
                st.success("🎉 Order placed successfully! Thank you for shopping at BookVerse! 📦")
                st.balloons()
                st.session_state.cart = []
                st.rerun()
    else:
        st.info("🛒 Your cart is empty. Ask the AI for recommendations or browse books!")

# === CHAT TAB ===
with tab3:
    st.header("💬 BookSnap AI")

    # Display chat history
    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            content = str(message.get("content", ""))
            st.markdown(content)

            # Display books
            books = message.get("books", [])
            if books:
                display_book_cards_in_chat(books, idx)

    # Chat input
    if prompt := st.chat_input("Ask about books..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤖 BookSnap AI is finding perfect recommendations..."):
                response_data = chat_with_backend_api(
                    prompt,
                    st.session_state.chat_history[:-1],
                    st.session_state.cart
                )

            st.markdown(response_data["response"])

            books = response_data.get("books", [])
            if books:
                display_book_cards_in_chat(books, len(st.session_state.chat_history))

        # Store response
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": str(response_data["response"]),
            "books": response_data.get("books", [])
        })

        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6b7280; padding: 1rem;'>
        📚 **BookVerse** • Powered by BookSnap AI • Dynamic Books from API
    </div>
    """,
    unsafe_allow_html=True
)