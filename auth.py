"""
auth.py - RailEase Ticket Booking System
Signup, login, sessions, and account management.
"""

import re
import hashlib
import secrets
import time

from database import get_connection


# config

MAX_FAILED_ATTEMPTS = 3          # after this many wrong passwords, lock the account temporarily
LOCKOUT_SECONDS = 60              # how long a locked account stays locked
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


# in-memory hash tables

failed_attempts = {}   # email -> {"count": int, "locked_until": timestamp or None}
active_sessions = {}   # session_token -> {"user_id", "name", "email", "role", "login_time"}


# password hashing

def hash_password(plain_password, salt="railease_static_salt"):
    salted = (salt + plain_password).encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def verify_password(plain_password, hashed_password):
    return hash_password(plain_password) == hashed_password


# validation

def is_valid_email(email):
    return bool(EMAIL_REGEX.match(email))


def is_strong_password(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not any(ch.isdigit() for ch in password):
        return False, "Password must contain at least one digit."
    return True, "OK"


# load users into a dict

def load_users_dict():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, password, role FROM Users")
    rows = cur.fetchall()
    conn.close()

    users_dict = {}
    for row in rows:
        users_dict[row["email"]] = {
            "user_id": row["user_id"],
            "name": row["name"],
            "password": row["password"],   # stored as a SHA-256 hash
            "role": row["role"],
        }
    return users_dict


def find_user_by_id(user_id):
    users_dict = load_users_dict()
    for email, data in users_dict.items():
        if data["user_id"] == user_id:
            return email, data
    return None, None


# lockout helpers

def _is_locked(email):
    record = failed_attempts.get(email)
    if not record or record["locked_until"] is None:
        return False
    if time.time() >= record["locked_until"]:
        failed_attempts[email] = {"count": 0, "locked_until": None}
        return False
    return True


def _register_failed_attempt(email):
    record = failed_attempts.get(email, {"count": 0, "locked_until": None})
    record["count"] += 1
    if record["count"] >= MAX_FAILED_ATTEMPTS:
        record["locked_until"] = time.time() + LOCKOUT_SECONDS
    failed_attempts[email] = record


def _reset_failed_attempts(email):
    failed_attempts[email] = {"count": 0, "locked_until": None}


# signup

def signup(name, email, password, role="user"):
    name = name.strip()
    email = email.strip().lower()

    if not name:
        return False, "Signup failed: name cannot be empty."

    if not is_valid_email(email):
        return False, "Signup failed: email format looks invalid."

    strong, reason = is_strong_password(password)
    if not strong:
        return False, f"Signup failed: {reason}"

    users_dict = load_users_dict()
    if email in users_dict:  # O(1) duplicate check
        return False, "Signup failed: an account with this email already exists."

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, hash_password(password), role)
        )
        conn.commit()
        return True, f"Signup successful! Welcome, {name}."
    except Exception as e:
        return False, f"Signup failed: {e}"
    finally:
        conn.close()


# login / logout

def login(email, password):
    email = email.strip().lower()

    if _is_locked(email):
        return False, "Account temporarily locked due to too many failed attempts. Try again later."

    users_dict = load_users_dict()          # O(n) to build, O(1) per lookup after
    user = users_dict.get(email)             # --- hashing in action ---

    if user is None:
        _register_failed_attempt(email)
        return False, "Login failed: no account found with this email."

    if not verify_password(password, user["password"]):
        _register_failed_attempt(email)
        return False, "Login failed: incorrect password."

    _reset_failed_attempts(email)

    token = secrets.token_hex(16)
    active_sessions[token] = {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": email,
        "role": user["role"],
        "login_time": time.time(),
    }

    return True, {
        "session_token": token,
        "user_id": user["user_id"],
        "name": user["name"],
        "email": email,
        "role": user["role"],
    }


def logout(session_token):
    if session_token in active_sessions:
        del active_sessions[session_token]
        return True, "Logged out successfully."
    return False, "Invalid or already-expired session."


def get_session(session_token):
    return active_sessions.get(session_token)


def is_session_valid(session_token):
    return session_token in active_sessions


# admin helpers

def is_admin(email):
    users_dict = load_users_dict()
    user = users_dict.get(email.strip().lower())
    return user is not None and user["role"] == "admin"


def is_admin_session(session_token):
    session = active_sessions.get(session_token)
    return session is not None and session["role"] == "admin"


# account management

