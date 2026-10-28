"""
demo_pnr_interactive.py
-----------------------------------------------
Interactive, menu-driven demo of pnr.py - lets you type in PNRs and see
the hashing-based lookup work live. This version is fully self-contained:
you can create a fresh booking right here (no need to run another demo
file first) and immediately test PNR lookup on it.

Does not modify pnr.py, booking.py, ticket.py, or database.py.
"""

from pnr import (
    build_pnr_dict,
    check_pnr_status,
    get_status_summary,
    get_all_pnrs_for_train,
    search_pnr_by_passenger_name,
    group_pnrs_by_status,
    benchmark_lookup_speed,
    get_recently_checked,
)
from booking import book_ticket, cancel_booking
from train import CLASS_CONFIG, get_all_trains, display_train_table

try:
    from ticket import generate_ticket, verify_ticket_integrity
    TICKET_MODULE_AVAILABLE = True
except ImportError:
    TICKET_MODULE_AVAILABLE = False


def menu():
    print("\n" + "=" * 55)
    print("   RailEase - PNR Module Interactive Demo")
    print("=" * 55)
    print(" 1. Book a fresh ticket right now (get a new PNR to test)")
    print(" 2. Check PNR status (single check)")
    print(" 3. Continuous PNR check mode (keep checking until you stop)")
    print(" 4. Search bookings by passenger name")
    print(" 5. View all PNRs for a train")
    print(" 6. Group all PNRs by status")
    print(" 7. Run hashing speed benchmark (dict vs list) - your own trial count")
    print(" 8. View recently-checked PNRs (cache)")
    print(" 9. Show total bookings loaded")
    print("10. Generate + verify a ticket for a PNR (staleness check)")
    print("11. List available trains (to pick a train ID from)")
    print(" 0. Exit")
    return input("Enter your choice: ").strip()


def handle_book_fresh():
    print("\n--- Quick Booking (to generate a PNR for testing) ---")
    train_id = input("Train ID (or type 'list' to see trains first): ").strip()
    if train_id.lower() == "list":
        display_train_table(get_all_trains()[:10])
        train_id = input("Now enter Train ID: ").strip()

    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return

    passenger_name = input("Passenger name: ").strip() or "Demo Passenger"
    print(f"Available classes: {list(CLASS_CONFIG.keys())}")
    travel_class = input("Class: ").strip()
    priority = input("Priority booking? (y/n): ").strip().lower() == "y"

    success, info = book_ticket(1, int(train_id), passenger_name, travel_class, priority_request=priority)
    if not success:
        print("\nBooking failed:", info["message"])
        return

    print(f"\nBooked! PNR = {info['pnr']} | status = {info['status']} | seat = {info['seat_number']}")
    print("You can now use this PNR in options 2, 3, 10, etc.")


def handle_check_status():
    pnr = input("Enter PNR to check: ").strip()
    print("\n" + get_status_summary(pnr))
    details = check_pnr_status(pnr)
    if details:
        print("\nFull details:")
        for key, value in details.items():
            print(f"  {key:15s}: {value}")


def handle_continuous_check():
    print("\n--- Continuous PNR Check Mode ---")
    print("Type a PNR and press Enter to check it. Type 'done' to stop.\n")
    while True:
        pnr = input("PNR (or 'done'): ").strip()
        if pnr.lower() == "done":
            break
        print(" ", get_status_summary(pnr))
    print("Exited continuous check mode.")


def handle_name_search():
    name = input("Enter passenger name (or part of it): ").strip()
    results = search_pnr_by_passenger_name(name)
    if not results:
        print("\nNo bookings found matching that name.")
        return
    print(f"\nFound {len(results)} matching booking(s):")
    for pnr, booking in results:
        print(f"  PNR={pnr} | {booking['passenger_name']} | {booking['status']} | train_id={booking['train_id']}")


