import streamlit as st
import sqlite3
from pathlib import Path

# Project configuration
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "laundry.db"

st.set_page_config(
    page_title="Automated Laundry Workflow System",
    page_icon="🧺",
    layout="wide"
)

# Database connection
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Create database tables
def initialize_database():
    conn = get_connection()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS Customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS Orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            garment_type TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            service_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Order Placed',
            order_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id)
                REFERENCES Customers(customer_id)
        );

        CREATE TABLE IF NOT EXISTS Billing (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL UNIQUE,
            amount REAL NOT NULL CHECK(amount >= 0),
            discount REAL NOT NULL DEFAULT 0,
            total_amount REAL NOT NULL CHECK(total_amount >= 0),
            FOREIGN KEY(order_id)
                REFERENCES Orders(order_id)
        );
    """)

    conn.commit()
    conn.close()


initialize_database()

# Laundry workflow
WORKFLOW = [
    "Order Placed",
    "Washing",
    "Drying",
    "Ironing",
    "Packaging",
    "Ready for Pickup",
    "Delivered"
]

# Sample service prices
PRICE_LIST = {
    "Wash": 50,
    "Iron": 30,
    "Wash + Iron": 70,
    "Wash + Dry + Iron": 100
}

st.title("🧺 Automated Laundry Workflow System")
st.caption("Laundry order management, workflow tracking and billing")

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Customer Management",
        "Place Order",
        "Order Tracking",
        "Billing",
        "Order History"
    ]
)

# Dashboard
if page == "Dashboard":
    conn = get_connection()

    customers = conn.execute(
        "SELECT COUNT(*) FROM Customers"
    ).fetchone()[0]

    orders = conn.execute(
        "SELECT COUNT(*) FROM Orders"
    ).fetchone()[0]

    revenue = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM Billing"
    ).fetchone()[0]

    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Customers", customers)
    col2.metric("Total Orders", orders)
    col3.metric("Total Billed", f"₹{revenue:.2f}")

    st.subheader("Laundry Workflow")
    st.write("Order Placed → Washing → Drying → Ironing → Packaging → Ready for Pickup → Delivered")

# Customer Management
elif page == "Customer Management":
    st.subheader("Register Customer")

    with st.form("customer_form"):
        name = st.text_input("Customer Name")
        phone = st.text_input("Phone Number")
        submitted = st.form_submit_button("Register Customer")

    if submitted:
        if not name.strip() or not phone.strip():
            st.error("Enter both customer name and phone number.")
        else:
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO Customers(name, phone) VALUES (?, ?)",
                    (name.strip(), phone.strip())
                )
                conn.commit()
                st.success("Customer registered successfully!")
            except sqlite3.IntegrityError:
                st.error("This phone number is already registered.")
            finally:
                conn.close()

    conn = get_connection()
    rows = conn.execute(
        "SELECT customer_id, name, phone, created_at "
        "FROM Customers ORDER BY customer_id DESC"
    ).fetchall()
    conn.close()

    st.subheader("Customer Records")
    st.dataframe(
        rows,
        column_config={
            "customer_id": "Customer ID",
            "name": "Name",
            "phone": "Phone",
            "created_at": "Registered At"
        },
        use_container_width=True
    )

# Place Order
elif page == "Place Order":
    st.subheader("Create Laundry Order")

    conn = get_connection()
    customers = conn.execute(
        "SELECT customer_id, name, phone FROM Customers ORDER BY name"
    ).fetchall()
    conn.close()

    if not customers:
        st.warning("Register a customer before placing an order.")
    else:
        customer_map = {
            f"{row[1]} — {row[2]} (ID {row[0]})": row[0]
            for row in customers
        }

        with st.form("order_form"):
            customer_label = st.selectbox(
                "Select Customer", list(customer_map.keys())
            )
            garment = st.selectbox(
                "Garment Type",
                ["Shirt", "Pant", "Saree", "Bedsheet", "Other"]
            )
            quantity = st.number_input(
                "Quantity", min_value=1, max_value=500, value=1
            )
            service = st.selectbox(
                "Service", list(PRICE_LIST.keys())
            )
            discount = st.number_input(
                "Discount (₹)", min_value=0.0, value=0.0
            )

            price = PRICE_LIST[service] * quantity
            discount = min(discount, float(price))
            total = price - discount

            st.write(f"Base Amount: ₹{price:.2f}")
            st.write(f"Discount: ₹{discount:.2f}")
            st.write(f"Total Amount: ₹{total:.2f}")

            submitted = st.form_submit_button("Place Order")

        if submitted:
            conn = get_connection()

            cursor = conn.execute(
                """
                INSERT INTO Orders
                (customer_id, garment_type, quantity, service_type)
                VALUES (?, ?, ?, ?)
                """,
                (
                    customer_map[customer_label],
                    garment,
                    quantity,
                    service
                )
            )

            order_id = cursor.lastrowid

            conn.execute(
                """
                INSERT INTO Billing
                (order_id, amount, discount, total_amount)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, price, discount, total)
            )

            conn.commit()
            conn.close()

            st.success(f"Order #{order_id} created successfully!")
            st.info(f"Total Bill: ₹{total:.2f}")

