"""
demo_ui_helpers_interactive.py
Interactive, menu-driven demo of ui_helpers.py.
"""

from ui_helpers import (
    print_welcome_screen,
    print_success,
    print_error,
    print_warning,
    print_info,
    set_theme,
    choose_theme_prompt,
    print_trains_table,
    print_seat_map_table,
    print_booking_summary,
    loading_bar,
    THEMES,
)
from train import get_all_trains, get_seat_map


def menu():
    print("\n" + "=" * 55)
    print("   RailEase - UI Helpers Demo")
    print("=" * 55)
    print("1. Show welcome screen")
    print("2. Change theme")
    print("3. Show sample success/error/warning messages")
    print("4. Show a real trains table (from the database)")
    print("5. Show a real seat map table (from the database)")
    print("6. Show a booking summary table")
    print("7. Run the loading bar")
    print("0. Exit")
    return input("Enter your choice: ").strip()


def handle_welcome():
    print_welcome_screen()


def handle_theme():
    choose_theme_prompt()


def handle_messages():
    print_success("This is a success message.")
    print_error("This is an error message.")
    print_warning("This is a warning message.")
    print_info("This is an info message.")


def handle_real_trains():
    trains = get_all_trains()
    print(f"\nShowing 10 of {len(trains)} trains:")
    print_trains_table(trains[:10])


def handle_real_seat_map():
    train_id = input("Enter train ID: ").strip()
    travel_class = input("Class (General/Sleeper/AC): ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    seat_map = get_seat_map(int(train_id), travel_class)
    if not seat_map:
        print("Invalid train ID or class.")
        return
    print_seat_map_table(seat_map)


def handle_booking_summary():
    confirmed = input("Confirmed count: ").strip()
    waiting = input("Waiting count: ").strip()
    cancelled = input("Cancelled count: ").strip()
    summary = {
        "Confirmed": int(confirmed) if confirmed.isdigit() else 0,
        "Waiting": int(waiting) if waiting.isdigit() else 0,
        "Cancelled": int(cancelled) if cancelled.isdigit() else 0,
    }
    print_booking_summary(summary)


def handle_loading():
    message = input("Loading message (or leave blank): ").strip() or "Loading"
    loading_bar(message, duration=1.5)
    print_success("Done!")


def main():
    actions = {
        "1": handle_welcome,
        "2": handle_theme,
        "3": handle_messages,
        "4": handle_real_trains,
        "5": handle_real_seat_map,
        "6": handle_booking_summary,
        "7": handle_loading,
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
