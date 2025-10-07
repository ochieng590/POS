import streamlit as st
import random
import csv
import io
from datetime import datetime

st.set_page_config(page_title="Advanced POS (stable)", page_icon="💳", layout="wide")

# -----------------------
# Session state init
# -----------------------
if "products" not in st.session_state:
    categories = ["Drinks", "Bakery", "Snacks", "Sandwich", "Dessert", "Other"]
    st.session_state.products = [
        {
            "id": i,
            "name": f"{random.choice(['Classic','Deluxe','Premium','Special','Iced','Hot','Sweet','Choco','Spicy'])} "
                    f"{random.choice(['Latte','Muffin','Donut','Tea','Cookie','Juice','Espresso','Sandwich','Cake'])}",
            "price": round(float(random.uniform(1.0, 10.0)), 2),
            "stock": int(random.randint(10, 100)),
            "category": random.choice(categories),
        }
        for i in range(1, 101)
    ]

if "cart" not in st.session_state:
    st.session_state.cart = []  # each item: {id, name, price, qty}

if "transactions" not in st.session_state:
    st.session_state.transactions = []

if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None

# -----------------------
# Helper utilities
# -----------------------
def get_product(pid):
    return next((p for p in st.session_state.products if p["id"] == pid), None)

def add_to_cart(pid, qty=1):
    p = get_product(pid)
    if p is None:
        st.error("Product not found.")
        return
    # find existing cart item
    existing = next((c for c in st.session_state.cart if c["id"] == pid), None)
    desired_qty = (existing["qty"] + qty) if existing else qty
    if desired_qty > p["stock"]:
        st.warning(f"Cannot add {qty} — only {p['stock'] - (existing['qty'] if existing else 0)} left in stock.")
        return
    if existing:
        existing["qty"] = desired_qty
    else:
        st.session_state.cart.append({"id": p["id"], "name": p["name"], "price": float(p["price"]), "qty": int(qty)})

def remove_from_cart(pid):
    st.session_state.cart = [c for c in st.session_state.cart if c["id"] != pid]

def update_cart_qty(pid, qty):
    for item in st.session_state.cart:
        if item["id"] == pid:
            qty = int(max(1, qty))
            product = get_product(pid)
            if product and qty > product["stock"]:
                item["qty"] = product["stock"]
                st.warning(f"Limited to stock: {product['stock']}")
            else:
                item["qty"] = qty
            break

def cart_subtotal():
    return round(sum(float(i["price"]) * int(i["qty"]) for i in st.session_state.cart), 2)

def process_checkout(discount_percent: float, cash_given: float):
    try:
        if not st.session_state.cart:
            st.error("Cart is empty.")
            return None
        subtotal = cart_subtotal()
        discount_percent = float(discount_percent)
        total = round(subtotal * (1 - discount_percent / 100), 2)
        cash_given = float(cash_given)
        if cash_given < total:
            st.error("Insufficient cash.")
            return None
        # check stock again before finalizing
        for item in st.session_state.cart:
            prod = get_product(item["id"])
            if prod is None:
                st.error(f"Product {item['name']} not found in inventory.")
                return None
            if item["qty"] > prod["stock"]:
                st.error(f"Not enough stock for {item['name']}. Available: {prod['stock']}")
                return None
        # deduct stock
        for item in st.session_state.cart:
            prod = get_product(item["id"])
            prod["stock"] = max(0, prod["stock"] - item["qty"])
        # create transaction
        tx = {
            "id": len(st.session_state.transactions) + 1,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": [dict(i) for i in st.session_state.cart],
            "subtotal": subtotal,
            "discount": discount_percent,
            "total": total,
            "cash": round(cash_given, 2),
            "change": round(cash_given - total, 2),
        }
        st.session_state.transactions.insert(0, tx)
        st.session_state.last_receipt = tx
        st.session_state.cart = []
        st.success("Transaction completed.")
        return tx
    except Exception as e:
        st.exception(e)
        return None

