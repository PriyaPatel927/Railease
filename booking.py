"""
booking.py - RailEase Ticket Booking System
Booking, seat allocation, waiting list, cancellation, refund, history.

DSA: Queue (deque) for the waiting list, Priority Queue/Heap (heapq)
for picking who gets a seat when one frees up.
"""

import heapq
import secrets
import time
from collections import deque

from database import get_connection
from train import calculate_fare, get_first_available_seat, get_food_menu


def _ensure_priority_column():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE Bookings ADD COLUMN priority INTEGER DEFAULT 1")
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


_ensure_priority_column()


def generate_pnr():
    conn = get_connection()
    cur = conn.cursor()
    while True:
        pnr = str(secrets.randbelow(9_000_000_000) + 1_000_000_000)
        cur.execute("SELECT 1 FROM Bookings WHERE pnr = ?", (pnr,))
        if cur.fetchone() is None:
            conn.close()
            return pnr


def _calculate_total_fare(train_id, travel_class, food_items):
    base_fare = calculate_fare(train_id, travel_class)
    if base_fare is None:
        return None

    food_total = 0.0
    if food_items:
        menu = dict(get_food_menu(train_id))
        for item in food_items:
            food_total += menu.get(item, 0.0)

    return round(base_fare + food_total, 2)


def book_ticket(user_id, train_id, passenger_name, travel_class, food_items=None, priority_request=False):
    total_fare = _calculate_total_fare(train_id, travel_class, food_items)
    if total_fare is None:
        return False, {"message": "Invalid train ID or class."}

    pnr = generate_pnr()
    seat = get_first_available_seat(train_id, travel_class)
    status = "Confirmed" if seat else "Waiting"
    priority_value = 0 if priority_request else 1

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO Bookings
           (user_id, train_id, passenger_name, pnr, class, seat_number, fare, status, priority)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, train_id, passenger_name, pnr, travel_class, seat, total_fare, status, priority_value)
    )
    conn.commit()
    conn.close()

    info = {
        "pnr": pnr,
        "status": status,
        "seat_number": seat,
        "fare": total_fare,
        "message": (
            f"Booking confirmed! Seat {seat} allocated."
            if status == "Confirmed"
            else "Class is full - added to the waiting list."
        ),
    }
    return True, info


def get_waiting_queue(train_id, travel_class):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT booking_id, passenger_name, booking_time, priority
           FROM Bookings
           WHERE train_id = ? AND class = ? AND status = 'Waiting'
           ORDER BY booking_time ASC""",
        (train_id, travel_class)
    )
    rows = cur.fetchall()
    conn.close()

    queue = deque()
    for row in rows:
        queue.append(dict(row))
    return queue


def peek_next_in_line(train_id, travel_class):
    queue = get_waiting_queue(train_id, travel_class)
    return queue[0] if queue else None


def _build_priority_heap(train_id, travel_class):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT booking_id, priority, booking_time
           FROM Bookings
           WHERE train_id = ? AND class = ? AND status = 'Waiting'""",
        (train_id, travel_class)
    )
    rows = cur.fetchall()
    conn.close()

    heap = []
    for row in rows:
        heapq.heappush(heap, (row["priority"], row["booking_time"], row["booking_id"]))
    return heap


def confirm_next_waiting_passenger(train_id, travel_class, released_seat):
    heap = _build_priority_heap(train_id, travel_class)
    if not heap:
        return None

    _, _, booking_id = heapq.heappop(heap)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE Bookings SET status = 'Confirmed', seat_number = ? WHERE booking_id = ?",
        (released_seat, booking_id)
    )
    conn.commit()
    conn.close()
    return booking_id


def calculate_refund_percentage(hours_before_departure):
    if hours_before_departure >= 24:
        return 90
    elif hours_before_departure >= 12:
        return 50
    elif hours_before_departure >= 2:
        return 25
    return 0


def get_booking_by_pnr(pnr):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Bookings WHERE pnr = ?", (pnr,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def cancel_booking(pnr, hours_before_departure):
    booking = get_booking_by_pnr(pnr)
    if booking is None:
        return False, {"message": "No booking found with this PNR."}
    if booking["status"] == "Cancelled":
        return False, {"message": "This booking is already cancelled."}

    was_confirmed = booking["status"] == "Confirmed"
    refund_percent = calculate_refund_percentage(hours_before_departure)
    refund_amount = round(booking["fare"] * refund_percent / 100, 2)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Bookings SET status = 'Cancelled' WHERE pnr = ?", (pnr,))
    conn.commit()
    conn.close()

    promoted_booking_id = None
    if was_confirmed and booking["seat_number"]:
        promoted_booking_id = confirm_next_waiting_passenger(
            booking["train_id"], booking["class"], booking["seat_number"]
        )

    return True, {
        "message": "Booking cancelled successfully.",
        "refund_percent": refund_percent,
        "refund_amount": refund_amount,
        "promoted_booking_id": promoted_booking_id,
    }