def handle_train_pnrs():
    train_id = input("Enter train ID: ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    pnrs = get_all_pnrs_for_train(int(train_id))
    if not pnrs:
        print("\nNo bookings found for this train.")
        return
    print(f"\n{len(pnrs)} PNR(s) found for train {train_id}:")
    for pnr in pnrs:
        print(" ", pnr, "->", check_pnr_status(pnr)["status"])


def handle_group_by_status():
    buckets = group_pnrs_by_status()
    print("\nPNRs grouped by status:")
    for status, pnr_list in buckets.items():
        print(f"\n{status} ({len(pnr_list)}):")
        for pnr in pnr_list:
            print("  ", pnr)


def handle_benchmark():
    pnr_dict = build_pnr_dict()
    if not pnr_dict:
        print("\nNo bookings exist yet - book one first (option 1).")
        return
    pnr_choice = input("Enter a specific PNR to benchmark (or leave blank for any): ").strip()
    sample_pnr = pnr_choice if pnr_choice in pnr_dict else list(pnr_dict.keys())[0]

    trials_input = input("How many trials to run? (default 3000): ").strip()
    trials = int(trials_input) if trials_input.isdigit() else 3000

    result = benchmark_lookup_speed(sample_pnr, trials=trials)
    print(f"\nBenchmarking lookup for PNR {sample_pnr} over {result['trials']} trials:")
    print(f"  Dictionary (hash table) time : {result['dict_time_sec']} sec")
    print(f"  Linear list scan time        : {result['list_time_sec']} sec")
    print(f"  Dictionary is ~{result['speedup_factor']}x faster")


def handle_recent_cache():
    recent = get_recently_checked()
    if not recent:
        print("\nNo PNRs have been checked yet in this session.")
        return
    print("\nRecently checked PNRs (oldest -> newest):")
    for pnr, checked_at in recent:
        print(f"  {pnr} checked at {checked_at}")


def handle_total_count():
    pnr_dict = build_pnr_dict()
    print(f"\nTotal bookings currently loaded into the PNR dictionary: {len(pnr_dict)}")


def handle_ticket_verify():
    if not TICKET_MODULE_AVAILABLE:
        print("\nticket.py not found in this folder - upload it to use this option.")
        return

    pnr = input("Enter PNR: ").strip()
    print("\nStep 1: Generating/printing the ticket now...")
    success, result = generate_ticket(pnr)
    if not success:
        print(" ", result)
        return
    print(" Ticket saved to:", result)

    do_cancel = input("\nWant to simulate a change (cancel this booking) before verifying? (y/n): ").strip().lower()
    if do_cancel == "y":
        hours = input("Hours before departure (for refund calc): ").strip()
        hours = float(hours) if hours.replace(".", "", 1).isdigit() else 5
        success, cancel_info = cancel_booking(pnr, hours)
        print(" Cancel result:", cancel_info["message"] if success else cancel_info)

    print("\nStep 2: Verifying ticket integrity against current database state...")
    is_valid, checksum = verify_ticket_integrity(pnr)
    print(f" Ticket still matches database? {is_valid} (checksum: {checksum})")
    if not is_valid:
        print(" -> This means the printed ticket is now STALE (booking changed after printing).")
    else:
        print(" -> Ticket matches - nothing has changed since it was printed.")


def handle_list_trains():
    trains = get_all_trains()
    display_train_table(trains[:10])
    print(f"... showing 10 of {len(trains)} trains total.")


def main():
    actions = {
        "1": handle_book_fresh,
        "2": handle_check_status,
        "3": handle_continuous_check,
        "4": handle_name_search,
        "5": handle_train_pnrs,
        "6": handle_group_by_status,
        "7": handle_benchmark,
        "8": handle_recent_cache,
        "9": handle_total_count,
        "10": handle_ticket_verify,
        "11": handle_list_trains,
    }

    print("Welcome! This demo lets you book, check, and stress-test PNR lookups live.")

    while True:
        choice = menu()
        if choice == "0":
            print("Exiting. Thank you!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main()
