"""
train.py - RailEase Ticket Booking System
Search, routes, seat maps, fare, sorting, comparisons.
"""

from database import get_connection


# class settings

CLASS_CONFIG = {
    "General": {"seats": 20, "multiplier": 1.0, "prefix": "G"},
    "Sleeper": {"seats": 30, "multiplier": 1.8, "prefix": "S"},
    "AC":      {"seats": 10, "multiplier": 3.0, "prefix": "A"},
}

BASE_RATE_PER_KM = 0.5  # currency units per km, before class multiplier


# basic lookups

def get_all_trains():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Trains")
    trains = [dict(row) for row in cur.fetchall()]
    conn.close()
    return trains


def get_train_by_id(train_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM Trains WHERE train_id = ?", (train_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# searching

def search_trains_by_route(source=None, destination=None):
    all_trains = get_all_trains()
    results = []

    for train in all_trains:
        source_ok = True
        destination_ok = True

        if source:
            source_ok = source.strip().lower() in train["source"].lower()
        if destination:
            destination_ok = destination.strip().lower() in train["destination"].lower()

        if source_ok and destination_ok:
            results.append(train)

    return results


def search_trains_by_name(keyword):
    all_trains = get_all_trains()
    keyword = keyword.strip().lower()
    return [t for t in all_trains if keyword in t["train_name"].lower()]


def get_trains_via_station(station_name):
    station_name = station_name.strip().lower()
    matching = []
    for train in get_all_trains():
        route = [s.lower() for s in get_train_route(train["train_id"])]
        if station_name in route:
            matching.append(train)
    return matching


def filter_trains_by_status(status):
    return [t for t in get_all_trains() if t["status"].lower() == status.lower()]


# sorting

def bubble_sort_trains_by_distance(trains):
    arr = trains.copy()  # don't mutate the caller's list
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j]["distance"] > arr[j + 1]["distance"]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break  # already sorted, stop early
    return arr


def insertion_sort_trains_by_name(trains):
    arr = trains.copy()
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j]["train_name"].lower() > key["train_name"].lower():
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr


def binary_search_by_distance(sorted_trains, target_distance):
    low, high = 0, len(sorted_trains) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_distance = sorted_trains[mid]["distance"]
        if mid_distance == target_distance:
            return sorted_trains[mid]
        elif mid_distance < target_distance:
            low = mid + 1
        else:
            high = mid - 1
    return None


# routes

def get_train_route(train_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT station_name FROM Stations WHERE train_id = ? ORDER BY station_order",
        (train_id,)
    )
    route = [row["station_name"] for row in cur.fetchall()]
    conn.close()
    return route


def get_next_station(train_id, current_station):
    route = get_train_route(train_id)
    current_station = current_station.strip().lower()
    normalized = [s.lower() for s in route]

    if current_station not in normalized:
        return None  # station not on this train's route

    index = normalized.index(current_station)
    if index == len(route) - 1:
        return None  # already at the last station
    return route[index + 1]


def is_valid_route(train_id, source, destination):
    route = [s.lower() for s in get_train_route(train_id)]
    source, destination = source.strip().lower(), destination.strip().lower()

    if source not in route or destination not in route:
        return False
    return route.index(source) < route.index(destination)


# seat map

def _generate_seat_labels(travel_class):
    config = CLASS_CONFIG.get(travel_class)
    if not config:
        return []
    return [f"{config['prefix']}{i}" for i in range(1, config["seats"] + 1)]


def get_occupied_seats(train_id, travel_class):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT seat_number FROM Bookings WHERE train_id = ? AND class = ? AND status = 'Confirmed'",
        (train_id, travel_class)
    )
    occupied = [row["seat_number"] for row in cur.fetchall()]
    conn.close()
    return occupied


def get_seat_map(train_id, travel_class):
    if travel_class not in CLASS_CONFIG:
        return None

    all_seats = _generate_seat_labels(travel_class)
    occupied = set(get_occupied_seats(train_id, travel_class))  # O(1) membership check

    return [(seat, seat not in occupied) for seat in all_seats]


def display_seat_map(train_id, travel_class, seats_per_row=5):
    seat_map = get_seat_map(train_id, travel_class)
    if seat_map is None:
        print(f"Invalid class '{travel_class}'. Choose from {list(CLASS_CONFIG.keys())}.")
        return

    print(f"\nSeat map for train {train_id} - {travel_class} class:")
    for i in range(0, len(seat_map), seats_per_row):
        row = seat_map[i:i + seats_per_row]
        print("  ", "  ".join(seat for seat, _ in row))
        print("  ", "  ".join(("OK" if available else "X ") for _, available in row))
        print()


