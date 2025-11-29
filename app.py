import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
import json
import uuid
import time

# === CONFIG ===
st.set_page_config(
    page_title="BookVerse - AI Book Shop",
    page_icon="📚",
    layout="wide"
)

# API Configurations
BOOKS_API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/IWConnect/Hackathon/RetriveAllBooksTask"
BOOKS_API_TOKEN = "eNBKWJ5rIaphA2tRzQVacKRCU4BJwjHQ"
CHAT_API_URL = "https://eks-ultra.snaplogic-demo.com/api/1/rest/feed-master/queue/ConnectFasterInc/IWConnect/Hackathon/BookAgentDriver_Ultra"
CHAT_API_TOKEN = "nnWP8mDzAw80OfTDgxyp5WPBSQXj2659"


# === ULTRA-FAST 3-LAYER CACHING SYSTEM ===
@st.cache_data(ttl=3600, show_spinner=False)  # 1 HOUR CACHE - NO SPINNER
def fetch_books_from_api():
    """ULTRA-FAST book fetching with optimized processing"""
    start_time = time.time()

    try:
        headers = {
            "Authorization": f"Bearer {BOOKS_API_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.get(BOOKS_API_URL, headers=headers)

        if response.status_code == 200:
            data = response.json()
            books = data if isinstance(data, list) else data.get("books", data.get("data", data.get("items", [])))

            # 🚀 ULTRA-FAST PROCESSING (SIMPLIFIED)
            formatted_books = []
            for i, book in enumerate(books):
                if isinstance(book, dict):
                    # ⚡ SUPER FAST GENRE DETECTION
                    genre = "Fiction"

                    # Direct field checks (no loops)
                    if book.get("genre"):
                        genre = str(book["genre"]).strip()
                    elif book.get("category"):
                        genre = str(book["category"]).strip()
                    elif book.get("bookGenre"):
                        genre = str(book["bookGenre"]).strip()
                    else:
                        # Fast title-based detection
                        title_lower = str(book.get("title", "")).lower()
                        if any(kw in title_lower for kw in ["mystery", "crime", "thriller"]):
                            genre = "Mystery"
                        elif any(kw in title_lower for kw in ["romance", "love"]):
                            genre = "Romance"
                        elif any(kw in title_lower for kw in ["sci", "space", "future"]):
                            genre = "Science Fiction"
                        elif any(kw in title_lower for kw in ["fantasy", "magic", "dragon"]):
                            genre = "Fantasy"

                    formatted_books.append({
                        "id": book.get("id") or book.get("bookId") or i + 1,
                        "title": book.get("title") or f"Book {i + 1}",
                        "author": book.get("author") or "Unknown Author",
                        "genre": genre,
                        "price": float(book.get("price") or 9.99),
                        "image_url": book.get("image_url") or book.get("image") or "",
                        "description": book.get("description", "")
                    })

            load_time = time.time() - start_time
            print(f"🚀 Books loaded in {load_time:.2f}s - {len(formatted_books)} books")
            return formatted_books

    except Exception as e:
        print(f"❌ Books error: {e}")
        return []


# === SEPARATE IMAGE CACHE - 2 HOURS ===
@st.cache_data(ttl=7200, show_spinner=False, max_entries=200)
def load_single_image(image_url):
    """Dedicated image cache - separate from books"""
    try:
        if image_url:
            response = requests.get(image_url, timeout=2)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
    except:
        pass
    return None


# === PRE-COMPUTED GENRE CACHE ===
@st.cache_data(ttl=3600, show_spinner=False)
def get_genres_and_counts(books_data):
    """Pre-compute genres for instant filtering"""
    genre_counts = {}
    for book in books_data:
        genre = book.get('genre', 'Unknown')
        genre_counts[genre] = genre_counts.get(genre, 0) + 1

    display_genres = ["All"]
    for genre, count in sorted(genre_counts.items()):
        if genre != 'Unknown' and count > 0:
            display_genres.append(f"{genre} ({count})")

    return display_genres


# === LIGHTNING-FAST BOOK LOADING ===
@st.cache_data(ttl=3600, show_spinner=False)
def get_books():
    """Final cached books with ALL pre-computations"""
    books = fetch_books_from_api()
    genres = get_genres_and_counts(books)
    return books, genres


# === INITIAL LOAD - ULTRA-FAST ===
books_data, genre_list = get_books()

# === SESSION STATE ===
if "cart" not in st.session_state:
    st.session_state.cart = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# === Add book to cart ===
def add_book_to_cart(book_info):
    title = book_info.get('title', 'Unknown Book')
    book_id = book_info.get('id')

    for item in st.session_state.cart:
        if item.get("original_id") == book_id:
            item["quantity"] += 1
            return f"✅ Added another **{title}** to cart! (Qty: {item['quantity']})"

    new_item = {
        "id": f"{book_id}_{uuid.uuid4().hex[:8]}",
        "original_id": book_id,
        "title": title,
        "author": book_info.get('author', 'Unknown Author'),
        "price": book_info.get('price', 9.99),
        "quantity": 1,
        "image_url": book_info.get('image_url', ''),
        "genre": book_info.get('genre', 'Unknown')
    }

    st.session_state.cart.append(new_item)
    return f"✅ **{title}** added to cart!"


# === Chat API ===
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
                "response": "I'm having trouble connecting to the book catalog. I can still chat about books though!",
                "books": []
            }

        data = response.json()
        response_text = "I'm here to help you find great books!"
        books_list = []

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

        return {
            "response": str(response_text),
            "books": books_list
        }

    except:
        return {
            "response": "I'm having a moment! 😅 Tell me what kind of books you're looking for!",
            "books": []
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
            cached_img = load_single_image(image_url)
            if cached_img:
                st.image(cached_img, width=80)
            else:
                st.markdown("📖")

        with col2:
            title = book_info.get('title', 'Unknown Book')
            author = book_info.get('author', 'Unknown Author')
            price = book_info.get('price')
            genre = book_info.get('genre', 'Unknown')

            st.markdown(f"**{title}**")
            st.markdown(f"✍️ *{author}*")
            if price and price > 0:
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

    st.divider()
    if st.button("🔄 Refresh Books", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📚 Browse", "🛒 Cart", "💬 AI Assistant"])

# === ULTRA-FAST BROWSE TAB ===
with tab1:
    st.header("🔍 Browse Books")

    if not books_data:
        st.info("📚 No books available. Click 'Refresh Books' in sidebar to try again.")
    else:
        # ✅ PRE-COMPUTED GENRES - INSTANT!
        display_genres = genre_list

        # Filters
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            search = st.text_input("🔍 Search by title or author")
        with col2:
            genre = st.selectbox("📂 Filter by genre", display_genres, index=0)
        with col3:
            price_range = st.slider("💰 Price range", 0, 100, (0, 100))
            min_price, max_price = price_range

        # Extract selected genre
        selected_genre = genre.split(" (")[0] if genre != "All" else "All"

        # 🚀 ULTRA-FAST FILTERING
        filtered = books_data.copy()

        if search:
            search_lower = search.lower()
            filtered = [b for b in filtered if
                        search_lower in b["title"].lower() or
                        search_lower in str(b["author"]).lower()]

        if selected_genre != "All":
            filtered = [b for b in filtered if b["genre"] == selected_genre]

        filtered = [b for b in filtered if min_price <= b["price"] <= max_price]

        st.metric("📚", len(filtered), f"of {len(books_data)} books")

        if filtered:
            # 🚀 SHOW FIRST 24 BOOKS INSTANTLY
            display_limit = 24
            cols = st.columns(4)

            for i, book in enumerate(filtered[:display_limit]):
                with cols[i % 4]:
                    # ⚡ CACHED IMAGES
                    cached_img = load_single_image(book.get("image_url"))
                    if cached_img:
                        st.image(cached_img, width=180)
                    else:
                        st.markdown("📖")

                    st.markdown(f"**{book['title']}**")
                    st.caption(f"✍️ {book['author']}")
                    st.caption(f"📂 {book['genre']}")
                    if book['price'] > 0:
                        st.markdown(f"💰 **${book['price']:.2f}**")

                    if st.button("🛒 Add", key=f"browse_add_{book['id']}", use_container_width=True):
                        success_message = add_book_to_cart(book)
                        st.success(success_message)
                        st.rerun()

                    st.markdown("─" * 20)

            # Show more info
            if len(filtered) > display_limit:
                st.info(f"🚀 Showing first {display_limit} books for speed. "
                        f"({len(filtered) - display_limit} more available - use filters!)")
        else:
            st.info("🔍 No books found matching your criteria.")

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
                st.markdown(f"${item['price']:.2f}")
            with col3:
                qty = st.number_input("Qty", min_value=1, value=item["quantity"], key=f"qty_{i}")
                if qty != item["quantity"]:
                    item["quantity"] = qty
                    st.rerun()
            with col4:
                if st.button("🗑️", key=f"del_{i}", use_container_width=True):
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
        st.info("🛒 Your cart is empty. Browse books or ask the AI for recommendations!")

# === CHAT TAB ===
with tab3:
    st.header("💬 BookSnap AI")

    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            content = str(message.get("content", ""))
            st.markdown(content)

            books = message.get("books", [])
            if books:
                display_book_cards_in_chat(books, idx)

    if "waiting_for_response" not in st.session_state:
        st.session_state.waiting_for_response = False

    if st.session_state.waiting_for_response:
        with st.chat_message("assistant"):
            with st.spinner("🤖 BookSnap AI is finding perfect recommendations..."):
                st.markdown("**Thinking...** 💭")
                st.markdown("I'm searching our catalog for the best books for you!")

    if prompt := st.chat_input("Ask about books..."):
        st.session_state.waiting_for_response = True
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

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

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": str(response_data["response"]),
            "books": response_data.get("books", [])
        })
        st.session_state.waiting_for_response = False
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6b7280; padding: 1rem;'>
        📚 BookVerse • Powered by SnapSquad
    </div>
    """,
    unsafe_allow_html=True
)