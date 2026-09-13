import streamlit as st
from datetime import datetime
import mysql.connector

st.set_page_config(
    page_title="E-Commerce App",
    page_icon="🛒",
    layout="wide"
)

# =========================
# MySQL Connection
# =========================

db = mysql.connector.connect(
    host=st.secrets["mysql"]["host"],
    user=st.secrets["mysql"]["user"],
    password=st.secrets["mysql"]["password"],
    database=st.secrets["mysql"]["database"]
)

cursor = db.cursor()

st.success("MySQL Connected Successfully!")

st.title("🛒 E-Commerce App")
st.write("Welcome to our E-Commerce Store")


# =========================
# Session State
# =========================

if "cart" not in st.session_state:
    st.session_state["cart"] = []


# =========================
# Search and Category
# =========================

search = st.text_input("🔍 Search Product")

category = st.selectbox(
    "📂 Select Category",
    ["All", "Electronics", "Accessories"]
)


# =========================
# Get Products From MySQL
# =========================

cursor.execute("""
    SELECT id, name, price, category, emoji
    FROM products
    ORDER BY id
""")

product_data = cursor.fetchall()

products = []

for product in product_data:

    products.append({
        "id": product[0],
        "name": product[1],
        "price": float(product[2]),
        "category": product[3],
        "emoji": product[4]
    })


# =========================
# Filter Products
# =========================

filtered_products = []

for product in products:

    if search.lower() not in product["name"].lower():
        continue

    if category != "All" and product["category"] != category:
        continue

    filtered_products.append(product)


# =========================
# Display Products
# =========================

st.subheader("🛍️ Products")

if len(filtered_products) == 0:

    st.warning("No products found.")

else:

    columns = st.columns(len(filtered_products))

    for column, product in zip(columns, filtered_products):

        with column:

            st.write(
                f"### {product['emoji']} {product['name']}"
            )

            st.write(
                f"₹{product['price']:,.0f}"
            )

            if st.button(
                "Add to Cart",
                key=f"add_{product['id']}"
            ):

                found = False

                for item in st.session_state["cart"]:

                    if item["id"] == product["id"]:

                        item["quantity"] += 1
                        found = True
                        break

                if not found:

                    new_product = product.copy()
                    new_product["quantity"] = 1

                    st.session_state["cart"].append(
                        new_product
                    )

                st.success(
                    f"{product['name']} added to cart!"
                )


# =========================
# Cart
# =========================

st.divider()

st.subheader("🛒 Your Cart")

total = 0
total_items = 0

if len(st.session_state["cart"]) == 0:

    st.info("Your cart is empty.")

else:

    for item in st.session_state["cart"]:

        st.write(
            f"### {item['emoji']} {item['name']}"
        )

        st.write(
            f"Price: ₹{item['price']:,.0f}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            if st.button(
                "➖",
                key=f"minus_{item['id']}"
            ):

                item["quantity"] -= 1

                if item["quantity"] <= 0:
                    st.session_state["cart"].remove(item)

                st.rerun()

        with col2:

            st.write(
                f"Quantity: **{item['quantity']}**"
            )

        with col3:

            if st.button(
                "➕",
                key=f"plus_{item['id']}"
            ):

                item["quantity"] += 1
                st.rerun()

        if st.button(
            "🗑️ Remove",
            key=f"remove_{item['id']}"
        ):

            st.session_state["cart"].remove(item)
            st.rerun()

        item_total = item["price"] * item["quantity"]

        st.write(
            f"Item Total: **₹{item_total:,.0f}**"
        )

        total += item_total
        total_items += item["quantity"]

        st.divider()

    st.write(
        f"### 📦 Total Items: {total_items}"
    )

    st.write(
        f"## 💰 Grand Total: ₹{total:,.0f}"
    )


# =========================
# Checkout
# =========================

st.divider()

st.subheader("🧾 Checkout")

customer_name = st.text_input("👤 Customer Name")

phone = st.text_input("📱 Phone Number")

address = st.text_area("📍 Delivery Address")


