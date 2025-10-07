import streamlit as st
import random
from datetime import datetime

st.set_page_config(page_title="Grocery POS System", page_icon="🛒", layout="wide")

# -------------------- INITIAL SETUP --------------------
if "products" not in st.session_state:
    product_names = [
        "Apple", "Banana", "Orange", "Mango", "Pineapple", "Avocado", "Tomato", "Potato", "Onion",
        "Cabbage", "Carrot", "Spinach", "Broccoli", "Milk", "Bread", "Eggs", "Cheese", "Butter",
        "Cereal", "Yogurt", "Rice", "Flour", "Sugar", "Salt", "Cooking Oil", "Tea", "Coffee",
        "Juice", "Soda", "Water", "Biscuits", "Chips", "Chocolate", "Ice Cream", "Beef", "Chicken",
        "Fish", "Pork", "Sausage", "Soap", "Toothpaste", "Shampoo", "Tissue", "Detergent",
        "Toothbrush", "Candy", "Peanut Butter", "Jam", "Honey", "Ketchup", "Mustard", "Mayonnaise",
        "Vinegar", "Spaghetti", "Macaroni", "Beans", "Lentils", "Peas", "Corn", "Coconut Oil",
        "Groundnuts", "Baking Powder", "Vanilla", "Yeast", "Oats", "Pasta", "Butter Milk", "Whipping Cream",
        "Cocoa Powder", "Tomato Sauce", "Frozen Pizza", "Popcorn", "Ice Cubes", "Margarine", "Apple Juice",
        "Orange Juice", "Energy Drink", "Mineral Water", "Laundry Soap", "Bleach", "Cleaning Spray",
        "Napkins", "Paper Towels", "Toilet Paper", "Mouthwash", "Body Lotion", "Shower Gel", "Perfume",
        "Shaving Cream", "Toilet Cleaner", "Hand Wash", "Deodorant", "Lip Balm", "Pet Food", "Cat Litter",
        "Candle", "Battery", "Matchbox", "Light Bulb"
    ]

    image_sources = [
        "https://source.unsplash.com/featured/?grocery,{}",
        "https://source.unsplash.com/featured/?food,{}",
        "https://source.unsplash.com/featured/?supermarket,{}",
        "https://source.unsplash.com/featured/?fruit,{}",
        "https://source.unsplash.com/featured/?vegetable,{}"
    ]

    categories = ["Fruits", "Vegetables", "Dairy", "Snacks", "Drinks", "Bakery", "Cleaning", "Toiletries", "Other"]

    st.session_state.products = [
        {
            "id": i,
            "name": name,
            "price": round(random.uniform(0.5, 20.0), 2),
            "stock": random.randint(10, 100),
            "category": random.choice(categories),
            "image": random.choice(image_sources).format(name)
        }
        for i, name in enumerate(random.sample(product_names, 100), 1)
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []

if "transactions" not in st.session_state:
    st.session_state.transactions = []

# -------------------- HELPER FUNCTIONS --------------------
def add_to_cart(product):
    for item in st.session_state.cart:
        if item["id"] == product["id"]:
            item["qty"] += 1
            return
    st.session_state.cart.append({**product, "qty": 1})

def remove_from_cart(pid):
    st.session_state.cart = [i for i in st.session_state.cart if i["id"] != pid]

def clear_cart():
    st.session_state.cart = []

def subtotal():
    return sum(i["price"] * i["qty"] for i in st.session_state.cart)

def checkout(discount, cash):
    sub = subtotal()
    total = sub * (1 - discount / 100)
    if cash < total:
        st.error("Insufficient cash!")
        return
    change = round(cash - total, 2)
    transaction = {
        "id": len(st.session_state.transactions) + 1,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": st.session_state.cart.copy(),
        "subtotal": round(sub, 2),
        "discount": discount,
        "total": round(total, 2),
        "cash": round(cash, 2),
        "change": change
    }
    st.session_state.transactions.insert(0, transaction)
    clear_cart()
    st.success(f"Transaction successful! Change: ${change}")

def total_sales():
    return sum(t["total"] for t in st.session_state.transactions)

# -------------------- SIDEBAR --------------------
st.sidebar.title("🛒 Grocery POS")
menu = st.sidebar.radio("Navigate", ["POS", "Inventory", "Sales History", "Reports"])

# -------------------- POS PAGE --------------------
if menu == "POS":
    st.title("🛍️ Grocery Point of Sale")
    col1, col2 = st.columns([2, 1])

    with col1:
        search = st.text_input("🔍 Search Product")
        category_filter = st.selectbox("Filter by Category", ["All"] + sorted({p["category"] for p in st.session_state.products}))
        filtered = [
            p for p in st.session_state.products
            if search.lower() in p["name"].lower() and (category_filter == "All" or p["category"] == category_filter)
        ]

        cols = st.columns(3)
        for idx, p in enumerate(filtered):
            with cols[idx % 3]:
                st.image(p["image"], use_container_width=True, caption=f"{p['name']}")
                st.markdown(f"**${p['price']:.2f}** — Stock: {p['stock']}")
                st.button("Add to Cart", key=f"add_{p['id']}", on_click=add_to_cart, args=(p,))

    with col2:
        st.subheader("🛒 Cart")
        if not st.session_state.cart:
            st.info("Cart is empty.")
        else:
            for item in st.session_state.cart:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"{item['name']}")
                item["qty"] = c2.number_input("Qty", min_value=1, value=item["qty"], key=f"qty_{item['id']}")
                c3.write(f"${item['price'] * item['qty']:.2f}")
                if st.button("❌ Remove", key=f"rem_{item['id']}"):
                    remove_from_cart(item["id"])

            st.divider()
            sub = subtotal()
            discount = st.number_input("Discount (%)", 0, 100, 0)
            total = sub * (1 - discount / 100)
            st.write(f"**Subtotal:** ${sub:.2f}")
            st.write(f"**Total:** ${total:.2f}")
            cash = st.number_input("Cash Given", 0.0, 9999.0, 0.0)
            if st.button("✅ Checkout"):
                checkout(discount, cash)