def transactions_to_csv_bytes():
    if not st.session_state.transactions:
        return None
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id","date","subtotal","discount","total","cash","change","items"])
    for t in st.session_state.transactions:
        items_str = "; ".join([f'{it["name"]} x{it["qty"]} (${it["price"]})' for it in t["items"]])
        writer.writerow([t["id"], t["date"], t["subtotal"], t["discount"], t["total"], t["cash"], t["change"], items_str])
    return output.getvalue().encode("utf-8")

# -----------------------
# Sidebar navigation
# -----------------------
st.sidebar.title("💳 POS Navigation")
menu = st.sidebar.radio("Go to:", ["POS", "Inventory", "Sales History", "Reports", "Admin"])

# Quick actions
st.sidebar.markdown("---")
if st.sidebar.button("🧾 Download transactions (CSV)"):
    csv_bytes = transactions_to_csv_bytes()
    if csv_bytes:
        st.sidebar.download_button("Download CSV", data=csv_bytes, file_name="transactions.csv", mime="text/csv")
    else:
        st.sidebar.info("No transactions to export.")

# -----------------------
# POS Page
# -----------------------
if menu == "POS":
    st.title("🛍️ Point of Sale")
    col_products, col_cart = st.columns([2, 1])

    with col_products:
        st.subheader("Products")
        search = st.text_input("Search product", key="search_products")
        category_list = ["All"] + sorted({p["category"] for p in st.session_state.products})
        category_filter = st.selectbox("Category", category_list, key="category_filter")
        filtered = [
            p for p in st.session_state.products
            if (search.lower() in p["name"].lower()) and (category_filter == "All" or p["category"] == category_filter)
        ]
        # show products as compact rows
        for p in filtered:
            cols = st.columns([4, 1, 1, 1])
            cols[0].markdown(f"**{p['name']}**  \n_{p['category']}_  \n${p['price']:.2f}")
            cols[1].text(f"Stock: {p['stock']}")
            # Add with qty 1
            cols[2].button("Add ➕", key=f"add_{p['id']}_btn", on_click=add_to_cart, args=(p["id"], 1))
            # small "add custom qty" expander to avoid too many widgets
            with cols[3]:
                qty = st.number_input("", min_value=1, max_value=1000, value=1, key=f"quickqty_{p['id']}")
                st.button("Add x", key=f"addqty_{p['id']}_btn", on_click=add_to_cart, args=(p["id"], qty))

    with col_cart:
        st.subheader("Cart")
        if not st.session_state.cart:
            st.info("Cart is empty.")
        else:
            for item in st.session_state.cart:
                p = get_product(item["id"])
                max_stock = p["stock"] if p else item["qty"]
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{item['name']}**  \n${item['price']:.2f}")
                qty = c2.number_input("Qty", min_value=1, max_value=max_stock if max_stock > 0 else 1,
                                      value=int(item["qty"]), key=f"qty_cart_{item['id']}")
                if qty != item["qty"]:
                    update_cart_qty(item["id"], qty)
                c3.markdown(f"${item['price'] * item['qty']:.2f}")
                # remove button
                if st.button("Remove", key=f"rm_{item['id']}_btn"):
                    remove_from_cart(item["id"])
                    st.experimental_rerun()

            st.write("---")
            subtotal = cart_subtotal()
            discount = st.number_input("Discount (%)", min_value=0.0, max_value=100.0, value=0.0, key="discount_pct")
            total = round(subtotal * (1 - float(discount) / 100), 2)
            st.markdown(f"**Subtotal:** ${subtotal:.2f}")
            st.markdown(f"**Total:** ${total:.2f}")
            cash = st.number_input("Cash Given ($)", min_value=0.0, value=0.0, key="cash_given")
            st.markdown(f"**Change:** ${round(float(cash) - total, 2) if cash else 0.0:.2f}")

            if st.button("✅ Checkout", key="checkout_btn"):
                receipt = process_checkout(discount, cash)
                if receipt:
                    st.success("Sale recorded.")
                    st.experimental_rerun()

    # last receipt display
    if st.session_state.last_receipt:
        st.write("### 🧾 Last receipt")
        st.json(st.session_state.last_receipt)

