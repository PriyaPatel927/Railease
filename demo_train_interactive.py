"""
demo_train_interactive.py
Interactive menu-driven demo of train.py.
"""

from train import (
    search_trains_by_route,
    get_train_route,
    display_seat_map,
    count_available_seats,
    calculate_fare,
    get_food_menu,
    get_train_status,
    display_train_table,
    get_all_trains,
    CLASS_CONFIG,
)


def menu():
    print("\n" + "=" * 50)
    print("   RailEase - Train Module Demo")
    print("=" * 50)
    print("1. Search trains by source and destination")
    print("2. View a train's route (stations)")
    print("3. View seat map for a train")
    print("4. Calculate fare for a train")
    print("5. View food menu for a train")
    print("6. Check train status")
    print("7. List all trains (table view)")
    print("0. Exit")
    return input("Enter your choice: ").strip()


def handle_search():
    source = input("Enter source station (leave blank to skip): ").strip()
    destination = input("Enter destination station (leave blank to skip): ").strip()
    results = search_trains_by_route(
        source=source if source else None,
        destination=destination if destination else None,
    )
    if not results:
        print("\nNo trains found for that search.")
        return
    print(f"\nFound {len(results)} train(s):")
    display_train_table(results)


def handle_route():
    train_id = input("Enter train ID: ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    route = get_train_route(int(train_id))
    if not route:
        print("No route found - check the train ID.")
        return
    print("\nRoute:", " -> ".join(route))


def handle_seat_map():
    train_id = input("Enter train ID: ").strip()
    print(f"Available classes: {list(CLASS_CONFIG.keys())}")
    travel_class = input("Enter class (General/Sleeper/AC): ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    display_seat_map(int(train_id), travel_class)
    print("Available seats:", count_available_seats(int(train_id), travel_class))


def handle_fare():
    train_id = input("Enter train ID: ").strip()
    print(f"Available classes: {list(CLASS_CONFIG.keys())}")
    travel_class = input("Enter class (General/Sleeper/AC): ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    fare = calculate_fare(int(train_id), travel_class)
    if fare is None:
        print("Invalid train ID or class.")
    else:
        print(f"\nFare for train {train_id} ({travel_class}): Rs.{fare}")


def handle_food_menu():
    train_id = input("Enter train ID: ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    menu_items = get_food_menu(int(train_id))
    if not menu_items:
        print("\nThis train has no pantry service.")
        return
    print("\nFood Menu:")
    for item, price in menu_items:
        print(f"  {item:15s} - Rs.{price}")


def handle_status():
    train_id = input("Enter train ID: ").strip()
    if not train_id.isdigit():
        print("Please enter a valid numeric train ID.")
        return
    status = get_train_status(int(train_id))
    print(f"\nStatus: {status}" if status else "\nTrain not found.")


def handle_list_all():
    trains = get_all_trains()
    print(f"\nTotal trains: {len(trains)}\n")
    display_train_table(trains[:15])
    print("... (showing first 15 of", len(trains), ")")


def main():
    actions = {
        "1": handle_search,
        "2": handle_route,
        "3": handle_seat_map,
        "4": handle_fare,
        "5": handle_food_menu,
        "6": handle_status,
        "7": handle_list_all,
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
