"""
ui_helpers.py - RailEase Ticket Booking System
Colors, banner, tables, theme, loading bar.
"""

import time
import sys

from pyfiglet import Figlet
from tabulate import tabulate

try:
    get_ipython()
    IN_NOTEBOOK = True
except NameError:
    IN_NOTEBOOK = False

if IN_NOTEBOOK:
    from IPython.display import display, HTML


RESET = "\033[0m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
LIGHTGREEN = "\033[92m"
LIGHTRED = "\033[91m"
WHITE = "\033[37m"

_HTML_COLORS = {
    CYAN: "#22d3ee",
    GREEN: "#22c55e",
    RED: "#ef4444",
    YELLOW: "#eab308",
    MAGENTA: "#d946ef",
    LIGHTGREEN: "#4ade80",
    LIGHTRED: "#f87171",
    WHITE: "#e5e7eb",
}


def _show(text):
    if not IN_NOTEBOOK:
        print(text)
        return

    html_text = text
    for code, hex_color in _HTML_COLORS.items():
        html_text = html_text.replace(code, f'<span style="color:{hex_color}">')
    html_text = html_text.replace(RESET, "</span>")
    display(HTML(f'<pre style="font-family:monospace; white-space:pre-wrap; margin:0;">{html_text}</pre>'))


THEMES = {
    "default": {"primary": CYAN, "success": GREEN, "error": RED, "warning": YELLOW},
    "sunset":  {"primary": MAGENTA, "success": YELLOW, "error": RED, "warning": LIGHTRED},
    "forest":  {"primary": GREEN, "success": LIGHTGREEN, "error": RED, "warning": YELLOW},
}

_current_theme = "default"


def set_theme(theme_name):
    global _current_theme
    if theme_name in THEMES:
        _current_theme = theme_name
        return True
    return False


def get_theme_colors():
    return THEMES[_current_theme]


def choose_theme_prompt():
    print("\nAvailable themes:", ", ".join(THEMES.keys()))
    choice = input("Choose a theme (or press Enter for default): ").strip().lower()
    if choice and set_theme(choice):
        print(f"Theme set to '{choice}'.")
    else:
        print("Using default theme.")


def print_banner(text="RailEase"):
    colors = get_theme_colors()
    fig = Figlet(font="slant")
    _show(colors["primary"] + fig.renderText(text) + RESET)


def print_welcome_screen(tagline="Book your journey, the smart way."):
    colors = get_theme_colors()
    print_banner("RailEase")
    width = 56
    box = (
        colors["primary"] + "+" + "-" * width + "+\n"
        + "|" + tagline.center(width) + "|\n"
        + "|" + f"Theme: {_current_theme}".center(width) + "|\n"
        + "+" + "-" * width + "+" + RESET
    )
    _show(box)


def print_success(message):
    _show(get_theme_colors()["success"] + "[OK] " + message + RESET)


def print_error(message):
    _show(get_theme_colors()["error"] + "[ERROR] " + message + RESET)


def print_warning(message):
    _show(get_theme_colors()["warning"] + "[WARNING] " + message + RESET)


def print_info(message):
    _show(get_theme_colors()["primary"] + message + RESET)


def _colorize_status(status):
    status_colors = {"On Time": GREEN, "Confirmed": GREEN,
                      "Delayed": YELLOW, "Waiting": YELLOW,
                      "Cancelled": RED}
    color = status_colors.get(status, WHITE)
    return color + status + RESET


def print_table(rows, headers):
    _show(tabulate(rows, headers=headers, tablefmt="fancy_grid"))


def print_trains_table(trains):
    rows = [
        [t["train_id"], t["train_name"], t["source"], t["destination"],
         t["distance"], _colorize_status(t["status"])]
        for t in trains
    ]
    print_table(rows, ["ID", "Name", "Source", "Destination", "Dist (km)", "Status"])


def print_seat_map_table(seat_map, seats_per_row=5):
    for i in range(0, len(seat_map), seats_per_row):
        row = seat_map[i:i + seats_per_row]
        labels = [seat for seat, _ in row]
        marks = [_colorize_status("Confirmed" if avail else "Cancelled") for _, avail in row]
        marks = [m.replace("Confirmed", "Available").replace("Cancelled", "Occupied") for m in marks]
        print_table([marks], labels)


def print_booking_summary(summary):
    rows = [[status, count] for status, count in summary.items()]
    print_table(rows, ["Status", "Count"])


def loading_bar(message="Loading", duration=1.2, width=30):
    steps = 20
    delay = duration / steps
    for i in range(steps + 1):
        filled = int(width * i / steps)
        bar = "#" * filled + "-" * (width - filled)
        percent = int(100 * i / steps)
        sys.stdout.write(f"\r{message} [{bar}] {percent}%")
        sys.stdout.flush()
        time.sleep(delay)
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: Welcome screen")
    print("=" * 60)
    print_welcome_screen()

    print("\n" + "=" * 60)
    print("TEST 2: Themed messages (default theme)")
    print("=" * 60)
    print_success("Booking confirmed.")
    print_error("Invalid PNR.")
    print_warning("Only 2 seats left.")
    print_info("Welcome to RailEase.")

    print("\n" + "=" * 60)
    print("TEST 3: Switch theme and repeat")
    print("=" * 60)
    set_theme("forest")
    print_welcome_screen("Now running the forest theme.")
    print_success("Theme changed to forest.")
    set_theme("default")

    print("\n" + "=" * 60)
    print("TEST 4: Trains table (with colored status)")
    print("=" * 60)
    sample_trains = [
        {"train_id": 1, "train_name": "Delhi Express 1", "source": "Delhi",
         "destination": "Ahmedabad", "distance": 200, "status": "On Time"},
        {"train_id": 2, "train_name": "Mumbai Superfast 2", "source": "Mumbai",
         "destination": "Jaipur", "distance": 237, "status": "Delayed"},
        {"train_id": 3, "train_name": "Kolkata Mail 3", "source": "Kolkata",
         "destination": "Lucknow", "distance": 274, "status": "Cancelled"},
    ]
    print_trains_table(sample_trains)

    print("\n" + "=" * 60)
    print("TEST 5: Seat map table")
    print("=" * 60)
    sample_seat_map = [("G1", True), ("G2", False), ("G3", True), ("G4", True), ("G5", False)]
    print_seat_map_table(sample_seat_map)

    print("\n" + "=" * 60)
    print("TEST 6: Booking summary table")
    print("=" * 60)
    print_booking_summary({"Confirmed": 10, "Waiting": 2, "Cancelled": 1})

    print("\n" + "=" * 60)
    print("TEST 7: Loading progress bar")
    print("=" * 60)
    loading_bar("Searching trains", duration=1.0)

    print("\n" + "=" * 60)
    print("TEST 8: Invalid theme name (should fail gracefully)")
    print("=" * 60)
    print(" set_theme('galaxy') ->", set_theme("galaxy"))
    print(" current theme is still:", _current_theme)
