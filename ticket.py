"""
ticket.py - RailEase Ticket Booking System
Generates the e-ticket (.txt file) for a booking. Also supports a QR
code, a checksum to detect if a ticket is stale, and bulk generation.

DSA concept: File Handling (Section 20 of the report)
"""

import os
import hashlib
from datetime import datetime

from database import get_connection
from train import get_train_by_id

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


TICKETS_DIR = "tickets"


def _get_booking(pnr):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Bookings WHERE pnr = ?", (pnr,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def _compute_ticket_checksum(booking):
    """Short hash of the booking's key fields. Used to check later if
    the booking changed since the ticket was printed."""
    raw = f"{booking['pnr']}|{booking['passenger_name']}|{booking['seat_number']}|{booking['fare']}|{booking['status']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12].upper()


def generate_ticket(pnr):
    """Write a .txt e-ticket for the given PNR."""
    booking = _get_booking(pnr)
    if booking is None:
        return False, "No booking found with this PNR."

    train = get_train_by_id(booking["train_id"])
    if train is None:
        return False, "Train details not found for this booking."

    os.makedirs(TICKETS_DIR, exist_ok=True)
    file_path = os.path.join(TICKETS_DIR, f"ticket_{pnr}.txt")
    checksum = _compute_ticket_checksum(booking)

    lines = [
        "=" * 45,
        "        RAILEASE E-TICKET",
        "=" * 45,
        f"PNR            : {booking['pnr']}",
        f"Passenger      : {booking['passenger_name']}",
        f"Train          : {train['train_name']} (ID {train['train_id']})",
        f"Route          : {train['source']} -> {train['destination']}",
        f"Class          : {booking['class']}",
        f"Seat           : {booking['seat_number'] or 'Not allocated (Waiting list)'}",
        f"Fare           : Rs.{booking['fare']}",
        f"Status         : {booking['status']}",
        f"Booking Time   : {booking['booking_time']}",
        f"Ticket Printed : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "-" * 45,
        f"Verification Code : {checksum}",
        "=" * 45,
        "Have a safe journey!",
        "=" * 45,
    ]

    with open(file_path, "w") as f:
        f.write("\n".join(lines))

    return True, file_path


def read_ticket(pnr):
    """Read back a previously generated ticket file, if it exists."""
    file_path = os.path.join(TICKETS_DIR, f"ticket_{pnr}.txt")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as f:
        return f.read()


def verify_ticket_integrity(pnr):
    """Recompute the checksum from current DB data and compare it to
    the one saved in the ticket file - detects a stale/changed booking."""
    booking = _get_booking(pnr)
    if booking is None:
        return False, "Booking not found in the database."

    file_content = read_ticket(pnr)
    if file_content is None:
        return False, "Ticket file not found - generate it first."

    current_checksum = _compute_ticket_checksum(booking)
    is_valid = current_checksum in file_content
    return is_valid, current_checksum


def generate_qr_code(pnr):
    """Generate a scannable QR code (PNG) encoding the booking details."""
    if not QR_AVAILABLE:
        return False, "qrcode library not installed. Run: pip install qrcode[pil]"

    booking = _get_booking(pnr)
    if booking is None:
        return False, "No booking found with this PNR."

    os.makedirs(TICKETS_DIR, exist_ok=True)
    qr_data = (
        f"RailEase | PNR:{booking['pnr']} | {booking['passenger_name']} | "
        f"{booking['class']} | Seat:{booking['seat_number']} | {booking['status']}"
    )
    img = qrcode.make(qr_data)
    path = os.path.join(TICKETS_DIR, f"ticket_{pnr}_qr.png")
    img.save(path)
    return True, path


