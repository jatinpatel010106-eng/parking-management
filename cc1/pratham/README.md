# Parking Vehicle Management Website

A beginner-friendly full-stack **Parking Vehicle Management System** built using:
- Frontend: HTML, CSS, JavaScript (+ Bootstrap)
- Backend: Python Flask
- Database: MongoDB (via `pymongo`)

---

## Project Structure

```text
parking-management/
│
├── app.py
├── requirements.txt
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
│
└── database/
    ├── mongo_config.py
    └── seed_data.py
```

---

## Features

### 1) Authentication
- User registration
- User login
- Password hashing (`werkzeug.security`)
- Session-based auth
- Logout
- Default admin user bootstrapped:
  - **Email**: `admin@parking.com`
  - **Password**: `admin123`

### 2) Parking Management
- Dashboard after login
- Add vehicle entry (owner, number, type, auto entry time)
- Exit vehicle with parking duration and fee calculation
- View all currently parked vehicles
- Search vehicle by number
- Delete vehicle record

### 3) Admin Features
- Admin login (same login page; role-based access)
- View all users
- View parking history
- Total earnings summary

---

## MongoDB Collections

### `users`
- `username`
- `email`
- `password_hash`
- `role`
- `created_at`

### `vehicles`
- `vehicle_number`
- `owner_name`
- `vehicle_type`
- `entry_time`
- `status`
- `exit_time` (after exit)
- `duration_hours` (after exit)
- `total_fee` (after exit)

### `parking_history`
- `vehicle_number`
- `owner_name`
- `vehicle_type`
- `entry_time`
- `exit_time`
- `duration_hours`
- `total_fee`

---

## Installation & Setup (VS Code)

### 1. Clone / open project
Open this project folder in VS Code.

### 2. Create virtual environment
```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**
```bash
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3. Install requirements
```bash
pip install -r requirements.txt
```

### 4. MongoDB setup
1. Install MongoDB Community Server.
2. Start MongoDB service.
3. Default URI used by app: `mongodb://localhost:27017/`

Optional environment variables:
```bash
export MONGO_URI="mongodb://localhost:27017/"
export MONGO_DB_NAME="parking_management"
```

### 5. Seed dummy data (optional)
```bash
python database/seed_data.py
```

### 6. Run Flask app
```bash
python app.py
```

### 7. Open in browser
```text
http://127.0.0.1:5000
```

---

## API Endpoints

### Auth
- `POST /register`
- `POST /login`
- `GET /logout`

### Parking
- `POST /add_vehicle`
- `POST /exit_vehicle`
- `GET /vehicles?number=<query>`
- `DELETE /vehicles/<vehicle_id>`

### Admin
- `GET /admin/users`
- `GET /admin/history`

---

## API Flow (Brief)

1. User registers via `/register`.
2. User logs in via `/login`.
3. Flask stores session (`user_id`, `role`) after successful login.
4. Dashboard uses AJAX to call parking endpoints:
   - `/add_vehicle` creates active parked entry.
   - `/vehicles` fetches active vehicles.
   - `/exit_vehicle` closes parking session and logs data to `parking_history`.
5. Admin-only endpoints validate role before returning users/history/earnings.

---

## UI Screenshot Description

- **Home (`index.html`)**: Gradient hero with app title and Login/Register buttons.
- **Login/Register**: Centered card-based forms with validation messages.
- **Dashboard**: Modern cards for vehicle entry, exit, search, parked vehicle table, and admin panel widgets for users/history.

