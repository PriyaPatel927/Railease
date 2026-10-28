import sqlite3

conn = sqlite3.connect('railease.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def print_table(title, query):
    print("=" * 70)
    print(title)
    print("=" * 70)
    cur.execute(query)
    rows = cur.fetchall()
    for row in rows:
        print(dict(row))
    print(f"\n>>> Total rows: {len(rows)}\n")

print_table("USERS (all 51 rows)", "SELECT * FROM Users")
print_table("TRAINS (all 50 rows)", "SELECT * FROM Trains")
print_table("STATIONS (all 150 rows)", "SELECT * FROM Stations ORDER BY train_id, station_order")
print_table(
    "FOOD MENU (all 200 rows, with train name)",
    """
    SELECT f.food_id, t.train_name, f.item_name, f.price
    FROM Food_Menu f
    JOIN Trains t ON f.train_id = t.train_id
    ORDER BY t.train_id
    """
)
print_table("BOOKINGS", "SELECT * FROM Bookings")

conn.close()