# -------------------- INVENTORY --------------------
elif menu == "Inventory":
    st.title("📦 Inventory")
    st.info("Edit product stock or price (changes are temporary).")
    for p in st.session_state.products[:50]:
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        c1.write(p["name"])
        p["price"] = c2.number_input("Price", value=p["price"], key=f"price_{p['id']}")
        p["stock"] = c3.number_input("Stock", value=p["stock"], key=f"stock_{p['id']}")
        c4.text(p["category"])

# -------------------- SALES HISTORY --------------------
elif menu == "Sales History":
    st.title("📜 Transaction History")
    if not st.session_state.transactions:
        st.info("No transactions yet.")
    else:
        for t in st.session_state.transactions:
            with st.expander(f"🧾 {t['date']} — Total: ${t['total']:.2f}"):
                for item in t["items"]:
                    st.write(f"{item['name']} x{item['qty']} — ${item['price'] * item['qty']:.2f}")
                st.markdown(f"**Subtotal:** ${t['subtotal']:.2f} | **Discount:** {t['discount']}% | **Change:** ${t['change']:.2f}")

# -------------------- REPORTS --------------------
elif menu == "Reports":
    st.title("📊 Sales Reports")
    st.metric("Total Transactions", len(st.session_state.transactions))
    st.metric("Total Sales ($)", round(total_sales(), 2))
    if st.session_state.transactions:
        top_items = {}
        for t in st.session_state.transactions:
            for i in t["items"]:
                top_items[i["name"]] = top_items.get(i["name"], 0) + i["qty"]
        sorted_items = sorted(top_items.items(), key=lambda x: x[1], reverse=True)[:5]
        st.subheader("🏆 Top Selling Items")
        for name, qty in sorted_items:
            st.write(f"{name} — {qty} sold")
    else:
        st.info("No sales data yet.")
