import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Simple POS System", page_icon="💳", layout="wide")

# --- Initialize session state ---
if "products" not in st.session_state:
    st.session_state.products = [
        {"id": 1, "name": "Espresso", "price": 2.50, "stock": 50},
        {"id": 2, "name": "Cappuccino", "price": 3.50, "stock": 40},
        {"id": 3, "name": "Latte", "price": 3.00, "stock": 45},
        {"id": 4, "name": "Blueberry Muffin", "price": 2.00, "stock": 30},
        {"id": 5, "name": "Bagel", "price": 1.75, "stock": 25},
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "transactions" not in st.session_state:
    st.session_state.transactions = []

# --- Helper functions ---
def add_to_cart(prod):
    for item in st.session_state.cart:
        if item["id"] == prod["id"]:
            item["qty"] += 1
            return
    st.session_state.cart.append({**prod, "qty": 1})

def remove_from_cart(pid):
    st.session_state.cart = [i for i in st.session_state.cart if i["id"] != pid]

def clear_cart():
    st.session_state.cart = []

def cart_subtotal():
    return sum(i["price"] * i["qty"] for i in st.session_state.cart)

def process_checkout(discount, cash):
    subtotal = cart_subtotal()
    total = subtotal * (1 - discount / 100)
    change = cash - total
    if cash < total:
        st.error("Insufficient cash given!")
        return None
    trans = {
        "id": len(st.session_state.transactions) + 1,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": st.session_state.cart.copy(),
        "subtotal": round(subtotal, 2),
        "discount": discount,
        "total": round(total, 2),
        "cash": round(cash, 2),
        "change": round(change, 2),
    }
    st.session_state.transactions.insert(0, trans)
    clear_cart()
    return trans

# --- Layout ---
st.title("💳 Simple Point of Sale (POS) System")

col1, col2 = st.columns([2, 1])

# --- Left: Product Catalog ---
with col1:
    st.subheader("🛍️ Product Catalog")
    search = st.text_input("Search products", "")
    for p in st.session_state.products:
        if search.lower() not in p["name"].lower():
            continue
        cols = st.columns([3, 1, 1, 1])
        cols[0].markdown(f"**{p['name']}**  \n${p['price']:.2f}")
        cols[1].text(f"Stock: {p['stock']}")
        cols[2].button("Add", key=f"add_{p['id']}", on_click=add_to_cart, args=(p,))
        cols[3].button("🗑️", key=f"del_{p['id']}", on_click=remove_from_cart, args=(p['id'],))

# --- Right: Cart / Checkout ---
with col2:
    st.subheader("🛒 Cart")
    if not st.session_state.cart:
        st.info("Cart is empty.")
    else:
        for item in st.session_state.cart:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"{item['name']} (${item['price']:.2f})")
            qty = c2.number_input("Qty", key=f"qty_{item['id']}", min_value=1, value=item["qty"])
            item["qty"] = qty
            c3.write(f"${item['price'] * qty:.2f}")
        st.write("---")
        subtotal = cart_subtotal()
        discount = st.number_input("Discount (%)", 0, 100, 0)
        total = subtotal * (1 - discount / 100)
        st.write(f"**Subtotal:** ${subtotal:.2f}")
        st.write(f"**Total after discount:** ${total:.2f}")
        cash = st.number_input("Cash Given ($)", 0.0, 99999.0, 0.0)
        change = cash - total
        st.write(f"**Change:** ${change:.2f}")
        if st.button("✅ Checkout"):
            receipt = process_checkout(discount, cash)
            if receipt:
                st.success("Transaction completed!")
                st.session_state.last_receipt = receipt

# --- Receipt Display ---
if "last_receipt" in st.session_state and st.session_state.last_receipt:
    st.write("### 🧾 Last Receipt")
    r = st.session_state.last_receipt
    st.json(r)

# --- Transactions History ---
st.write("---")
st.subheader("📜 Transaction History")
if st.session_state.transactions:
    for t in st.session_state.transactions[:10]:
        st.write(f"**{t['date']}** — ${t['total']:.2f} | {len(t['items'])} items | Change: ${t['change']:.2f}")
else:
    st.info("No transactions yet.")