# Order Tracking
elif page == "Order Tracking":
    st.subheader("Update Laundry Workflow")

    conn = get_connection()
    orders = conn.execute(
        """
        SELECT o.order_id, c.name, o.garment_type,
               o.quantity, o.status
        FROM Orders o
        JOIN Customers c ON c.customer_id = o.customer_id
        ORDER BY o.order_id DESC
        """
    ).fetchall()
    conn.close()

    if not orders:
        st.info("No orders available.")
    else:
        order_map = {
            f"Order #{r[0]} — {r[1]} — {r[2]}": r
            for r in orders
        }

        selected = st.selectbox(
            "Select Order", list(order_map.keys())
        )
        record = order_map[selected]

        st.write(f"Current Status: **{record[4]}**")

        new_status = st.selectbox(
            "Update Status",
            WORKFLOW,
            index=WORKFLOW.index(record[4])
        )

        if st.button("Update Order Status"):
            conn = get_connection()
            conn.execute(
                "UPDATE Orders SET status = ? WHERE order_id = ?",
                (new_status, record[0])
            )
            conn.commit()
            conn.close()
            st.success("Order status updated.")
            st.rerun()

# Billing
elif page == "Billing":
    st.subheader("Billing Records")

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT b.bill_id, b.order_id, c.name,
               b.amount, b.discount, b.total_amount
        FROM Billing b
        JOIN Orders o ON o.order_id = b.order_id
        JOIN Customers c ON c.customer_id = o.customer_id
        ORDER BY b.bill_id DESC
        """
    ).fetchall()
    conn.close()

    st.dataframe(
        rows,
        column_config={
            "bill_id": "Bill ID",
            "order_id": "Order ID",
            "name": "Customer",
            "amount": "Base Amount",
            "discount": "Discount",
            "total_amount": "Total Amount"
        },
        use_container_width=True
    )

# Order History
elif page == "Order History":
    st.subheader("Laundry Order History")

    conn = get_connection()
    rows = conn.execute(
        """
        SELECT o.order_id, c.name, o.garment_type,
               o.quantity, o.service_type, o.status,
               o.order_date, b.total_amount
        FROM Orders o
        JOIN Customers c ON c.customer_id = o.customer_id
        LEFT JOIN Billing b ON b.order_id = o.order_id
        ORDER BY o.order_id DESC
        """
    ).fetchall()
    conn.close()

    st.dataframe(
        rows,
        column_config={
            "order_id": "Order ID",
            "name": "Customer",
            "garment_type": "Garment",
            "quantity": "Quantity",
            "service_type": "Service",
            "status": "Status",
            "order_date": "Order Date",
            "total_amount": "Total Bill"
        },
        use_container_width=True
    )