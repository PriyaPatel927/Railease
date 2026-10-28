# RailEase — Run in VS Code (Windows)

## What this project is
This uploaded code is a Python command-line RailEase application. It is not a React website or FastAPI server. The main interactive application starts from `main.py`.

## Easiest setup
1. Install Python 3 from https://www.python.org/downloads/ and enable **Add Python to PATH** during installation.
2. Extract the `RailEase_VSCode` folder to a convenient location.
3. Open VS Code → **File → Open Folder** → select `RailEase_VSCode`.
4. In VS Code, open the folder's `setup_windows.bat` in File Explorer and double-click it once. It creates `.venv`, installs dependencies, and runs `database.py` to create `railease.db` and insert sample data.
5. After setup succeeds, double-click `run_windows.bat` to launch the app.

## Run from the VS Code terminal instead
Open **Terminal → New Terminal** in VS Code and run these commands from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python database.py
python main.py
```

If PowerShell blocks activation, skip activation and use the venv's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe database.py
.\.venv\Scripts\python.exe main.py
```

## Important
- Run `python database.py` before `python main.py` on the first run. `main.py` does not create the database itself.
- Keep all `.py` files together in this folder because the modules import each other.
- The database file `railease.db` is created in this folder. Do not delete it if you want to preserve your local bookings/users.
- Sample admin credentials defined in the code: `admin@railease.com` / `admin123`. This is for local demo/testing only; change it before any real deployment.
- `demo_*.py` files run separate terminal demos for individual modules; they are optional. For example: `python demo_train_interactive.py`.
- `print_all.py` prints database table contents and needs the database to exist first.
- `.gitignore` excludes the local database and generated tickets from Git, so local data is not accidentally uploaded.
