import streamlit as st
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
import json
import uuid
import time
import hashlib
import os
from datetime import datetime

# === CONFIG ===
st.set_page_config(
    page_title="BookVerse - AI Book Shop",
    page_icon="📚",
    layout="wide"
)

# Custom avatar configuration
USER_AVATAR = "👤"  # User icon
ASSISTANT_AVATAR = "🤖"  # Robot/AI icon

# API Configurations
BOOKS_API_URL = "https://emea.snaplogic.com/api/1/rest/slsched/feed/ConnectFasterInc/IWConnect/Hackathon/RetriveAllBooksTask"
BOOKS_API_TOKEN = "eNBKWJ5rIaphA2tRzQVacKRCU4BJwjHQ"
CHAT_API_URL = "https://eks-ultra.snaplogic-demo.com/api/1/rest/feed-master/queue/ConnectFasterInc/IWConnect/Hackathon/BookAgentDriver_Ultra"
CHAT_API_TOKEN = "nnWP8mDzAw80OfTDgxyp5WPBSQXj2659"

# User data storage file
USER_DATA_FILE = "users_data.json"


# === ULTRA-FAST 3-LAYER CACHING SYSTEM ===
@st.cache_data(ttl=3600, show_spinner=False)
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

            formatted_books = []
            for i, book in enumerate(books):
                if isinstance(book, dict):
                    genre = "Fiction"

                    if book.get("genre"):
                        genre = str(book["genre"]).strip()
                    elif book.get("category"):
                        genre = str(book["category"]).strip()
                    elif book.get("bookGenre"):
                        genre = str(book["bookGenre"]).strip()
                    else:
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


@st.cache_data(ttl=3600, show_spinner=False)
def get_books():
    """Final cached books with ALL pre-computations"""
    books = fetch_books_from_api()
    genres = get_genres_and_counts(books)
    return books, genres


books_data, genre_list = get_books()

# === AUTHENTICATION FUNCTIONS ===
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load user data from JSON file"""
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users_data):
    """Save user data to JSON file"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users_data, f, indent=2)

def register_user(username, email, password):
    """Register a new user"""
    users = load_users()
    
    if username in users:
        return False, "Username already exists"
    
    if any(user.get("email") == email for user in users.values()):
        return False, "Email already registered"
    
    users[username] = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "preferences": {
            "favorite_genres": [],
            "price_range": [0, 100],
            "notifications": True
        },
        "wishlist": [],
        "order_history": [],
        "chat_history": [],
        "created_at": datetime.now().isoformat()
    }
    
    save_users(users)
    return True, "Registration successful!"

def authenticate_user(username, password):
    """Authenticate a user"""
    users = load_users()
    
    if username not in users:
        return False, None
    
    user = users[username]
    if user["password_hash"] == hash_password(password):
        return True, user
    else:
        return False, None

def get_user_data(username):
    """Get user data"""
    users = load_users()
    return users.get(username)

def update_user_data(username, user_data):
    """Update user data"""
    users = load_users()
    if username in users:
        users[username].update(user_data)
        save_users(users)

def add_to_wishlist(username, book_info):
    """Add book to user's wishlist"""
    user_data = get_user_data(username)
    if user_data:
        wishlist = user_data.get("wishlist", [])
        book_id = book_info.get('id')
        
        # Check if already in wishlist
        if not any(item.get('id') == book_id for item in wishlist):
            wishlist.append({
                "id": book_id,
                "title": book_info.get('title'),
                "author": book_info.get('author'),
                "price": book_info.get('price'),
                "image_url": book_info.get('image_url'),
                "genre": book_info.get('genre'),
                "added_at": datetime.now().isoformat()
            })
            user_data["wishlist"] = wishlist
            update_user_data(username, user_data)
            return True
    return False

def remove_from_wishlist(username, book_id):
    """Remove book from user's wishlist"""
    user_data = get_user_data(username)
    if user_data:
        wishlist = user_data.get("wishlist", [])
        user_data["wishlist"] = [item for item in wishlist if item.get('id') != book_id]
        update_user_data(username, user_data)
        return True
    return False