def get_booking_history(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM Bookings WHERE user_id = ? ORDER BY booking_time DESC",
        (user_id,)
    )
    history = [dict(row) for row in cur.fetchall()]
    conn.close()
    return history


def get_train_booking_summary(train_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT status, COUNT(*) as cnt FROM Bookings WHERE train_id = ? GROUP BY status",
        (train_id,)
    )
    summary = {row["status"]: row["cnt"] for row in cur.fetchall()}
    conn.close()
    for status in ("Confirmed", "Waiting", "Cancelled"):
        summary.setdefault(status, 0)
    return summary


if __name__ == "__main__":
    TEST_TRAIN_ID = 2
    TEST_CLASS = "AC"

    print("=" * 60)
    print("TEST 1: Book tickets until the AC class is full (10 seats)")
    print("=" * 60)
    pnrs = []
    for i in range(10):
        success, info = book_ticket(1, TEST_TRAIN_ID, f"Passenger {i+1}", TEST_CLASS)
        pnrs.append(info["pnr"])
        print(f" Passenger {i+1}: status={info['status']}, seat={info['seat_number']}")

    print("\n" + "=" * 60)
    print("TEST 2: Book 2 more (normal) passengers - should go to Waiting list")
    print("=" * 60)
    success, waiting_1 = book_ticket(1, TEST_TRAIN_ID, "Waitlist Passenger A", TEST_CLASS)
    print(" Waitlist Passenger A:", waiting_1["status"])
    success, waiting_2 = book_ticket(1, TEST_TRAIN_ID, "Waitlist Passenger B", TEST_CLASS)
    print(" Waitlist Passenger B:", waiting_2["status"])

    print("\n" + "=" * 60)
    print("TEST 3: Book a PRIORITY passenger - still goes to Waiting list,")
    print("        but should jump ahead of A and B when a seat frees up")
    print("=" * 60)
    success, waiting_priority = book_ticket(
        1, TEST_TRAIN_ID, "Priority Passenger", TEST_CLASS, priority_request=True
    )
    print(" Priority Passenger:", waiting_priority["status"])

    print("\n" + "=" * 60)
    print("TEST 4: Plain FIFO queue view (deque) - front of the line")
    print("=" * 60)
    queue_view = get_waiting_queue(TEST_TRAIN_ID, TEST_CLASS)
    print(" Waiting queue (FIFO order):", [p["passenger_name"] for p in queue_view])
    print(" peek_next_in_line() (by time, ignores priority):",
          peek_next_in_line(TEST_TRAIN_ID, TEST_CLASS)["passenger_name"])

    print("\n" + "=" * 60)
    print("TEST 5: Cancel one CONFIRMED booking -> priority passenger")
    print("        should be promoted first (heap), not Waitlist Passenger A")
    print("=" * 60)
    success, cancel_info = cancel_booking(pnrs[0], hours_before_departure=30)
    print(" Cancel result:", cancel_info["message"], "| refund:", cancel_info["refund_percent"], "%")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT passenger_name, status, seat_number FROM Bookings WHERE booking_id = ?",
                (cancel_info["promoted_booking_id"],))
    promoted_row = cur.fetchone()
    conn.close()
    print(" Promoted passenger:", dict(promoted_row) if promoted_row else "None")

    print("\n" + "=" * 60)
    print("TEST 6: Refund percentage tiers")
    print("=" * 60)
    for hours in [30, 15, 5, 1]:
        print(f" {hours} hrs before departure -> {calculate_refund_percentage(hours)}% refund")

    print("\n" + "=" * 60)
    print("TEST 7: Booking history for user_id = 1")
    print("=" * 60)
    history = get_booking_history(1)
    print(f" Total bookings for user 1: {len(history)}")
    for h in history[:5]:
        print(f"  PNR={h['pnr']} | {h['passenger_name']} | {h['status']} | seat={h['seat_number']}")

    print("\n" + "=" * 60)
    print("TEST 8: Train booking summary (Confirmed/Waiting/Cancelled counts)")
    print("=" * 60)
    print(" Summary:", get_train_booking_summary(TEST_TRAIN_ID))

    print("\n" + "=" * 60)
    print("TEST 9: Cancel a booking that doesn't exist")
    print("=" * 60)
    success, info = cancel_booking("0000000000", 10)
    print(" success:", success, "| message:", info["message"])

    print("\n" + "=" * 60)
    print("TEST 10: Booking with food items included in fare")
    print("=" * 60)
    menu = get_food_menu(1)
    sample_items = [name for name, _ in menu[:2]] if menu else []
    success, info = book_ticket(1, 1, "Food Test Passenger", "General", food_items=sample_items)
    print(" Ordered food:", sample_items)
    print(" Total fare (ticket + food):", info["fare"])
