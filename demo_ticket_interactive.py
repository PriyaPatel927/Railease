"""
demo_ticket_interactive.py
Interactive, menu-driven demo of ticket.py. Does not modify ticket.py,
booking.py, or database.py.
"""

from ticket import (
    generate_ticket,
    read_ticket,
    verify_ticket_integrity,
    generate_qr_code,
    generate_all_tickets_for_user,
)
from booking import book_ticket, cancel_booking
from train import CLASS_CONFIG, get_all_trains, display_train_table


def menu():
    print("\n" + "=" * 55)
    print("   RailEase - Ticket Module Demo")
    print("=" * 55)
    print("1. Book a fresh ticket (get a new PNR to test)")
    print("2. Generate a ticket for a PNR")
    print("3. Read a previously generated ticket")
    print("4. Verify ticket integrity (staleness check)")
    print("5. Generate a QR code for a PNR")
    print("6. Bulk-generate all tickets for a user")
    print("7. Cancel a booking (to test staleness afterwards)")
    print("8. List available trains")
    print("0. Exit")
    return input("Enter your choice: ").strip()


def handle_book():
    train_id = input("Train ID (or type 'list'): ").strip()
    if train_id.lower() == "list":
        display_train_table(get_all_trains()[:10])
        train_id = input("Now enter Train ID: ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    passenger_name = input("Passenger name: ").strip() or "Demo Passenger"
    print(f"Available classes: {list(CLASS_CONFIG.keys())}")
    travel_class = input("Class: ").strip()

    success, info = book_ticket(1, int(train_id), passenger_name, travel_class)
    if not success:
        print("\nBooking failed:", info["message"])
        return
    print(f"\nBooked! PNR = {info['pnr']} | status = {info['status']}")


def handle_generate():
    pnr = input("Enter PNR: ").strip()
    success, result = generate_ticket(pnr)
    if not success:
        print("\n", result)
        return
    print("\nTicket saved to:", result)
    print(read_ticket(pnr))


def handle_read():
    pnr = input("Enter PNR: ").strip()
    content = read_ticket(pnr)
    if content is None:
        print("\nNo ticket file found for this PNR - generate it first (option 2).")
        return
    print()
    print(content)


def handle_verify():
    pnr = input("Enter PNR: ").strip()
    is_valid, checksum = verify_ticket_integrity(pnr)
    print(f"\nTicket valid? {is_valid} (checksum: {checksum})")
    if not is_valid:
        print("This means the booking changed after the ticket was printed.")


def handle_qr():
    pnr = input("Enter PNR: ").strip()
    success, result = generate_qr_code(pnr)
    print()
    if success:
        print("QR code saved to:", result)
    else:
        print(result)


def handle_bulk():
    user_id = input("Enter user ID: ").strip()
    if not user_id.isdigit():
        print("Please enter a valid numeric user ID.")
        return
    results = generate_all_tickets_for_user(int(user_id))
    if not results:
        print("\nNo bookings found for this user.")
        return
    print(f"\nGenerated {len(results)} ticket(s):")
    for pnr, success, path_or_msg in results:
        print(f"  {pnr} -> success={success} -> {path_or_msg}")


def handle_cancel():
    pnr = input("Enter PNR to cancel: ").strip()
    hours = input("Hours before departure: ").strip()
    hours = float(hours) if hours.replace(".", "", 1).isdigit() else 5
    success, info = cancel_booking(pnr, hours)
    print()
    if success:
        print("Cancelled. Refund:", info["refund_percent"], "%")
        print("Now try option 4 (verify) on this PNR to see the staleness check.")
    else:
        print(info["message"])


def handle_list_trains():
    trains = get_all_trains()
    display_train_table(trains[:10])
    print(f"... showing 10 of {len(trains)} trains total.")


def main():
    actions = {
        "1": handle_book,
        "2": handle_generate,
        "3": handle_read,
        "4": handle_verify,
        "5": handle_qr,
        "6": handle_bulk,
        "7": handle_cancel,
        "8": handle_list_trains,
    }

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