def save_order(username, cart_items, total):
    """Save order to user's order history"""
    user_data = get_user_data(username)
    if user_data:
        order_history = user_data.get("order_history", [])
        order_history.append({
            "order_id": str(uuid.uuid4()),
            "items": cart_items.copy(),
            "total": total,
            "date": datetime.now().isoformat()
        })
        user_data["order_history"] = order_history
        update_user_data(username, user_data)
        return True
    return False

def save_chat_history(username, chat_history):
    """Save chat history to user's data"""
    user_data = get_user_data(username)
    if user_data:
        # Convert chat history to a serializable format
        serializable_history = []
        for msg in chat_history:
            serializable_msg = {
                "role": msg.get("role"),
                "content": msg.get("content", ""),
                "books": msg.get("books", []),
                "timestamp": msg.get("timestamp", datetime.now().isoformat())
            }
            serializable_history.append(serializable_msg)
        
        user_data["chat_history"] = serializable_history
        update_user_data(username, user_data)
        return True
    return False

def load_chat_history(username):
    """Load chat history from user's data"""
    user_data = get_user_data(username)
    if user_data:
        return user_data.get("chat_history", [])
    return []

def get_personalized_recommendations(username, books_data):
    """Get personalized book recommendations based on user preferences and history"""
    user_data = get_user_data(username)
    if not user_data:
        return books_data[:12]  # Return first 12 books if not logged in
    
    preferences = user_data.get("preferences", {})
    favorite_genres = preferences.get("favorite_genres", [])
    order_history = user_data.get("order_history", [])
    wishlist = user_data.get("wishlist", [])
    
    # Collect genres from order history
    ordered_genres = []
    for order in order_history:
        for item in order.get("items", []):
            if item.get("genre"):
                ordered_genres.append(item["genre"])
    
    # Combine favorite genres and ordered genres
    preferred_genres = list(set(favorite_genres + ordered_genres))
    
    # Score books based on preferences
    scored_books = []
    for book in books_data:
        score = 0
        genre = book.get("genre", "")
        
        # Boost score for preferred genres
        if genre in preferred_genres:
            score += 10
        
        # Boost score if in wishlist
        if any(w.get('id') == book.get('id') for w in wishlist):
            score += 5
        
        # Boost score for books from previously ordered authors
        ordered_authors = []
        for order in order_history:
            for item in order.get("items", []):
                if item.get("author"):
                    ordered_authors.append(item["author"])
        
        if book.get("author") in ordered_authors:
            score += 3
        
        scored_books.append((score, book))
    
    # Sort by score and return top recommendations
    scored_books.sort(key=lambda x: x[0], reverse=True)
    recommendations = [book for _, book in scored_books[:12]]
    
    # If we don't have enough recommendations, fill with other books
    if len(recommendations) < 12:
        remaining = [book for book in books_data if book not in recommendations]
        recommendations.extend(remaining[:12 - len(recommendations)])
    
    return recommendations

# === SESSION STATE ===
if "cart" not in st.session_state:
    st.session_state.cart = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "scroll_trigger" not in st.session_state:
    st.session_state.scroll_trigger = 0
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "show_login" not in st.session_state:
    st.session_state.show_login = False
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False
if "chat_loaded" not in st.session_state:
    st.session_state.chat_loaded = False


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