# -----------------------
# Inventory Page
# -----------------------
elif menu == "Inventory":
    st.title("📦 Inventory")
    st.info("Edit product price/stock. Changes are kept in-memory (app restart will reset).")

    # add-new-product quick form
    with st.expander("➕ Add new product"):
        new_name = st.text_input("Name", key="new_name")
        new_category = st.text_input("Category", key="new_cat")
        new_price = st.number_input("Price", min_value=0.0, value=1.0, key="new_price")
        new_stock = st.number_input("Stock", min_value=0, value=10, key="new_stock")
        if st.button("Add product"):
            new_id = max([p["id"] for p in st.session_state.products] + [0]) + 1
            st.session_state.products.append({
                "id": new_id,
                "name": new_name or f"Product {new_id}",
                "price": float(new_price),
                "stock": int(new_stock),
                "category": new_category or "Other"
            })
            st.success("Product added.")

    # show/edit existing products (paged)
    page_size = 25
    total = len(st.session_state.products)
    pages = (total + page_size - 1) // page_size
    page_idx = st.number_input("Page", min_value=1, max_value=max(1, pages), value=1, step=1, key="inv_page")
    start = (page_idx - 1) * page_size
    end = start + page_size

    for p in st.session_state.products[start:end]:
        cols = st.columns([4, 1, 1, 1])
        cols[0].text(p["name"])
        price_val = cols[1].number_input("Price", value=float(p["price"]), key=f"inv_price_{p['id']}", step=0.1)
        stock_val = cols[2].number_input("Stock", value=int(p["stock"]), key=f"inv_stock_{p['id']}", step=1)
        cols[3].text(p["category"])
        # store edits
        p["price"] = float(price_val)
        p["stock"] = int(stock_val)

# -----------------------
# Sales History Page
# -----------------------
elif menu == "Sales History":
    st.title("📜 Sales History")
    if not st.session_state.transactions:
        st.info("No transactions yet.")
    else:
        for t in st.session_state.transactions:
            with st.expander(f"Tx {t['id']} — {t['date']} — ${t['total']:.2f}"):
                st.write(f"Subtotal: ${t['subtotal']:.2f}  | Discount: {t['discount']}%  | Cash: ${t['cash']:.2f}  | Change: ${t['change']:.2f}")
                for it in t["items"]:
                    st.write(f"- {it['name']} x{it['qty']} @ ${it['price']:.2f}")

        csv_bytes = transactions_to_csv_bytes()
        if csv_bytes:
            st.download_button("Download transactions CSV", data=csv_bytes, file_name="transactions.csv", mime="text/csv")

# -----------------------
# Reports Page
# -----------------------
elif menu == "Reports":
    st.title("📊 Reports")
    total_sales = round(sum(t["total"] for t in st.session_state.transactions), 2)
    total_tx = len(st.session_state.transactions)
    total_items = sum(sum(it["qty"] for it in t["items"]) for t in st.session_state.transactions)
    st.metric("Total Sales ($)", total_sales)
    st.metric("Transactions", total_tx)
    st.metric("Items sold", total_items)

    # Top sellers
    counts = {}
    for t in st.session_state.transactions:
        for it in t["items"]:
            counts[it["name"]] = counts.get(it["name"], 0) + it["qty"]
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    if top:
        st.write("Top selling items:")
        for name, qty in top:
            st.write(f"- {name}: {qty}")

# -----------------------
# Admin / maintenance
# -----------------------
elif menu == "Admin":
    st.title("⚙️ Admin")
    if st.button("🧹 Clear all data (products, cart, transactions)"):
        st.session_state.products = []
        st.session_state.cart = []
        st.session_state.transactions = []
        st.session_state.last_receipt = None
        st.success("Cleared in-memory data. Reload app to regenerate default products.")

    st.write("Tip: For production/persistence, switch to a small DB (SQLite) or connect a remote DB.")