if st.button("✅ Place Order"):

    if customer_name == "":
        st.warning("Please enter your name.")

    elif phone == "":
        st.warning("Please enter your phone number.")

    elif address == "":
        st.warning("Please enter your delivery address.")

    elif len(st.session_state["cart"]) == 0:
        st.warning("Your cart is empty.")

    else:

        # Generate Order ID
        order_id = (
            "ORD-"
            + datetime.now().strftime("%Y%m%d%H%M%S")
        )

        # =========================
        # Save Order
        # =========================

        sql = """
        INSERT INTO orders
        (order_id, customer_name, phone, address, total, items, order_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            order_id,
            customer_name,
            phone,
            address,
            total,
            total_items,
            datetime.now()
        )

        cursor.execute(sql, values)
        db.commit()


        # =========================
        # Save Order Items
        # =========================

        for item in st.session_state["cart"]:

            item_total = item["price"] * item["quantity"]

            cursor.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    product_name,
                    category,
                    price,
                    quantity,
                    item_total
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    item["id"],
                    item["name"],
                    item["category"],
                    item["price"],
                    item["quantity"],
                    item_total
                )
            )

        db.commit()


        # =========================
        # Success Message
        # =========================

        st.success("🎉 Order placed successfully!")

        st.write(
            f"### 🆔 Order ID: {order_id}"
        )

        st.write(
            f"👤 Customer: {customer_name}"
        )

        st.write(
            f"📱 Phone: {phone}"
        )

        st.write(
            f"📍 Address: {address}"
        )

        st.write(
            f"📦 Items: {total_items}"
        )

        st.write(
            f"💰 Order Total: ₹{total:,.0f}"
        )

        st.session_state["cart"] = []


# =========================
# Order History
# =========================

st.divider()

st.subheader("📋 Order History")

cursor.execute("""
    SELECT
        order_id,
        customer_name,
        phone,
        address,
        total,
        items,
        order_date
    FROM orders
    ORDER BY order_date DESC
""")

orders = cursor.fetchall()

if len(orders) == 0:

    st.info("No orders placed yet.")

else:

    for order in orders:

        order_id = order[0]
        customer_name = order[1]
        phone = order[2]
        address = order[3]
        order_total = order[4]
        items = order[5]
        order_date = order[6]

        with st.expander(
            f"🆔 {order_id} - ₹{float(order_total):,.0f}"
        ):

            st.write(
                f"👤 Customer: {customer_name}"
            )

            st.write(
                f"📱 Phone: {phone}"
            )

            st.write(
                f"📍 Address: {address}"
            )

            st.write(
                f"📦 Items: {items}"
            )

            st.write(
                f"💰 Total: ₹{float(order_total):,.0f}"
            )

            st.write(
                f"🕐 Date: {order_date}"
            )


# =========================
# Admin Panel
# =========================

st.divider()

st.subheader("🔐 Admin Panel")


# =========================
# Admin Dashboard
# =========================

st.write("### 📊 Admin Dashboard")

cursor.execute(
    "SELECT COUNT(*) FROM products"
)

total_products = cursor.fetchone()[0]

cursor.execute(
    "SELECT COUNT(*) FROM orders"
)

total_orders = cursor.fetchone()[0]

cursor.execute(
    "SELECT COALESCE(SUM(total), 0) FROM orders"
)

total_revenue = cursor.fetchone()[0]

cursor.execute(
    "SELECT COALESCE(SUM(items), 0) FROM orders"
)

items_sold = cursor.fetchone()[0]


# =========================
# KPI Cards
# =========================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "📦 Total Products",
        total_products
    )

with col2:

    st.metric(
        "🧾 Total Orders",
        total_orders
    )

with col3:

    st.metric(
        "💰 Total Revenue",
        f"₹{float(total_revenue):,.0f}"
    )

with col4:

    st.metric(
        "🛒 Items Sold",
        items_sold
    )


# =========================
# Sales Revenue Chart
# =========================

st.write("### 📈 Sales Revenue")

cursor.execute("""
    SELECT
        DATE(order_date) AS order_day,
        SUM(total) AS revenue
    FROM orders
    GROUP BY DATE(order_date)
    ORDER BY order_day
""")

sales_data = cursor.fetchall()

if len(sales_data) > 0:

    chart_data = {
        "Date": [],
        "Revenue": []
    }

    for row in sales_data:

        chart_data["Date"].append(row[0])
        chart_data["Revenue"].append(float(row[1]))

    st.line_chart(
        chart_data,
        x="Date",
        y="Revenue"
    )
# =========================
# Category-wise Sales
# =========================

st.write("### 📊 Category-wise Sales")

cursor.execute("""
    SELECT
        category,
        SUM(item_total) AS revenue
    FROM order_items
    GROUP BY category
    ORDER BY revenue DESC
""")

category_sales = cursor.fetchall()

if len(category_sales) > 0:

    category_chart = {
        "Category": [],
        "Revenue": []
    }

    for row in category_sales:

        category_chart["Category"].append(row[0])
        category_chart["Revenue"].append(float(row[1]))

    st.bar_chart(
        category_chart,
        x="Category",
        y="Revenue"
    )

else:

    st.info("No category sales data available yet.")


# =========================
# Best Selling Products
# =========================

st.write("### 🏆 Best Selling Products")

cursor.execute("""
    SELECT
        product_name,
        SUM(quantity) AS units_sold,
        SUM(item_total) AS revenue
    FROM order_items
    GROUP BY product_name
    ORDER BY units_sold DESC
