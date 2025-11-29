import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
import requests
from datetime import datetime

# === CONFIG ===
st.set_page_config(page_title="BookVerse - Your AI Book Shop", layout="wide")


# Load books
@st.cache_data
def load_books():
    # This creates the DataFrame directly in code
    data = {
        "title": [
            "The Midnight Library", "Dune", "Atomic Habits", "Sapiens",
            "Project Hail Mary", "Klara and the Sun", "The Psychology of Money",
            "Educated", "1984", "The Alchemist"
        ],
        "author": [
            "Matt Haig", "Frank Herbert", "James Clear", "Yuval Noah Harari",
            "Andy Weir", "Kazuo Ishiguro", "Morgan Housel",
            "Tara Westover", "George Orwell", "Paulo Coelho"
        ],
        "genre": [
            "Fiction", "Science Fiction", "Self-Help", "History",
            "Science Fiction", "Literary Fiction", "Finance",
            "Memoir", "Dystopian", "Fiction"
        ],
        "price": [18.99, 22.50, 16.99, 19.99, 20.00, 21.50, 17.99, 18.99, 12.99, 14.99],
        "description": [
            "A dazzling novel about all the choices that go into a life well lived.",
            "Epic science fiction saga on the desert planet Arrakis.",
            "Tiny changes, remarkable results: An easy & proven way to build good habits.",
            "A brief history of humankind – where we came from and how we got here.",
            "A lone astronaut must save the earth in this thrilling sci-fi adventure.",
            "A thrilling book that offers a look at our changing world through the eyes of an AI.",
            "Timeless lessons on wealth, greed, and happiness.",
            "A memoir about a woman who leaves her survivalist family and goes on to earn a PhD.",
            "A dystopian social science fiction novel about totalitarianism and surveillance.",
            "A magical story about dreams, omens, and finding your personal legend."
        ],
        "image_url": [
            "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
            "https://images.unsplash.com/photo-1532012197267-da84d127e765?w=400",
            "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=400",
            "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400",
            "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=400",
            "https://images.unsplash.com/photo-1491841573334-9bde9f1709a0?w=400",
            "https://images.unsplash.com/photo-1544716278-ca5e3f3abd8c?w=400",
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
            "https://images.unsplash.com/photo-1530538987395-7f02970410e0?w=400",
            "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400"
        ]
    }
    return pd.DataFrame(data)

# Load books (this will work immediately)
books = load_books()



# Initialize session state
if "cart" not in st.session_state:
    st.session_state.cart = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# === CHATBOT LOGIC ===
def chatbot_response(user_input):
    user_input = user_input.lower()
    history = st.session_state.chat_history

    # Greetings
    if any(g in user_input for g in ["hi", "hello", "hey", "good morning"]):
        return "Hello! Welcome to BookVerse 📚 How can I help you find your next great read?"

    # Search by title/author
    if "book called" in user_input or "by" in user_input or "find" in user_input:
        for _, book in books.iterrows():
            if book["title"].lower() in user_input or book["author"].lower() in user_input:
                return f"Found it! ✨\n**{book['title']}** by {book['author']}\nPrice: ${book['price']}\nGenre: {book['genre']}\n\n{book['description']}"

    # Genre recommendations
    genre_keywords = {
        "science fiction": "Science Fiction",
        "scifi": "Science Fiction",
        "fiction": "Fiction",
        "self-help": "Self-Help",
        "history": "History",
        "literary": "Literary Fiction",
        "novel": "Fiction"
    }
    for key, genre in genre_keywords.items():
        if key in user_input:
            matches = books[books["genre"] == genre].head(3)
            if not matches.empty:
                recs = "\n".join(
                    [f"• **{row['title']}** by {row['author']} - ${row['price']}" for _, row in matches.iterrows()])
                return f"Here are some great {genre} books:\n{recs}"
            else:
                return f"Sorry, no {genre} books in stock right now."

    # Cart questions
    if "cart" in user_input or "basket" in user_input:
        if st.session_state.cart:
            total = sum(item["price"] * item["qty"] for item in st.session_state.cart)
            items = "\n".join(
                [f"• {item['qty']} × {item['title']} (${item['price']})" for item in st.session_state.cart])
            return f"Your cart has:\n{items}\n\n**Total: ${total:.2f}**"
        else:
            return "Your cart is empty. Want some recommendations?"

    # Default responses
    if "recommend" in user_input or "suggest" in user_input:
        top = books.sample(3)
        recs = "\n".join([f"• **{row['title']}** by {row['author']} - ${row['price']}" for _, row in top.iterrows()])
        return f"Here are some popular picks right now:\n{recs}"

    return "I'm here to help you find books! Try asking: 'Recommend science fiction' or 'Find Dune' or 'What's in my cart?'"


