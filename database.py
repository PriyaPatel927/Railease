"""
database.py - RailEase Ticket Booking System
Database connection, table creation, and sample data setup.
"""

import sqlite3
import os
import hashlib

DB_NAME = "railease.db"


def _hash_password(plain_password, salt="railease_static_salt"):
    salted = (salt + plain_password).encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


# connection

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # lets us access columns by name, like a dict
    return conn


# table creation

def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'   -- 'user' or 'admin'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Trains (
            train_id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_name TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            distance INTEGER NOT NULL,
            has_pantry INTEGER DEFAULT 0,   -- 0 = No, 1 = Yes
            status TEXT DEFAULT 'On Time'   -- On Time / Delayed / Cancelled
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Stations (
            station_id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_id INTEGER NOT NULL,
            station_name TEXT NOT NULL,
            station_order INTEGER NOT NULL,
            FOREIGN KEY (train_id) REFERENCES Trains(train_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            train_id INTEGER NOT NULL,
            passenger_name TEXT NOT NULL,
            pnr TEXT UNIQUE NOT NULL,
            class TEXT NOT NULL,           -- General / Sleeper / AC
            seat_number TEXT,
            fare REAL NOT NULL,
            status TEXT DEFAULT 'Waiting', -- Confirmed / Cancelled / Waiting
            booking_time TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (train_id) REFERENCES Trains(train_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Food_Menu (
            food_id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (train_id) REFERENCES Trains(train_id)
        )
    """)

    conn.commit()
    conn.close()
    print("[OK] All tables created successfully.")


# seed lists

CITIES = [
    "Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad", "Pune",
    "Ahmedabad", "Jaipur", "Lucknow", "Kanpur", "Nagpur", "Patna", "Bhopal",
    "Indore", "Surat", "Varanasi", "Amritsar", "Chandigarh", "Guwahati",
    "Ranchi", "Bhubaneswar", "Coimbatore", "Kochi", "Visakhapatnam", "Goa",
    "Dehradun", "Agra", "Gwalior", "Nashik",
]  # 30 cities

TRAIN_TYPES = [
    "Express", "Superfast Express", "Mail", "Duronto Express",
    "Shatabdi Express", "Rajdhani Express", "Jan Shatabdi", "Garib Rath",
    "Intercity Express", "SF Express",
]  # 10 types

STATUSES = ["On Time", "On Time", "On Time", "Delayed", "Cancelled"]  # weighted so most are "On Time"

FOOD_BASE_NAMES = [
    "Veg Thali", "Non-Veg Thali", "Tea", "Coffee", "Sandwich", "Biryani",
    "Cold Drink", "Paneer Roll", "Chicken Roll", "Samosa", "Idli Sambhar",
    "Poha", "Upma", "Dosa", "Vada Pav", "Pav Bhaji", "Chole Bhature",
    "Fried Rice", "Noodles", "Soup", "Salad", "Fruit Bowl", "Ice Cream",
    "Milkshake", "Lassi", "Buttermilk", "Omelette", "Bread Butter", "Cutlet",
    "Pakora", "Dhokla", "Khichdi", "Rajma Chawal", "Dal Makhani", "Mixed Veg",
    "Curd Rice", "Lemon Rice", "Pulao", "Kachori", "Jalebi", "Gulab Jamun",
    "Rasgulla", "Barfi", "Namkeen Pack", "Chips", "Biscuits", "Water Bottle",
    "Juice", "Energy Drink", "Chocolate",
]  # 49 real names ...

while len(FOOD_BASE_NAMES) < 50:
    FOOD_BASE_NAMES.append(f"Snack Pack {len(FOOD_BASE_NAMES) + 1}")

FIRST_NAMES = [
    "Rahul", "Anjali", "Karan", "Sneha", "Vikram", "Neha", "Arjun", "Divya",
    "Rohan", "Priya", "Aman", "Kavya", "Siddharth", "Pooja", "Manish", "Ritu",
    "Suresh", "Meena", "Ankit", "Shreya", "Devansh", "Isha", "Varun", "Nisha",
    "Yash",
]  # 25 first names

LAST_NAMES = [
    "Sharma", "Verma", "Mehta", "Gupta", "Singh", "Joshi", "Nair", "Reddy",
    "Kapoor", "Iyer",
]  # 10 last names -> combined with first names gives 250 unique combos, more than enough for 50


# data generation

def generate_train_data(n=50):
    data = []
    for i in range(n):
        source = CITIES[i % len(CITIES)]
        destination = CITIES[(i + 7) % len(CITIES)]
        if destination == source:
            destination = CITIES[(i + 8) % len(CITIES)]
        midpoint = CITIES[(i + 15) % len(CITIES)]
        if midpoint in (source, destination):
            midpoint = CITIES[(i + 16) % len(CITIES)]

        train_type = TRAIN_TYPES[i % len(TRAIN_TYPES)]
        # index appended so all 50 names are guaranteed unique (train_name is our duplicate check)
        train_name = f"{source} {train_type} {i + 1}"
        distance = 200 + (i * 37) % 2800          # deterministic pseudo-distance, 200-3000 km
        has_pantry = 1 if i % 2 == 0 else 0        # alternate: 25 trains with pantry, 25 without
        status = STATUSES[i % len(STATUSES)]
        stations = [source, midpoint, destination]

        data.append((train_name, source, destination, distance, has_pantry, status, stations))
    return data


def generate_user_data(n=50):
    users = []
    for i in range(n):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[i % len(LAST_NAMES)]
        name = f"{first} {last}"
        email = f"{first.lower()}{i + 1}@railease.com"
        password = f"{first.lower()}{i + 1}23"
        users.append((name, email, password))
    return users


def assign_food_items(train_index, count=8):
    start = (train_index * 3) % len(FOOD_ITEMS)
    return [FOOD_ITEMS[(start + j) % len(FOOD_ITEMS)] for j in range(count)]


TRAIN_DATA = generate_train_data(50)
USER_DATA = generate_user_data(50)
FOOD_ITEMS = [(name, 20 + (i * 4) % 180) for i, name in enumerate(FOOD_BASE_NAMES)]


# sample data insertion

def insert_sample_data():
    conn = get_connection()
    cur = conn.cursor()

    # ---- Admin user ----
    cur.execute("SELECT * FROM Users WHERE email = ?", ("admin@railease.com",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO Users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@railease.com", _hash_password("admin123"), "admin")
        )

    # ---- 50 regular users ----
    for name, email, password in USER_DATA:
        cur.execute("SELECT * FROM Users WHERE email = ?", (email,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO Users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, _hash_password(password), "user")
            )

    # ---- 50 trains + their stations + food menus ----
    for index, (train_name, source, destination, distance, has_pantry, status, stations) in enumerate(TRAIN_DATA):
        cur.execute("SELECT * FROM Trains WHERE train_name = ?", (train_name,))
        if cur.fetchone():
            continue  # already inserted earlier, skip

        cur.execute(
            "INSERT INTO Trains (train_name, source, destination, distance, has_pantry, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (train_name, source, destination, distance, has_pantry, status)
        )
        train_id = cur.lastrowid

        # Stations stored in order (station_order) - this is the "route list"
        for order, station in enumerate(stations, start=1):
            cur.execute(
                "INSERT INTO Stations (train_id, station_name, station_order) VALUES (?, ?, ?)",
                (train_id, station, order)
            )

        # Only trains with pantry (has_pantry = 1) get a food menu,
        # picking 8 items out of the 50-item catalog
        if has_pantry:
            for item, price in assign_food_items(index):
                cur.execute(
                    "INSERT INTO Food_Menu (train_id, item_name, price) VALUES (?, ?, ?)",
                    (train_id, item, price)
                )

    conn.commit()
    conn.close()
    print("[OK] Sample data inserted (or already present).")


def print_summary():
    conn = get_connection()
    cur = conn.cursor()
    for table in ["Users", "Trains", "Stations", "Bookings", "Food_Menu"]:
        cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
        count = cur.fetchone()["c"]
        print(f"{table:12s} -> {count} rows")
    conn.close()


def reset_database():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"[OK] {DB_NAME} deleted.")


# tests

def verify_data():
    conn = get_connection()
    cur = conn.cursor()

    print("=" * 60)
    print("TEST 1: Route of train_id = 1 (stations in order)")
    print("=" * 60)
    cur.execute("SELECT * FROM Stations WHERE train_id = 1 ORDER BY station_order")
    for row in cur.fetchall():
        print(" ", dict(row))

    print("\n" + "=" * 60)
    print("TEST 2: Food menu of train_id = 1 (if it has pantry)")
    print("=" * 60)
    cur.execute("SELECT * FROM Food_Menu WHERE train_id = 1")
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(" ", dict(row))
    else:
        print("  (this train has no pantry, so no food menu - that's expected)")

    print("\n" + "=" * 60)
    print("TEST 3: First 5 users (name + email)")
    print("=" * 60)
    cur.execute("SELECT name, email FROM Users LIMIT 5")
    for row in cur.fetchall():
        print(" ", dict(row))

    print("\n" + "=" * 60)
    print("TEST 4: Search test - all trains starting from Delhi")
    print("=" * 60)
    cur.execute("SELECT train_name, source, destination, status FROM Trains WHERE source = 'Delhi'")
    for row in cur.fetchall():
        print(" ", dict(row))

    print("\n" + "=" * 60)
    print("TEST 5: Train count grouped by status")
    print("=" * 60)
    cur.execute("SELECT status, COUNT(*) as cnt FROM Trains GROUP BY status")
    for row in cur.fetchall():
        print(" ", dict(row))

    print("\n" + "=" * 60)
    print("TEST 6: Data integrity - any train with NO stations? (should be empty)")
    print("=" * 60)
    cur.execute("""
        SELECT t.train_name FROM Trains t
        LEFT JOIN Stations s ON t.train_id = s.train_id
        WHERE s.train_id IS NULL
    """)
    orphans = cur.fetchall()
    if orphans:
        for row in orphans:
            print("  [PROBLEM] ", dict(row))
    else:
        print("  [OK] Every train has at least one station.")

    conn.close()


if __name__ == "__main__":
    # Running this file directly will set up the database from scratch,
    # then run the verification tests so you can see everything working.
    create_tables()
    insert_sample_data()
    print("\nRailEase database is ready! (railease.db)\n")
    print_summary()
    print()
    verify_data()