""")

best_products = cursor.fetchall()

if len(best_products) > 0:

    product_chart = {
        "Product": [],
        "Units Sold": []
    }

    for row in best_products:

        product_chart["Product"].append(row[0])
        product_chart["Units Sold"].append(int(row[1]))

    st.bar_chart(
        product_chart,
        x="Product",
        y="Units Sold"
    )

    st.write("### 📋 Product Sales Details")

    for row in best_products:

        product_name = row[0]
        units_sold = row[1]
        revenue = row[2]

        st.write(
            f"🏷️ **{product_name}** | "
            f"📦 Units Sold: **{units_sold}** | "
            f"💰 Revenue: **₹{float(revenue):,.0f}**"
        )

else:

    st.info("No product sales data available yet.")

# =========================
# Manage Products
# =========================

with st.expander("⚙️ Manage Products"):

    # =========================
    # Add Product
    # =========================

    st.write("### ➕ Add New Product")

    product_name = st.text_input(
        "Product Name",
        key="add_product_name"
    )

    product_price = st.number_input(
        "Product Price",
        min_value=0.0,
        step=100.0,
        key="add_product_price"
    )

    product_category = st.selectbox(
        "Product Category",
        ["Electronics", "Accessories"],
        key="add_product_category"
    )

    product_emoji = st.text_input(
        "Product Emoji",
        value="📦",
        key="add_product_emoji"
    )

    if st.button(
        "➕ Add Product",
        key="add_product_button"
    ):

        if product_name.strip() == "":
            st.warning("Please enter product name.")

        elif product_price <= 0:
            st.warning("Please enter valid price.")

        else:

            cursor.execute(
                """
                INSERT INTO products
                (name, price, category, emoji)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    product_name.strip(),
                    product_price,
                    product_category,
                    product_emoji
                )
            )

            db.commit()

            st.success(
                f"✅ {product_name} added successfully!"
            )

            st.rerun()


# =========================
# Delete Product
# =========================

st.write("### 🗑️ Delete Product")

cursor.execute("""
    SELECT id, name, price
    FROM products
    ORDER BY id
""")

all_products = cursor.fetchall()

if len(all_products) > 0:

    product_options = {}

    for product in all_products:

        product_options[
            f"{product[1]} - ₹{float(product[2]):,.0f}"
        ] = product[0]

    selected_product = st.selectbox(
        "Select Product",
        list(product_options.keys()),
        key="delete_product_select"
    )

    if st.button(
        "🗑️ Delete Product",
        key="delete_product_button"
    ):

        product_id = product_options[selected_product]

        cursor.execute(
            "DELETE FROM products WHERE id = %s",
            (product_id,)
        )

        db.commit()

        st.success(
            f"✅ {selected_product} deleted successfully!"
        )

        st.rerun()


# =========================
# Update Product
# =========================

st.write("### ✏️ Update Product")

cursor.execute("""
    SELECT id, name, price, category, emoji
    FROM products
    ORDER BY id
""")

update_products = cursor.fetchall()

if len(update_products) > 0:

    update_options = {}

    for product in update_products:

        update_options[
            f"{product[1]} - ₹{float(product[2]):,.0f}"
        ] = product

    selected_update = st.selectbox(
        "Select Product to Update",
        list(update_options.keys()),
        key="update_product_select"
    )

    selected_product = update_options[selected_update]

    product_id = selected_product[0]
    current_name = selected_product[1]
    current_price = float(selected_product[2])
    current_category = selected_product[3]
    current_emoji = selected_product[4]

    new_name = st.text_input(
        "Product Name",
        value=current_name,
        key="update_product_name"
    )

    new_price = st.number_input(
        "Product Price",
        min_value=0.0,
        value=current_price,
        step=100.0,
        key="update_product_price"
    )

    new_category = st.selectbox(
        "Product Category",
        ["Electronics", "Accessories"],
        index=["Electronics", "Accessories"].index(
            current_category
        ),
        key="update_product_category"
    )

    new_emoji = st.text_input(
        "Product Emoji",
        value=current_emoji,
        key="update_product_emoji"
    )

    if st.button(
        "✏️ Update Product",
        key="update_product_button"
    ):

        if new_name.strip() == "":
            st.warning("Please enter product name.")

        elif new_price <= 0:
            st.warning("Please enter valid price.")

        else:

            cursor.execute(
                """
                UPDATE products
                SET name = %s,
                    price = %s,
                    category = %s,
                    emoji = %s
                WHERE id = %s
                """,
                (
                    new_name.strip(),
                    new_price,
                    new_category,
                    new_emoji,
                    product_id
                )
            )

            db.commit()

            st.success(
                f"✅ {new_name} updated successfully!"
            )

            st.rerun()