def generate_all_tickets_for_user(user_id):
    """Generate .txt tickets for every booking a user has made."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT pnr FROM Bookings WHERE user_id = ?", (user_id,))
    pnr_list = [row["pnr"] for row in cur.fetchall()]
    conn.close()

    results = []
    for pnr in pnr_list:
        success, path_or_message = generate_ticket(pnr)
        results.append((pnr, success, path_or_message))
    return results


if __name__ == "__main__":
    from booking import book_ticket, cancel_booking

    print("=" * 60)
    print("SETUP: creating sample bookings (Confirmed, Waiting, Cancelled)")
    print("=" * 60)

    _, confirmed_info = book_ticket(1, 1, "Confirmed Demo Passenger", "General")
    confirmed_pnr = confirmed_info["pnr"]
    print(" Confirmed booking PNR:", confirmed_pnr)
    generate_ticket(confirmed_pnr)  # print ticket now, while still Confirmed

    for i in range(10):
        book_ticket(1, 3, f"Filler Passenger {i+1}", "AC")
    _, waiting_info = book_ticket(1, 3, "Waiting Demo Passenger", "AC")
    waiting_pnr = waiting_info["pnr"]
    print(" Waiting-list booking PNR:", waiting_pnr, "-> status:", waiting_info["status"])

    _, cancel_result = cancel_booking(confirmed_pnr, hours_before_departure=3)
    print(" Cancelled the Confirmed booking above -> refund:", cancel_result["refund_percent"], "%")

    print("\n" + "=" * 60)
    print("TEST 1: Read the ticket printed BEFORE cancellation (now stale)")
    print("=" * 60)
    print(read_ticket(confirmed_pnr))

    print("\n" + "=" * 60)
    print("TEST 2: Generate ticket for the WAITING-LIST booking")
    print("=" * 60)
    success, result = generate_ticket(waiting_pnr)
    print(" success:", success)
    if success:
        print(read_ticket(waiting_pnr))

    print("\n" + "=" * 60)
    print("TEST 3: Generate ticket for a fresh CONFIRMED booking")
    print("=" * 60)
    _, fresh_info = book_ticket(1, 2, "Fresh Confirmed Passenger", "Sleeper")
    fresh_pnr = fresh_info["pnr"]
    success, result = generate_ticket(fresh_pnr)
    print(" success:", success)
    if success:
        print(read_ticket(fresh_pnr))

    print("\n" + "=" * 60)
    print("TEST 4: Generate ticket for a non-existent PNR")
    print("=" * 60)
    print(" ", generate_ticket("0000000000"))

    print("\n" + "=" * 60)
    print("TEST 5: Read a ticket that was never generated")
    print("=" * 60)
    print(" ", read_ticket("9999999999"))

    print("\n" + "=" * 60)
    print("TEST 6: Confirm ticket files exist on disk")
    print("=" * 60)
    for pnr in (confirmed_pnr, waiting_pnr, fresh_pnr):
        path = os.path.join(TICKETS_DIR, f"ticket_{pnr}.txt")
        print(f"  {path} exists:", os.path.exists(path))

    print("\n" + "=" * 60)
    print("TEST 7: List every ticket file generated this run")
    print("=" * 60)
    if os.path.isdir(TICKETS_DIR):
        for filename in sorted(os.listdir(TICKETS_DIR)):
            print("  ", filename)

    print("\n" + "=" * 60)
    print("TEST 8: Verify ticket integrity - unmodified ticket")
    print("=" * 60)
    is_valid, checksum = verify_ticket_integrity(fresh_pnr)
    print(f" Ticket for {fresh_pnr} valid? {is_valid} (checksum: {checksum})")

    print("\n" + "=" * 60)
    print("TEST 9: Verify ticket integrity - booking changed after printing")
    print("=" * 60)
    is_valid, checksum = verify_ticket_integrity(confirmed_pnr)
    print(f" Ticket for {confirmed_pnr} still valid? {is_valid}")
    print(" False is expected: ticket says Confirmed, DB now says Cancelled.")

    print("\n" + "=" * 60)
    print("TEST 10: QR code generation")
    print("=" * 60)
    success, result = generate_qr_code(fresh_pnr)
    print(" success:", success, "| result:", result)

    print("\n" + "=" * 60)
    print("TEST 11: Bulk-generate every ticket for user_id = 1")
    print("=" * 60)
    bulk_results = generate_all_tickets_for_user(1)
    print(f" Generated {len(bulk_results)} ticket(s) for user 1:")
    for pnr_value, success, path_or_msg in bulk_results:
        print(f"   {pnr_value} -> success={success} -> {path_or_msg}")
