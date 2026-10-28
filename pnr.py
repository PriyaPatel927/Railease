"""
pnr.py - RailEase Ticket Booking System
Fast PNR-to-booking lookup using a dictionary (hash table).

DSA concept: Hashing / Dictionary (Section 13 of the report)
"""

import time
from collections import OrderedDict

from database import get_connection


_recent_checks = OrderedDict()
RECENT_CACHE_SIZE = 5


def _track_recent_check(pnr):
    if pnr in _recent_checks:
        _recent_checks.move_to_end(pnr)
    _recent_checks[pnr] = time.strftime("%H:%M:%S")
    if len(_recent_checks) > RECENT_CACHE_SIZE:
        _recent_checks.popitem(last=False)


def get_recently_checked():
    """Recently checked PNRs, oldest first (LRU-style cache)."""
    return list(_recent_checks.items())


def build_pnr_dict():
    """Load every booking into a dict keyed by PNR."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Bookings")
    rows = cur.fetchall()
    conn.close()

    pnr_dict = {}
    for row in rows:
        pnr_dict[row["pnr"]] = dict(row)
    return pnr_dict


def check_pnr_status(pnr):
    """O(1) average lookup of a booking by PNR."""
    pnr_dict = build_pnr_dict()
    result = pnr_dict.get(pnr)
    _track_recent_check(pnr)
    return result


def get_status_summary(pnr):
    """Human-readable one-line status for a PNR."""
    booking = check_pnr_status(pnr)
    if booking is None:
        return f"PNR {pnr} not found."

    if booking["status"] == "Confirmed":
        return f"PNR {pnr}: CONFIRMED - Seat {booking['seat_number']}, {booking['class']} class."
    elif booking["status"] == "Waiting":
        return f"PNR {pnr}: WAITING LIST - no seat allocated yet."
    else:
        return f"PNR {pnr}: CANCELLED."


def get_all_pnrs_for_train(train_id):
    """All PNRs booked for a given train."""
    pnr_dict = build_pnr_dict()
    return [pnr for pnr, booking in pnr_dict.items() if booking["train_id"] == train_id]


def search_pnr_by_passenger_name(name):
    """Reverse lookup by name - O(n), since the dict is keyed by PNR,
    not by name."""
    pnr_dict = build_pnr_dict()
    name = name.strip().lower()
    return [(pnr, b) for pnr, b in pnr_dict.items() if name in b["passenger_name"].lower()]


def group_pnrs_by_status():
    """Bucket every PNR by status (Confirmed/Waiting/Cancelled)."""
    pnr_dict = build_pnr_dict()
    buckets = {"Confirmed": [], "Waiting": [], "Cancelled": []}
    for pnr, booking in pnr_dict.items():
        buckets.setdefault(booking["status"], []).append(pnr)
    return buckets


def benchmark_lookup_speed(pnr, trials=2000):
    """Compare O(1) dict lookup vs O(n) linear list scan for the same PNR."""
    pnr_dict = build_pnr_dict()
    booking_list = list(pnr_dict.values())

    start = time.perf_counter()
    for _ in range(trials):
        _ = pnr_dict.get(pnr)
    dict_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(trials):
        for b in booking_list:
            if b["pnr"] == pnr:
                break
    list_time = time.perf_counter() - start

    speedup = round(list_time / dict_time, 2) if dict_time > 0 else None
    return {
        "trials": trials,
        "dict_time_sec": round(dict_time, 6),
        "list_time_sec": round(list_time, 6),
        "speedup_factor": speedup,
    }


if __name__ == "__main__":
    from booking import book_ticket, cancel_booking

    print("=" * 60)
    print("SETUP: creating sample bookings (Confirmed, Waiting, Cancelled)")
    print("=" * 60)

    setup_train_id = 3
    confirmed_pnrs = []
    for i in range(10):
        _, info = book_ticket(1, setup_train_id, f"Setup Passenger {i+1}", "AC")
        confirmed_pnrs.append(info["pnr"])
    print(f" Created 10 Confirmed bookings on train {setup_train_id} (AC class).")

    _, waiting_info = book_ticket(1, setup_train_id, "Waitlisted Setup Passenger", "AC")
    waiting_pnr = waiting_info["pnr"]
    print(" Created 1 Waiting booking:", waiting_pnr, "-> status:", waiting_info["status"])

    _, cancel_result = cancel_booking(confirmed_pnrs[0], hours_before_departure=20)
    cancelled_pnr = confirmed_pnrs[0]
    print(" Cancelled booking:", cancelled_pnr, "-> refund:", cancel_result["refund_percent"], "%")

    print("\n" + "=" * 60)
    print("TEST 1: Build the PNR dictionary")
    print("=" * 60)
    pnr_dict = build_pnr_dict()
    print(f"Loaded {len(pnr_dict)} total bookings.")

    print("\n" + "=" * 60)
    print("TEST 2: Lookup - CONFIRMED PNR")
    print("=" * 60)
    sample_confirmed = confirmed_pnrs[1]
    print(" ", get_status_summary(sample_confirmed))

    print("\n" + "=" * 60)
    print("TEST 3: Lookup - CANCELLED PNR")
    print("=" * 60)
    print(" ", get_status_summary(cancelled_pnr))

    print("\n" + "=" * 60)
    print("TEST 4: Lookup - WAITING (or auto-promoted) PNR")
    print("=" * 60)
    print(" ", get_status_summary(waiting_pnr))

    print("\n" + "=" * 60)
    print("TEST 5: Lookup - non-existent / malformed PNR")
    print("=" * 60)
    print(" ", get_status_summary("0000000000"))
    print(" ", get_status_summary("ABCDEFGHIJ"))

    print("\n" + "=" * 60)
    print("TEST 6: All PNRs for train_id =", setup_train_id)
    print("=" * 60)
    for p in get_all_pnrs_for_train(setup_train_id):
        print("  ", p, "->", check_pnr_status(p)["status"])

    print("\n" + "=" * 60)
    print("TEST 7: Status breakdown across all bookings")
    print("=" * 60)
    status_counts = {}
    for booking in pnr_dict.values():
        status_counts[booking["status"]] = status_counts.get(booking["status"], 0) + 1
    for status, count in status_counts.items():
        print(f"  {status:10s}: {count}")

    print("\n" + "=" * 60)
    print("TEST 8: Hashing speed benchmark - dict O(1) vs list O(n)")
    print("=" * 60)
    bench = benchmark_lookup_speed(sample_confirmed, trials=3000)
    print(f" Dict lookup time : {bench['dict_time_sec']} sec for {bench['trials']} lookups")
    print(f" List scan time   : {bench['list_time_sec']} sec for {bench['trials']} lookups")
    print(f" Dict is ~{bench['speedup_factor']}x faster")

    print("\n" + "=" * 60)
    print("TEST 9: Reverse search by passenger name")
    print("=" * 60)
    name_results = search_pnr_by_passenger_name("Setup Passenger")
    print(f" Found {len(name_results)} matches. First 3:")
    for pnr_value, booking in name_results[:3]:
        print(f"   {pnr_value} -> {booking['passenger_name']}")

    print("\n" + "=" * 60)
    print("TEST 10: Group PNRs by status")
    print("=" * 60)
    buckets = group_pnrs_by_status()
    for status, pnr_list in buckets.items():
        print(f"  {status:10s}: {len(pnr_list)} PNR(s)")

    print("\n" + "=" * 60)
    print("TEST 11: Recently-checked PNR cache")
    print("=" * 60)
    check_pnr_status(sample_confirmed)
    check_pnr_status(cancelled_pnr)
    check_pnr_status(waiting_pnr)
    for pnr_value, checked_at in get_recently_checked():
        print(f"   {pnr_value} checked at {checked_at}")