def count_available_seats(train_id, travel_class):
    seat_map = get_seat_map(train_id, travel_class)
    if seat_map is None:
        return 0
    return sum(1 for _, available in seat_map if available)


def get_first_available_seat(train_id, travel_class):
    seat_map = get_seat_map(train_id, travel_class)
    if not seat_map:
        return None
    for seat, available in seat_map:
        if available:
            return seat
    return None


def get_seat_availability_summary(train_id):
    return {cls: count_available_seats(train_id, cls) for cls in CLASS_CONFIG}


# fare

def calculate_fare(train_id, travel_class):
    train = get_train_by_id(train_id)
    config = CLASS_CONFIG.get(travel_class)

    if train is None or config is None:
        return None

    fare = train["distance"] * BASE_RATE_PER_KM * config["multiplier"]
    return round(fare, 2)


def get_all_fares(train_id):
    return {cls: calculate_fare(train_id, cls) for cls in CLASS_CONFIG}


def get_cheapest_train(source, destination, travel_class="General"):
    matches = search_trains_by_route(source=source, destination=destination)
    if not matches:
        return None

    cheapest = None
    cheapest_fare = None
    for train in matches:
        fare = calculate_fare(train["train_id"], travel_class)
        if cheapest_fare is None or fare < cheapest_fare:
            cheapest_fare = fare
            cheapest = train

    return cheapest, cheapest_fare


# food menu

def get_food_menu(train_id):
    train = get_train_by_id(train_id)
    if train is None or not train["has_pantry"]:
        return []

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT item_name, price FROM Food_Menu WHERE train_id = ?", (train_id,))
    menu = [(row["item_name"], row["price"]) for row in cur.fetchall()]
    conn.close()
    return menu


# status

def get_train_status(train_id):
    train = get_train_by_id(train_id)
    return train["status"] if train else None


# profile / comparison / display

def get_full_train_details(train_id):
    train = get_train_by_id(train_id)
    if train is None:
        return None

    details = dict(train)
    details["route"] = get_train_route(train_id)
    details["fares"] = get_all_fares(train_id)
    details["seat_availability"] = get_seat_availability_summary(train_id)
    details["food_menu"] = get_food_menu(train_id)
    return details


def compare_two_trains(train_id_1, train_id_2):
    t1 = get_full_train_details(train_id_1)
    t2 = get_full_train_details(train_id_2)
    if t1 is None or t2 is None:
        return None

    return {
        "train_1": {"name": t1["train_name"], "distance": t1["distance"],
                    "status": t1["status"], "fares": t1["fares"]},
        "train_2": {"name": t2["train_name"], "distance": t2["distance"],
                    "status": t2["status"], "fares": t2["fares"]},
    }


def display_train_table(trains):
    header = f"{'ID':<4}{'Name':<28}{'Source':<12}{'Destination':<14}{'Dist':<7}{'Status':<10}"
    print(header)
    print("-" * len(header))
    for t in trains:
        name = t["train_name"] if len(t["train_name"]) <= 26 else t["train_name"][:23] + "..."
        print(f"{t['train_id']:<4}{name:<28}{t['source']:<12}"
              f"{t['destination']:<14}{t['distance']:<7}{t['status']:<10}")


# tests

