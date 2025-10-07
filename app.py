import streamlit as st
import random
from datetime import datetime

st.set_page_config(page_title="Advanced POS System", page_icon="💳", layout="wide")

# ---------- INITIALIZATION ----------
if "products" not in st.session_state:
    # Generate 100 random products
    categories = ["Drinks", "Bakery", "Snacks", "Sandwich", "Dessert", "Other"]
    st.session_state.products = [
        {
            "id": i,
            "name": f"{random.choice(['Classic','Deluxe','Premium','Special','Iced','Hot','Sweet','Choco','Spicy'])} {random.choice(['Latte','Muffin','Donut','Tea','Cookie','Juice','Espresso','Sandwich','Cake'])}",
            "price": round(random.uniform(1.0, 10.0), 2),
            "stock": random.randint(10, 100),
            "category": random.choice(categories),
        }
        for i in range(1, 101)
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "page" not in st.session_state:
    st.session_state.page = "POS"

# ---------- HELPER FUNCTIONS ----------
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
        st.error("❌ Insufficient cash given!")
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

def total_sales():
    return sum(t["total"] for t in st.session_state.transactions)

def total_items_sold():
    return sum(sum(i["qty"] for i in t["items"]) for t in st.session_state.transactions)

def top_selling_items():
    counts = {}
    for t in st.session_state.transactions:
        for item in t["items"]:
            counts[item["name"]] = counts.get(item["name"], 0) + item["qty"]
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

# ---------- SIDEBAR ----------
st.sidebar.title("💳 POS Navigation")
menu = st.sidebar.radio("Go to:", ["POS", "Inventory", "Sales History", "Reports"])

# ---------- PAGE: POS ----------
if menu == "POS":
    st.title("🛍️ Point of Sale")
    col1, col2 = st.columns([2, 1])

    # Left: Product list
    with col1:
        st.subheader("Available Products")
        search = st.text_input("🔎 Search products")
        category_filter = st.selectbox("Filter by category", ["All"] + sorted({p["category"] for p in st.session_state.products}))
        filtered = [
            p for p in st.session_state.products
            if (search.lower() in p["name"].lower()) and (category_filter == "All" or p["category"] == category_filter)
        ]
        for p in filtered:
            cols = st.columns([3, 1, 1, 1])
            cols[0].markdown(f"**{p['name']}**  \n💰 ${p['price']:.2f}")
            cols[1].text(f"Stock: {p['stock']}")
            cols[2].button("Add ➕", key=f"add_{p['id']}", on_click=add_to_cart, args=(p,))
            cols[3].button("❌", key=f"del_{p['id']}", on_click=remove_from_cart, args=(p['id'],))

    # Right: Cart
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

    if "last_receipt" in st.session_state and st.session_state.last_receipt:
        st.write("### 🧾 Last Receipt")
        st.json(st.session_state.last_receipt)

# ---------- PAGE: INVENTORY ----------
elif menu == "Inventory":
    st.title("📦 Inventory Management")
    st.info("Edit product prices or stock below (temporary; resets on reload).")
    for p in st.session_state.products[:100]:
        c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
        c1.write(p["name"])
        p["price"] = c2.number_input("Price", key=f"price_{p['id']}", value=p["price"], step=0.1)
        p["stock"] = c3.number_input("Stock", key=f"stock_{p['id']}", value=p["stock"], step=1)
        c4.text(p["category"])
    st.success("Inventory updated in memory!")

# ---------- PAGE: SALES HISTORY ----------
elif menu == "Sales History":
    st.title("📜 Sales History")
    if not st.session_state.transactions:
        st.info("No transactions yet.")
    else:
        for t in st.session_state.transactions:
            st.markdown(f"**{t['date']}** — ${t['total']:.2f} | {len(t['items'])} items | Change: ${t['change']:.2f}")
            with st.expander("View Details"):
                for i in t["items"]:
                    st.write(f"• {i['name']} — Qty: {i['qty']} — ${i['price'] * i['qty']:.2f}")

# ---------- PAGE: REPORTS ----------
elif menu == "Reports":
    st.title("📊 Sales Reports & Analytics")
    total_tx = len(st.session_state.transactions)
    st.metric("Total Transactions", total_tx)
    st.metric("Total Sales ($)", round(total_sales(), 2))
    st.metric("Total Items Sold", total_items_sold())

    if total_tx > 0:
        st.write("### 🏆 Top Selling Items")
        for name, qty in top_selling_items():
            st.write(f"• {name} — {qty} sold")
    else:
        st.info("No data yet to show reports.")

    if st.button("🧹 Reset All Data"):
        st.session_state.products = []
        st.session_state.cart = []
        st.session_state.transactions = []
        st.success("All in-memory data cleared!")