# === MAIN APP ===
col1, col2 = st.columns([3, 1])

with col1:
    st.title("📚 BookVerse - Your AI-Powered Book Shop")
    st.caption("Discover your next favorite book with the help of our smart assistant")

with col2:
    st.metric("Books in Stock", len(books))
    st.metric("In Your Cart", len(st.session_state.cart))

# Tabs
tab1, tab2, tab3 = st.tabs(["Browse Books", "Shopping Cart", "Chat with Assistant"])

# === TAB 1: Browse Books ===
with tab1:
    st.subheader("All Books")
    cols = st.columns(4)
    for idx, book in books.iterrows():
        with cols[idx % 4]:
            try:
                response = requests.get(book["image_url"])
                img = Image.open(BytesIO(response.content))
            except:
                img = Image.new('RGB', (200, 300), color=(200, 200, 200))
                from PIL import ImageDraw

                d = ImageDraw.Draw(img)
                d.text((10, 140), "No Image", fill=(0, 0, 0))

            st.image(img, use_container_width=True)
            st.subheader(book["title"], anchor=False)
            st.caption(f"by {book['author']}")
            st.write(f"**${book['price']}** • {book['genre']}")

            if st.button(f"Add to Cart", key=f"add_{idx}"):
                if book["title"] not in [item["title"] for item in st.session_state.cart]:
                    st.session_state.cart.append({
                        "title": book["title"],
                        "author": book["author"],
                        "price": book["price"],
                        "qty": 1
                    })
                else:
                    for item in st.session_state.cart:
                        if item["title"] == book["title"]:
                            item["qty"] += 1
                st.success(f"Added {book['title']} to cart!")
                st.rerun()

# === TAB 2: Cart ===
with tab2:
    st.subheader("🛒 Your Shopping Cart")
    if st.session_state.cart:
        total = 0
        for i, item in enumerate(st.session_state.cart):
            colA, colB, colC, colD = st.columns([3, 1, 1, 1])
            with colA:
                st.write(f"**{item['title']}** by {item['author']}")
            with colB:
                st.write(f"${item['price']}")
            with colC:
                qty = st.number_input("Qty", min_value=1, value=item["qty"], key=f"qty_{i}")
                item["qty"] = qty
            with colD:
                if st.button("Remove", key=f"rem_{i}"):
                    st.session_state.cart.pop(i)
                    st.rerun()
            total += item["price"] * item["qty"]

        st.divider()
        st.write(f"**Total: ${total:.2f}**")
        if st.button("Proceed to Checkout 💳", type="primary", use_container_width=True):
            st.success("Checkout successful! (This is a demo)")
            st.balloons()
    else:
        st.info("Your cart is empty. Start shopping!")

# === TAB 3: Chat Assistant ===
with tab3:
    st.subheader("💬 Ask Me Anything About Books!")
    st.write("I can help you find books, recommend genres, check your cart, and more!")

    # Display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        else:
            st.chat_message("assistant").write(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your message... (e.g. 'Recommend sci-fi books' or 'Find Atomic Habits')"):
        st.session_state.chat_history.append({"role": "user", "content": prompt, "time": datetime.now()})
        st.chat_message("user").write(prompt)

        response = chatbot_response(prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": response, "time": datetime.now()})
        st.chat_message("assistant").write(response)

        st.rerun()

# Footer
st.markdown("---")
st.caption("BookVerse • Built with ❤️ using Streamlit • Demo Book Shop with AI Assistant")