if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: Get all trains (count check)")
    print("=" * 60)
    all_trains = get_all_trains()
    print(f"Total trains loaded: {len(all_trains)}")

    print("\n" + "=" * 60)
    print("TEST 2: Search by source = 'Delhi'")
    print("=" * 60)
    results = search_trains_by_route(source="Delhi")
    print(f"Found {len(results)} trains from Delhi. First 3:")
    for t in results[:3]:
        print(" ", t["train_name"], "->", t["destination"])

    print("\n" + "=" * 60)
    print("TEST 3: Search by source AND destination")
    print("=" * 60)
    sample = all_trains[0]
    results = search_trains_by_route(source=sample["source"], destination=sample["destination"])
    print(f"Search '{sample['source']}' -> '{sample['destination']}' found {len(results)} train(s).")

    print("\n" + "=" * 60)
    print("TEST 4: Search trains passing through a specific station")
    print("=" * 60)
    sample_route = get_train_route(all_trains[0]["train_id"])
    midpoint = sample_route[1] if len(sample_route) > 1 else sample_route[0]
    via_results = get_trains_via_station(midpoint)
    print(f"Trains passing through '{midpoint}': {len(via_results)} found.")

    print("\n" + "=" * 60)
    print("TEST 5: Get route (ordered station list) for train_id = 1")
    print("=" * 60)
    route = get_train_route(1)
    print(" Route:", route)

    print("\n" + "=" * 60)
    print("TEST 6: Next station logic")
    print("=" * 60)
    if len(route) >= 2:
        print(f" Next station after '{route[0]}':", get_next_station(1, route[0]))
        print(f" Next station after '{route[-1]}' (should be None):", get_next_station(1, route[-1]))

    print("\n" + "=" * 60)
    print("TEST 7: Valid vs invalid route check")
    print("=" * 60)
    if len(route) >= 2:
        print(f" is_valid_route({route[0]} -> {route[-1]}):", is_valid_route(1, route[0], route[-1]))
        print(f" is_valid_route({route[-1]} -> {route[0]}) [reversed, should be False]:",
              is_valid_route(1, route[-1], route[0]))

    print("\n" + "=" * 60)
    print("TEST 8: Seat map for train_id = 1, General class")
    print("=" * 60)
    display_seat_map(1, "General")

    print("=" * 60)
    print("TEST 9: Available seat count + first available seat")
    print("=" * 60)
    print(" Available General seats:", count_available_seats(1, "General"))
    print(" First available seat    :", get_first_available_seat(1, "General"))

    print("\n" + "=" * 60)
    print("TEST 10: Fare calculation for train_id = 1, all classes")
    print("=" * 60)
    for cls in CLASS_CONFIG:
        print(f" {cls:8s} fare:", calculate_fare(1, cls))

    print("\n" + "=" * 60)
    print("TEST 11: Bubble sort trains by distance (first 5 shown)")
    print("=" * 60)
    sorted_by_distance = bubble_sort_trains_by_distance(all_trains)
    for t in sorted_by_distance[:5]:
        print(f"  {t['train_name']:<20} distance={t['distance']}")
    print(" Sorted ascending check:",
          all(sorted_by_distance[i]["distance"] <= sorted_by_distance[i + 1]["distance"]
              for i in range(len(sorted_by_distance) - 1)))

    print("\n" + "=" * 60)
    print("TEST 12: Insertion sort trains by name (first 5 shown)")
    print("=" * 60)
    sorted_by_name = insertion_sort_trains_by_name(all_trains)
    for t in sorted_by_name[:5]:
        print(f"  {t['train_name']}")

    print("\n" + "=" * 60)
    print("TEST 13: Binary search by distance (bonus, needs sorted list)")
    print("=" * 60)
    target = sorted_by_distance[len(sorted_by_distance) // 2]["distance"]
    found = binary_search_by_distance(sorted_by_distance, target)
    print(f" Searching for distance={target} -> found:",
          found["train_name"] if found else "Not found")

    print("\n" + "=" * 60)
    print("TEST 14: Food menu for train_id = 1")
    print("=" * 60)
    menu = get_food_menu(1)
    if menu:
        for item, price in menu:
            print(f"  {item:15s} - Rs.{price}")
    else:
        print("  No pantry service on this train.")

    print("\n" + "=" * 60)
    print("TEST 15: Full train details (combined profile)")
    print("=" * 60)
    details = get_full_train_details(1)
    print(" Name           :", details["train_name"])
    print(" Route          :", details["route"])
    print(" Fares          :", details["fares"])
    print(" Seat available :", details["seat_availability"])
    print(" Status         :", details["status"])

    print("\n" + "=" * 60)
    print("TEST 16: Compare two trains (train_id 1 vs 2)")
    print("=" * 60)
    comparison = compare_two_trains(1, 2)
    print(" Train 1:", comparison["train_1"])
    print(" Train 2:", comparison["train_2"])

    print("\n" + "=" * 60)
    print("TEST 17: Display a formatted train table (first 5 trains)")
    print("=" * 60)
    display_train_table(all_trains[:5])

    print("\n" + "=" * 60)
    print("TEST 18: Filter trains by status")
    print("=" * 60)
    delayed = filter_trains_by_status("Delayed")
    cancelled = filter_trains_by_status("Cancelled")
    print(f" Delayed trains  : {len(delayed)}")
    print(f" Cancelled trains: {len(cancelled)}")

    print("\n" + "=" * 60)
    print("TEST 19: Cheapest train for a route")
    print("=" * 60)
    cheapest, fare = get_cheapest_train(sample["source"], sample["destination"], "Sleeper")
    if cheapest:
        print(f" Cheapest Sleeper option: {cheapest['train_name']} - Rs.{fare}")
    else:
        print(" No trains found for that route.")