# === FIXED CHAT API - PROPER MESSAGE HANDLING ===
def chat_with_backend_api(current_message: str, chat_history: list, cart: list):
   
    try:
        headers = {
            "Authorization": f"Bearer {CHAT_API_TOKEN}",
            "Content-Type": "application/json"
        }

        # Get user data if authenticated
        user_data = None
        if st.session_state.authenticated and st.session_state.username:
            user_data = get_user_data(st.session_state.username)

        # Build messages array from chat history
        messages_array = []

        # Add all previous messages in order (they already have correct roles)
        for msg in chat_history:
            # Only include user and assistant messages, skip the books data
            user_email = user_data.get("email", "guest") if st.session_state.authenticated and user_data else "guest"
            messages_array.append({
                "role": msg["role"],
                "content": msg["content"],
                "username": user_email if msg["role"] == "user" else "assistant"
            })

        # Add the current user message
        user_email = user_data.get("email", "guest") if st.session_state.authenticated and user_data else "guest"
        messages_array.append({
            "role": "user",
            "content": current_message,
            "username": user_email
        })

        payload = {
            "messages": messages_array,
            "cart": [],
            "email": user_data.get("email", "guest") if st.session_state.authenticated and user_data else "guest"
        }

        response = requests.post(CHAT_API_URL, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return {
                "response": "I'm having trouble connecting to the book catalog. I can still chat about books though!",
                "books": []
            }

        data = response.json()
        response_text = "I'm here to help you find great books!"
        books_list = []

        # Parse response
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

        print(f"✅ Received response with {len(books_list)} books")

        return {
            "response": str(response_text),
            "books": books_list
        }

    except Exception as e:
        print(f"❌ Chat API Exception: {e}")
        return {
            "response": "I'm having a moment! 😅 Tell me what kind of books you're looking for!",
            "books": []
        }


# === ANIMATED TEXT DISPLAY ===
def stream_text(text, placeholder):
    """
    Creates a typing animation effect
    """
    displayed_text = ""
    words = text.split()

    # Stream word by word for smooth effect
    for i, word in enumerate(words):
        displayed_text += word + " "
        placeholder.markdown(displayed_text)

        # Adjust speed: faster for short words, slower for long ones
        if len(word) > 8:
            time.sleep(0.08)
        else:
            time.sleep(0.05)

    # Final update with complete text
    placeholder.markdown(text)


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
            # Safely convert price to float
            try:
                price_float = float(price) if price is not None else 0
                if price_float > 0:
                    st.markdown(f"💰 **${price_float:.2f}**")
            except (ValueError, TypeError):
                pass  # Skip price display if conversion fails
            st.caption(f"📂 {genre}")

            if st.button("🛒 Add to Cart", key=unique_key, use_container_width=True):
                success_message = add_book_to_cart(book_info)
                st.success(success_message)
                st.rerun()

        st.markdown("─" * 60)


# === AUTHENTICATION UI ===
def show_login_form():
    """Display login form"""
    with st.form("login_form"):
        st.subheader("🔐 Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        col1, col2 = st.columns(2)
        with col1:
            login_submit = st.form_submit_button("Login", use_container_width=True)
        with col2:
            if st.form_submit_button("Sign Up", use_container_width=True):
                st.session_state.show_login = False
                st.session_state.show_signup = True
                st.rerun()
        
        if login_submit:
            if username and password:
                success, user = authenticate_user(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.show_login = False
                    # Load saved chat history
                    saved_chat = load_chat_history(username)
                    if saved_chat:
                        st.session_state.chat_history = saved_chat
                    st.session_state.chat_loaded = True
                    st.success(f"Welcome back, {username}! 👋")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")

def show_signup_form():
    """Display signup form"""
    with st.form("signup_form"):
        st.subheader("✨ Create Account")
        username = st.text_input("Username", key="signup_username")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        col1, col2 = st.columns(2)
        with col1:
            signup_submit = st.form_submit_button("Sign Up", use_container_width=True)
        with col2:
            if st.form_submit_button("Back to Login", use_container_width=True):
                st.session_state.show_signup = False
                st.session_state.show_login = True
                st.rerun()
        
        if signup_submit:
            if not username or not email or not password:
                st.warning("Please fill in all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.warning("Password must be at least 6 characters")
            else:
                success, message = register_user(username, email, password)
                if success:
                    st.success(message)
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.show_signup = False
                    # Initialize empty chat history for new user
                    st.session_state.chat_history = []
                    st.session_state.chat_loaded = True
                    st.rerun()
                else:
                    st.error(message)

# === MAIN APP ===
# Show login/signup if not authenticated
if not st.session_state.authenticated:
    if st.session_state.show_signup:
        show_signup_form()
    else:
        show_login_form()
    st.stop()

# Load chat history if user is authenticated but chat hasn't been loaded yet
if st.session_state.authenticated and st.session_state.username and not st.session_state.chat_loaded:
    saved_chat = load_chat_history(st.session_state.username)
    if saved_chat:
        st.session_state.chat_history = saved_chat
    st.session_state.chat_loaded = True

# Main app header
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    st.title("📚 BookVerse")
    st.markdown("**AI-Powered Book Shop**")
with col2:
    st.metric("📖 Books", len(books_data))
with col3:
    st.metric("🛒 Cart", sum(item.get("quantity", 0) for item in st.session_state.cart))
with col4:
    user_data = get_user_data(st.session_state.username)
    wishlist_count = len(user_data.get("wishlist", [])) if user_data else 0
    st.metric("❤️ Wishlist", wishlist_count)

# Sidebar
with st.sidebar:
    # User profile section
    st.header(f"👤 {st.session_state.username}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.cart = []
        st.session_state.chat_history = []
        st.session_state.chat_loaded = False
        st.rerun()
    
    st.divider()
    
    st.header("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Cart", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
    with col2:
        if st.button("💬 Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            # Also clear saved chat history
            if st.session_state.authenticated and st.session_state.username:
                save_chat_history(st.session_state.username, [])
            st.rerun()

    st.divider()
    if st.button("🔄 Refresh Books", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    # User preferences
    st.header("⚙️ Preferences")
    user_data = get_user_data(st.session_state.username)
    if user_data:
        preferences = user_data.get("preferences", {})
        favorite_genres = preferences.get("favorite_genres", [])
        
        available_genres = [g.split(" (")[0] for g in genre_list if g != "All"]
        selected_genres = st.multiselect(
            "Favorite Genres",
            available_genres,
            default=favorite_genres
        )
        
        if st.button("💾 Save Preferences", use_container_width=True):
            preferences["favorite_genres"] = selected_genres
            update_user_data(st.session_state.username, {"preferences": preferences})
            st.success("Preferences saved!")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📚 Browse", "🛒 Cart", "💬 AI Assistant", "❤️ Wishlist", "📋 Orders"])

# === BROWSE TAB ===
with tab1:
    st.header("🔍 Browse Books")
    
    # Show personalized recommendations if logged in
    user_data = get_user_data(st.session_state.username)
    if user_data:
        st.subheader("✨ Personalized Recommendations")
        recommendations = get_personalized_recommendations(st.session_state.username, books_data)
        
        if recommendations:
            rec_cols = st.columns(4)
            for i, book in enumerate(recommendations[:8]):
                with rec_cols[i % 4]:
                    cached_img = load_single_image(book.get("image_url"))
                    if cached_img:
                        st.image(cached_img, width=150)
                    else:
                        st.markdown("📖")
                    
                    st.markdown(f"**{book['title']}**")
                    st.caption(f"✍️ {book['author']}")
                    try:
                        price_val = float(book.get('price', 0))
                        if price_val > 0:
                            st.markdown(f"💰 **${price_val:.2f}**")
                    except (ValueError, TypeError):
                        pass
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🛒", key=f"rec_cart_{book['id']}", use_container_width=True):
                            add_book_to_cart(book)
                            st.rerun()
                    with col2:
                        in_wishlist = any(w.get('id') == book.get('id') for w in user_data.get("wishlist", []))
                        if in_wishlist:
                            if st.button("❤️", key=f"rec_wish_rm_{book['id']}", use_container_width=True):
                                remove_from_wishlist(st.session_state.username, book.get('id'))
                                st.rerun()
                        else:
                            if st.button("🤍", key=f"rec_wish_add_{book['id']}", use_container_width=True):
                                add_to_wishlist(st.session_state.username, book)
                                st.rerun()
        
        st.divider()

    if not books_data:
        st.info("📚 No books available. Click 'Refresh Books' in sidebar to try again.")
    else:
        display_genres = genre_list

        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            search = st.text_input("🔍 Search by title or author")
        with col2:
            genre = st.selectbox("📂 Filter by genre", display_genres, index=0)
        with col3:
            price_range = st.slider("💰 Price range", 0, 100, (0, 100))
            min_price, max_price = price_range

        selected_genre = genre.split(" (")[0] if genre != "All" else "All"

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
            display_limit = 24
            cols = st.columns(4)

            for i, book in enumerate(filtered[:display_limit]):
                with cols[i % 4]:
                    cached_img = load_single_image(book.get("image_url"))
                    if cached_img:
                        st.image(cached_img, width=180)
                    else:
                        st.markdown("📖")

                    st.markdown(f"**{book['title']}**")
                    st.caption(f"✍️ {book['author']}")
                    st.caption(f"📂 {book['genre']}")
                    try:
                        price_val = float(book.get('price', 0))
                        if price_val > 0:
                            st.markdown(f"💰 **${price_val:.2f}**")
                    except (ValueError, TypeError):
                        pass

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🛒 Add", key=f"browse_add_{book['id']}", use_container_width=True):
                            success_message = add_book_to_cart(book)
                            st.success(success_message)
                            st.rerun()
                    with col2:
                        user_data = get_user_data(st.session_state.username)
                        in_wishlist = any(w.get('id') == book.get('id') for w in user_data.get("wishlist", [])) if user_data else False
                        if in_wishlist:
                            if st.button("❤️", key=f"browse_wish_rm_{book['id']}", use_container_width=True):
                                remove_from_wishlist(st.session_state.username, book.get('id'))
                                st.rerun()
                        else:
                            if st.button("🤍", key=f"browse_wish_add_{book['id']}", use_container_width=True):
                                add_to_wishlist(st.session_state.username, book)
                                st.success(f"Added {book['title']} to wishlist!")
                                st.rerun()

                    st.markdown("─" * 20)

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
                # Save order to user's order history
                save_order(st.session_state.username, st.session_state.cart, total)
                st.success("🎉 Order placed successfully! Thank you for shopping at BookVerse! 📦")
                st.balloons()
                st.session_state.cart = []
                st.rerun()
    else:
        st.info("🛒 Your cart is empty. Browse books or ask the AI for recommendations!")

# === IMPROVED CHAT TAB WITH ANIMATION ===
with tab3:
    st.header("💬 BookSnap AI")

    # Add custom CSS to keep input at bottom
    st.markdown("""
        <style>
        .stChatFloatingInputContainer {
            position: sticky !important;
            bottom: 0 !important;
            z-index: 1000;
            background: var(--background-color);
            padding: 1rem 0;
        }

        /* Add padding to chat container to prevent overlap */
        section[data-testid="stChatMessageContainer"] {
            padding-bottom: 100px !important;
        }

        /* Smooth scrolling */
        section[data-testid="stChatMessageContainer"] {
            scroll-behavior: smooth;
        }
        </style>
    """, unsafe_allow_html=True)

    # JavaScript to force scroll to bottom - triggered by state change
    scroll_script = f"""
        <script>
        (function() {{
            const scrollTrigger = {st.session_state.scroll_trigger};

            function forceScrollToBottom() {{
                // Try multiple methods to ensure scrolling works
                const methods = [
                    () => {{
                        const container = window.parent.document.querySelector('[data-testid="stChatMessageContainer"]');
                        if (container) {{
                            container.scrollTop = container.scrollHeight + 1000;
                        }}
                    }},
                    () => {{
                        const endMarker = window.parent.document.getElementById('chat-end-anchor');
                        if (endMarker) {{
                            endMarker.scrollIntoView({{ behavior: 'auto', block: 'end' }});
                        }}
                    }},
                    () => {{
                        const allMessages = window.parent.document.querySelectorAll('[data-testid="stChatMessage"]');
                        if (allMessages.length > 0) {{
                            const lastMessage = allMessages[allMessages.length - 1];
                            lastMessage.scrollIntoView({{ behavior: 'auto', block: 'end' }});
                        }}
                    }}
                ];

                methods.forEach(method => {{
                    try {{ method(); }} catch(e) {{ console.log(e); }}
                }});
            }}

            // Execute immediately and with delays
            forceScrollToBottom();
            setTimeout(forceScrollToBottom, 50);
            setTimeout(forceScrollToBottom, 150);
            setTimeout(forceScrollToBottom, 300);
            setTimeout(forceScrollToBottom, 600);
            setTimeout(forceScrollToBottom, 1000);
            setTimeout(forceScrollToBottom, 2000);
        }})();
        </script>
    """
    st.components.v1.html(scroll_script, height=0)

    # Display existing chat history
    for idx, message in enumerate(st.session_state.chat_history):
        avatar = USER_AVATAR if message["role"] == "user" else ASSISTANT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            content = str(message.get("content", ""))
            st.markdown(content)

            books = message.get("books", [])
            if books:
                display_book_cards_in_chat(books, idx)

    # Add anchor point at the very end for scrolling
    st.markdown('<div id="chat-end-anchor" style="height: 1px;"></div>', unsafe_allow_html=True)

    # Input MUST be defined outside any conditional - always rendered
    prompt = st.chat_input("Ask about books...")

    # Handle the prompt if it exists
    if prompt:
        # Add user message immediately with timestamp
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })

        # Get response from backend
        with st.spinner("🤖 BookSnap AI is thinking..."):
            response_data = chat_with_backend_api(
                prompt,
                st.session_state.chat_history[:-1],  # Exclude the just-added user message
                st.session_state.cart
            )

        # Save assistant response to history with timestamp
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": str(response_data["response"]),
            "books": response_data.get("books", []),
            "timestamp": datetime.now().isoformat()
        })

        # Save chat history to user's data
        if st.session_state.authenticated and st.session_state.username:
            save_chat_history(st.session_state.username, st.session_state.chat_history)

        # Increment scroll trigger to force scroll on next render
        st.session_state.scroll_trigger += 1

        # Force rerun to display new messages and auto-scroll
        st.rerun()

# === WISHLIST TAB ===
with tab4:
    st.header("❤️ My Wishlist")
    
    user_data = get_user_data(st.session_state.username)
    wishlist = user_data.get("wishlist", []) if user_data else []
    
    if wishlist:
        st.metric("📚", len(wishlist), "books in wishlist")
        
        cols = st.columns(4)
        for i, item in enumerate(wishlist):
            with cols[i % 4]:
                cached_img = load_single_image(item.get("image_url"))
                if cached_img:
                    st.image(cached_img, width=180)
                else:
                    st.markdown("📖")
                
                st.markdown(f"**{item['title']}**")
                st.caption(f"✍️ {item.get('author', 'Unknown')}")
                st.caption(f"📂 {item.get('genre', 'Unknown')}")
                try:
                    price_val = float(item.get('price', 0))
                    if price_val > 0:
                        st.markdown(f"💰 **${price_val:.2f}**")
                except (ValueError, TypeError):
                    pass
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🛒 Add to Cart", key=f"wish_cart_{item['id']}", use_container_width=True):
                        add_book_to_cart(item)
                        st.rerun()
                with col2:
                    if st.button("🗑️ Remove", key=f"wish_rm_{item['id']}", use_container_width=True):
                        remove_from_wishlist(st.session_state.username, item['id'])
                        st.success("Removed from wishlist!")
                        st.rerun()
                
                st.markdown("─" * 20)
    else:
        st.info("❤️ Your wishlist is empty. Add books to your wishlist while browsing!")

# === ORDER HISTORY TAB ===
with tab5:
    st.header("📋 Order History")
    
    user_data = get_user_data(st.session_state.username)
    order_history = user_data.get("order_history", []) if user_data else []
    
    if order_history:
        st.metric("📦", len(order_history), "orders")
        
        # Show orders in reverse chronological order (newest first)
        for order in reversed(order_history):
            with st.expander(f"📦 Order #{order['order_id'][:8]} - ${order['total']:.2f} - {order['date'][:10]}", expanded=False):
                st.markdown(f"**Order Date:** {order['date']}")
                st.markdown(f"**Total:** ${order['total']:.2f}")
                st.markdown("**Items:**")
                
                for item in order.get("items", []):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"• {item.get('title', 'Unknown')}")
                    with col2:
                        st.markdown(f"Qty: {item.get('quantity', 1)}")
                    with col3:
                        st.markdown(f"${item.get('price', 0) * item.get('quantity', 1):.2f}")
                
                st.divider()
    else:
        st.info("📋 No orders yet. Start shopping to see your order history here!")

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