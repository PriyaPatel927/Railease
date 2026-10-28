"""
demo_auth_interactive.py
Interactive demo of auth.py's signup_prompt and login_prompt.
"""

from auth import signup_prompt, login_prompt

print("Welcome to RailEase - Interactive Auth Demo")
print("1. Sign up")
print("2. Login")
choice = input("Enter choice (1 or 2): ")

if choice == "1":
    signup_prompt()
elif choice == "2":
    session = login_prompt()
    if session:
        print("\nYou are now logged in as:", session["name"], f"({session['role']})")
    else:
        print("\nLogin did not succeed.")
else:
    print("Invalid choice.")
