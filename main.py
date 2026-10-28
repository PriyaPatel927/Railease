from database import get_connection
from auth import signup, login, logout, is_admin_session, change_password, list_all_users
from train import CLASS_CONFIG, search_trains_by_route, calculate_fare, count_available_seats, get_food_menu, get_all_trains, get_train_route, display_seat_map
from booking import book_ticket, cancel_booking, get_booking_history, get_train_booking_summary, get_waiting_queue
from pnr import get_status_summary, search_pnr_by_passenger_name
from ticket import generate_ticket, generate_qr_code, generate_all_tickets_for_user
import ui_helpers as ui

session = None


def login_screen():
    global session
    print("\n1. Login\n2. Sign up\n0. Exit")
    choice = input("Choice: ").strip()

    if choice == "1":
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        ok, result = login(email, password)
        if ok:
            session = result
            ui.print_success(f"Welcome, {result['name']}!")
        else:
            ui.print_error(result)
        return True

    if choice == "2":
        name = input("Full name: ").strip()
        email = input("Email: ").strip()
        password = input("Password (6+ chars, 1 digit): ").strip()
        ok, message = signup(name, email, password)
        if not ok:
            ui.print_error(message)
            return True
        ui.print_success(message)
        ok, result = login(email, password)
        if ok:
            session = result
            ui.print_success(f"Logged in as {result['name']}.")
        return True

    return False


def search_trains():
    source = input("Source (blank to skip): ").strip()
    dest = input("Destination (blank to skip): ").strip()
    ui.loading_bar("Searching", duration=0.6)
    results = search_trains_by_route(source or None, dest or None)
    if not results:
        ui.print_warning("No trains found.")
    else:
        ui.print_trains_table(results)
    return results


def book_flow():
    results = search_trains()
    if not results:
        return
    train_id = input("Train ID: ").strip()
    if not train_id.isdigit():
        ui.print_error("Invalid train ID.")
        return
    train_id = int(train_id)

    rows = [[c, count_available_seats(train_id, c), f"Rs.{calculate_fare(train_id, c)}"] for c in CLASS_CONFIG]
    ui.print_table(rows, ["Class", "Seats Left", "Fare"])

    travel_class = input("Class: ").strip()
    passenger = input("Passenger name: ").strip() or session["name"]

    food = []
    menu = get_food_menu(train_id)
    if menu:
        for item, price in menu:
            print(f"  {item} - Rs.{price}")
        chosen = input("Food items, comma separated (blank to skip): ").strip()
        food = [x.strip() for x in chosen.split(",")] if chosen else []

    priority = input("Priority booking? (y/n): ").strip().lower() == "y"

    ok, info = book_ticket(session["user_id"], train_id, passenger, travel_class, food, priority)
    if not ok:
        ui.print_error(info["message"])
        return
    ui.print_success(info["message"])
    print(f"PNR {info['pnr']} | {info['status']} | seat {info['seat_number']} | Rs.{info['fare']}")


def cancel_flow():
    pnr = input("PNR: ").strip()
    hours = input("Hours before departure: ").strip()
    hours = float(hours) if hours.replace(".", "", 1).isdigit() else 0
    ok, info = cancel_booking(pnr, hours)
    if ok:
        ui.print_success(f"{info['message']} Refund: {info['refund_percent']}%")
    else:
        ui.print_error(info["message"])


def pnr_flow():
    print(get_status_summary(input("PNR: ").strip()))


def ticket_flow():
    pnr = input("PNR: ").strip()
    ok, result = generate_ticket(pnr)
    if not ok:
        ui.print_error(result)
        return
    ui.print_success(f"Saved: {result}")
    if input("Also make a QR code? (y/n): ").strip().lower() == "y":
        ok, qr = generate_qr_code(pnr)
        ui.print_success(f"QR saved: {qr}") if ok else ui.print_warning(qr)


def seat_map_flow():
    train_id = input("Train ID: ").strip()
    travel_class = input("Class (General/Sleeper/AC): ").strip()
    if not train_id.isdigit():
        ui.print_error("Invalid train ID.")
        return
    display_seat_map(int(train_id), travel_class)


def route_flow():
    train_id = input("Train ID: ").strip()
    if not train_id.isdigit():
        ui.print_error("Invalid train ID.")
        return
    route = get_train_route(int(train_id))
    print(" -> ".join(route) if route else "No route found.")


def change_password_flow():
    old = input("Current password: ").strip()
    new = input("New password (6+ chars, 1 digit): ").strip()
    ok, message = change_password(session["email"], old, new)
    ui.print_success(message) if ok else ui.print_error(message)