def change_password(email, old_password, new_password):
    email = email.strip().lower()
    users_dict = load_users_dict()
    user = users_dict.get(email)

    if user is None:
        return False, "No account found with this email."
    if not verify_password(old_password, user["password"]):
        return False, "Old password is incorrect."

    strong, reason = is_strong_password(new_password)
    if not strong:
        return False, reason

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE Users SET password = ? WHERE email = ?",
        (hash_password(new_password), email)
    )
    conn.commit()
    conn.close()
    return True, "Password updated successfully."


def list_all_users(requesting_email):
    if not is_admin(requesting_email):
        return False, "Access denied: admin privileges required."

    users_dict = load_users_dict()
    user_list = [
        (data["name"], email, data["role"])
        for email, data in users_dict.items()
    ]
    return True, user_list


# cli helpers

def signup_prompt():
    print("\n--- Sign Up ---")
    name = input("Full name: ")
    email = input("Email: ")
    password = input("Password (min 6 chars, at least 1 digit): ")
    success, message = signup(name, email, password)
    print(message)
    return success


def login_prompt():
    print("\n--- Login ---")
    email = input("Email: ")
    password = input("Password: ")
    success, result = login(email, password)
    print(result if not success else f"Login successful! Welcome, {result['name']}.")
    return result if success else None


# tests

if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: Load users into dictionary (hash table)")
    print("=" * 60)
    users_dict = load_users_dict()
    print(f"Loaded {len(users_dict)} users into the dictionary.")

    print("\n" + "=" * 60)
    print("TEST 2: Password hashing")
    print("=" * 60)
    h1 = hash_password("mypassword1")
    h2 = hash_password("mypassword1")
    h3 = hash_password("different1")
    print(" Same password hashed twice -> equal hashes:", h1 == h2)
    print(" Different password -> different hash:", h1 != h3)

    print("\n" + "=" * 60)
    print("TEST 3: Signup validation (weak password, bad email)")
    print("=" * 60)
    print(" weak password ->", signup("Weak User", "weak@railease.com", "abc"))
    print(" bad email     ->", signup("Bad Email", "not-an-email", "abc123"))

    print("\n" + "=" * 60)
    print("TEST 4: Successful signup + duplicate signup blocked")
    print("=" * 60)
    print(" first signup  ->", signup("Test Student", "teststudent2@railease.com", "test1234"))
    print(" duplicate try ->", signup("Test Student", "teststudent2@railease.com", "test1234"))

    print("\n" + "=" * 60)
    print("TEST 5: Login with the new account (creates a session)")
    print("=" * 60)
    success, result = login("teststudent2@railease.com", "test1234")
    print(" success:", success)
    print(" result :", result)
    session_token = result["session_token"] if success else None

    print("\n" + "=" * 60)
    print("TEST 6: Session validity + logout")
    print("=" * 60)
    print(" is_session_valid (before logout):", is_session_valid(session_token))
    print(" logout()                        :", logout(session_token))
    print(" is_session_valid (after logout) :", is_session_valid(session_token))

    print("\n" + "=" * 60)
    print("TEST 7: Failed login lockout (wrong password 3 times)")
    print("=" * 60)
    for attempt in range(1, 4):
        success, message = login("teststudent2@railease.com", "wrongpass")
        print(f" attempt {attempt}: success={success}, message={message}")
    success, message = login("teststudent2@railease.com", "test1234")
    print(" attempt 4 (correct password, but locked):", success, "-", message)

    print("\n" + "=" * 60)
    print("TEST 8: Admin check")
    print("=" * 60)
    print(" is_admin('admin@railease.com')       ->", is_admin("admin@railease.com"))
    print(" is_admin('teststudent2@railease.com') ->", is_admin("teststudent2@railease.com"))

    print("\n" + "=" * 60)
    print("TEST 9: Admin-only user listing (access control)")
    print("=" * 60)
    success, result = list_all_users("admin@railease.com")
    print(" as admin -> success:", success, "| total users:", len(result) if success else result)
    success, result = list_all_users("teststudent2@railease.com")
    print(" as normal user -> success:", success, "| message:", result)

    print("\n" + "=" * 60)
    print("TEST 10: Change password")
    print("=" * 60)
    print(" wrong old password ->", change_password("teststudent2@railease.com", "notright", "newpass1"))
    print(" correct old password ->", change_password("teststudent2@railease.com", "test1234", "newpass1"))
    print(" login attempt with NEW password ->", login("teststudent2@railease.com", "newpass1"))
