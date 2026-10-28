"""
demo_booking_interactive.py
Interactive menu-driven demo of booking.py.
"""

from booking import (
    book_ticket,
    cancel_booking,
    get_booking_by_pnr,
    get_booking_history,
    get_waiting_queue,
    get_train_booking_summary,
)
from train import get_food_menu, CLASS_CONFIG


def menu():
    print("\n" + "=" * 50)
    print("   RailEase - Booking Module Demo")
    print("=" * 50)
    print("1. Book a ticket")
    print("2. Cancel a ticket (by PNR)")
    print("3. Check booking status by PNR")
    print("4. View booking history (by user ID)")
    print("5. View waiting queue for a train + class")
    print("6. View train booking summary")
    print("0. Exit")
    return input("Enter your choice: ").strip()


def handle_book():
    user_id = input("Enter your user ID (e.g. 1): ").strip()
    train_id = input("Enter train ID: ").strip()
    passenger_name = input("Passenger name: ").strip()
    print(f"Available classes: {list(CLASS_CONFIG.keys())}")
    travel_class = input("Class (General/Sleeper/AC): ").strip()

    if not (user_id.isdigit() and train_id.isdigit()):
        print("User ID and Train ID must be numbers.")
        return

    food_items = []
    menu_items = get_food_menu(int(train_id))
    if menu_items:
        print("\nFood menu available on this train:")
        for name, price in menu_items:
            print(f"  {name} - Rs.{price}")
        chosen = input("Enter food items you want, comma-separated (or leave blank): ").strip()
        if chosen:
            food_items = [item.strip() for item in chosen.split(",")]

    priority_input = input("Is this a priority booking (senior citizen/emergency)? (y/n): ").strip().lower()
    priority_request = priority_input == "y"

    success, info = book_ticket(
        int(user_id), int(train_id), passenger_name, travel_class,
        food_items=food_items, priority_request=priority_request
    )

    if not success:
        print("\nBooking failed:", info["message"])
        return

    print("\n--- Booking Result ---")
    print(" PNR         :", info["pnr"])
    print(" Status      :", info["status"])
    print(" Seat        :", info["seat_number"])
    print(" Total Fare  : Rs.", info["fare"])
    print(" Message     :", info["message"])


def handle_cancel():
    pnr = input("Enter PNR to cancel: ").strip()
    hours = input("How many hours before departure are you cancelling? ").strip()
    if not hours.replace(".", "", 1).isdigit():
        print("Please enter a valid number of hours.")
        return

    success, info = cancel_booking(pnr, float(hours))
    if not success:
        print("\nCancellation failed:", info["message"])
        return

    print("\n--- Cancellation Result ---")
    print(" Message       :", info["message"])
    print(" Refund percent:", info["refund_percent"], "%")
    print(" Refund amount : Rs.", info["refund_amount"])
    if info["promoted_booking_id"]:
        print(" A waiting passenger was promoted to your seat (booking_id =",
              info["promoted_booking_id"], ")")
    else:
        print(" No one was waiting - seat is now simply free.")


def handle_check_pnr():
    pnr = input("Enter PNR: ").strip()
    booking = get_booking_by_pnr(pnr)
    if booking is None:
        print("\nNo booking found with this PNR.")
        return
    print("\n--- Booking Details ---")
    for key in ("pnr", "passenger_name", "train_id", "class", "seat_number", "fare", "status"):
        print(f" {key:15s}: {booking[key]}")


def handle_history():
    user_id = input("Enter user ID: ").strip()
    if not user_id.isdigit():
        print("Please enter a valid numeric user ID.")
        return
    history = get_booking_history(int(user_id))
    if not history:
        print("\nNo bookings found for this user.")
        return
    print(f"\nTotal bookings: {len(history)}\n")
    for h in history:
        print(f" PNR={h['pnr']} | {h['passenger_name']} | {h['class']} | "
              f"seat={h['seat_number']} | status={h['status']} | fare=Rs.{h['fare']}")


def handle_waiting_queue():
    train_id = input("Enter train ID: ").strip()
    print(f"Available classes: {list(CLASS_CONFIG.keys())}")
    travel_class = input("Class: ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    queue = get_waiting_queue(int(train_id), travel_class)
    if not queue:
        print("\nNo one is waiting for this train + class.")
        return
    print(f"\nWaiting queue ({len(queue)} passenger(s), FIFO order):")
    for i, passenger in enumerate(queue, start=1):
        print(f"  {i}. {passenger['passenger_name']} (priority={passenger['priority']})")


def handle_summary():
    train_id = input("Enter train ID: ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    summary = get_train_booking_summary(int(train_id))
    print("\n--- Booking Summary ---")
    for status, count in summary.items():
        print(f" {status:10s}: {count}")


def main():
    actions = {
        "1": handle_book,
        "2": handle_cancel,
        "3": handle_check_pnr,
        "4": handle_history,
        "5": handle_waiting_queue,
        "6": handle_summary,
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
