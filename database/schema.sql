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
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    service_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Order Placed',
    order_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)
        REFERENCES Customers(customer_id)
);

CREATE TABLE IF NOT EXISTS Billing (
    bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL UNIQUE,
    amount REAL NOT NULL CHECK (amount >= 0),
    discount REAL NOT NULL DEFAULT 0,
    total_amount REAL NOT NULL CHECK (total_amount >= 0),
    FOREIGN KEY (order_id)
        REFERENCES Orders(order_id)
);