def bulk_ticket_flow():
    results = generate_all_tickets_for_user(session["user_id"])
    if not results:
        ui.print_warning("No bookings yet.")
        return
    for pnr, ok, path in results:
        print(f"  {pnr} -> {'saved: ' + path if ok else path}")


def theme_flow():
    ui.choose_theme_prompt()


def history_flow():
    rows = get_booking_history(session["user_id"])
    if not rows:
        ui.print_warning("No bookings yet.")
        return
    table = [[r["pnr"], r["passenger_name"], r["class"], r["seat_number"], r["status"], f"Rs.{r['fare']}"] for r in rows]
    ui.print_table(table, ["PNR", "Passenger", "Class", "Seat", "Status", "Fare"])


def user_menu():
    options = {"1": search_trains, "2": book_flow, "3": cancel_flow,
               "4": pnr_flow, "5": ticket_flow, "6": history_flow,
               "7": seat_map_flow, "8": route_flow, "9": change_password_flow,
               "10": bulk_ticket_flow, "11": theme_flow}
    while True:
        print(f"\n[{session['name']}]")
        print("1.Search 2.Book 3.Cancel 4.CheckPNR 5.Ticket 6.History")
        print("7.SeatMap 8.Route 9.ChangePassword 10.AllMyTickets 11.Theme 0.Logout")
        choice = input("Choice: ").strip()
        if choice == "0":
            logout(session["session_token"])
            return
        action = options.get(choice)
        action() if action else print("Invalid choice.")


def admin_overview():
    conn = get_connection()
    cur = conn.cursor()
    counts = {}
    for status in ("Confirmed", "Waiting", "Cancelled"):
        cur.execute("SELECT COUNT(*) c FROM Bookings WHERE status=?", (status,))
        counts[status] = cur.fetchone()["c"]
    cur.execute("SELECT SUM(fare) s FROM Bookings WHERE status='Confirmed'")
    revenue = cur.fetchone()["s"] or 0
    cur.execute("""SELECT t.train_name, COUNT(*) cnt FROM Bookings b
                   JOIN Trains t ON b.train_id = t.train_id
                   GROUP BY b.train_id ORDER BY cnt DESC LIMIT 1""")
    top = cur.fetchone()
    conn.close()

    rows = [["Confirmed", counts["Confirmed"]], ["Waiting", counts["Waiting"]],
            ["Cancelled", counts["Cancelled"]], ["Revenue", f"Rs.{revenue}"],
            ["Most booked train", top["train_name"] if top else "N/A"]]
    ui.print_table(rows, ["Metric", "Value"])


def admin_train_summary():
    train_id = input("Train ID: ").strip()
    if train_id.isdigit():
        ui.print_booking_summary(get_train_booking_summary(int(train_id)))


def admin_find_passenger():
    results = search_pnr_by_passenger_name(input("Passenger name: ").strip())
    if not results:
        ui.print_warning("No matches.")
        return
    rows = [[pnr, b["passenger_name"], b["status"], b["train_id"]] for pnr, b in results]
    ui.print_table(rows, ["PNR", "Passenger", "Status", "Train ID"])


def admin_waiting_queue():
    train_id = input("Train ID: ").strip()
    travel_class = input("Class: ").strip()
    if not train_id.isdigit():
        ui.print_error("Invalid train ID.")
        return
    queue = get_waiting_queue(int(train_id), travel_class)
    if not queue:
        ui.print_warning("No one waiting.")
        return
    for i, p in enumerate(queue, start=1):
        print(f"  {i}. {p['passenger_name']} (priority={p['priority']})")


def admin_list_users():
    ok, result = list_all_users(session["email"])
    if not ok:
        ui.print_error(result)
        return
    ui.print_table(result, ["Name", "Email", "Role"])


def admin_menu():
    options = {"1": admin_overview, "2": admin_train_summary, "3": admin_find_passenger,
               "4": lambda: ui.print_trains_table(get_all_trains()[:15]),
               "5": admin_waiting_queue, "6": admin_list_users, "7": theme_flow}
    while True:
        print(f"\n[Admin: {session['name']}]")
        print("1.Overview 2.TrainSummary 3.FindPassenger 4.AllTrains")
        print("5.WaitingQueue 6.AllUsers 7.Theme 0.Logout")
        choice = input("Choice: ").strip()
        if choice == "0":
            logout(session["session_token"])
            return
        action = options.get(choice)
        action() if action else print("Invalid choice.")


def run():
    global session
    ui.print_welcome_screen()
    while True:
        if session is None:
            if not login_screen():
                print("Goodbye!")
                return
            continue
        if is_admin_session(session["session_token"]):
            admin_menu()
        else:
            user_menu()
        session = None


if __name__ == "__main__":
    run()
