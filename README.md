# Women's Safety Emergency Alert System

A full-stack web application that helps women quickly request emergency
assistance, share their live location with trusted contacts, and access
safety resources.

- **Frontend:** React + Vite, React Router, Axios, Leaflet/OpenStreetMap, Lucide icons
- **Backend:** Python + Flask, Flask-SQLAlchemy, SQLite, JWT (PyJWT), Werkzeug password hashing, Twilio SMS
- **Database:** SQLite (file-based by default, in-memory for tests)

> ⚠️ **Important:** When Twilio is configured, triggering SOS sends a real SMS to
> your trusted contacts with your name, timestamp, GPS coordinates, and a
> Google Maps link. The app still does **not** replace calling emergency
> services — always call **112** directly in a real emergency. If Twilio is not
> configured, alerts are still recorded and each notification shows as failed
> with a clear "not configured" reason.

---

## Project structure

```
women-safety-system/
├── backend/
│   ├── app.py              # Flask app factory + entry point
│   ├── config.py           # Environment-based configuration
│   ├── extensions.py       # Shared db/cors instances
│   ├── security.py         # JWT helpers + token_required guard
│   ├── notifications.py    # Twilio SMS sending + delivery helpers
│   ├── models.py           # User, TrustedContact, EmergencyAlert, Location, NotificationLog
│   ├── seed.py             # Create demo account + sample contacts
│   ├── routes/             # Blueprint-based REST endpoints
│   │   ├── auth.py
│   │   ├── contacts.py
│   │   ├── alerts.py
│   │   ├── location.py
│   │   └── twilio.py        # SMS delivery status callback webhook
│   ├── tests/              # test_api.py + test_notifications.py (pytest)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/     # Navbar, SOSButton, LocationMap, etc.
│   │   ├── pages/         # Login, Register, Dashboard, Contacts, Resources, Alerts
│   │   ├── services/      # Axios client + geolocation helpers
│   │   ├── context/       # AuthContext
│   │   ├── styles/        # Global theme CSS
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/shield.svg
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── .env.example
└── README.md
```

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- A modern browser with geolocation support

---

## Backend setup

```bash
cd women-safety-system/backend

# 1) (Optional but recommended) create and activate a virtual environment
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure environment variables
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
# Then edit .env and set strong SECRET_KEY / JWT_SECRET_KEY values.

# 4) (Optional) create the demo account
python seed.py
# -> demo@womensafety.org / demo1234

# 5) Run the API server
python app.py
# The API is available at http://localhost:5000
```

The SQLite database is created automatically at `backend/instance/womens_safety.db`
on first run.

### API endpoints

| Method | Endpoint                        | Auth | Description                          |
| ------ | ------------------------------- | ---- | ------------------------------------ |
| POST   | `/api/auth/register`            | -    | Register a new user, returns JWT     |
| POST   | `/api/auth/login`               | -    | Log in, returns JWT                  |
| GET    | `/api/auth/me`                  | JWT  | Current user profile                 |
| GET    | `/api/contacts`                 | JWT  | List trusted contacts                |
| POST   | `/api/contacts`                 | JWT  | Add a contact                        |
| PUT    | `/api/contacts/{id}`            | JWT  | Update a contact                     |
| DELETE | `/api/contacts/{id}`            | JWT  | Delete a contact                     |
| POST   | `/api/alerts`                   | JWT  | Create an emergency alert + send SMS to contacts |
| GET    | `/api/alerts`                   | JWT  | List alerts with notification status (newest first) |
| GET    | `/api/alerts/{id}`              | JWT  | Get one alert + its notification status           |
| GET    | `/api/alerts/{id}/notifications` | JWT  | Delivery status of SMS notifications for an alert |
| POST   | `/api/alerts/{id}/notifications/retry` | JWT | Re-send failed/pending SMS notifications |
| PATCH  | `/api/alerts/{id}/status`       | JWT  | Update alert status                  |
| POST   | `/api/location`                 | JWT  | Save current location                |
| GET    | `/api/location/latest`          | JWT  | Get latest saved location            |
| POST   | `/api/twilio/status`             | -    | Twilio SMS delivery status webhook (Twilio → backend) |
| GET    | `/api/health`                   | -    | Health check                          |

---

## Twilio SMS setup (SOS notifications)

When a user triggers SOS, the backend sends an SMS to **every trusted contact**
using Twilio. Each SMS contains the user's name, an emergency message, the
timestamp, the GPS coordinates, and a clickable Google Maps link. Delivery
status (sent / delivered / failed + error) is stored per contact and shown on
the **Alerts** page, where failed notifications can be retried.

Twilio credentials live only in backend environment variables and are never
exposed to the React frontend.

### 1. Get Twilio credentials

1. Create a Twilio account at https://www.twilio.com (a trial account has
   free credit for testing).
2. In the console, copy your **Account SID** and **Auth Token** from the
   dashboard.
3. Get a Twilio phone number that can send SMS (Phone Numbers → Manage → Buy a
   number). Use E.164 format, e.g. `+12345678900`.

### 2. Configure the backend

Edit `backend/.env` (copy from `.env.example`) and set:

```ini
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+12345678900
TWILIO_STATUS_CALLBACK_URL=
TWILIO_VALIDATE_SIGNATURE=true
```

Leave `TWILIO_STATUS_CALLBACK_URL` empty to skip delivery-status callbacks
(notifications will show as "sent" once Twilio accepts them). To track real
"delivered" / "failed" status, expose the backend on a public URL (see step 3).

Restart the Flask server after changing `.env`.

> **Trial accounts** can only send SMS to *verified* numbers. Add each trusted
> contact's phone number under Phone Numbers → Verified Caller IDs before
> testing, otherwise delivery fails with a Twilio error (shown on the Alerts page).

### 3. (Optional) Real delivery status with a callback webhook

Twilio needs a public HTTPS URL to POST delivery updates back to
`/api/twilio/status`. For local development, tunnel the backend with ngrok:

```bash
# In a separate terminal, tunnel port 5000
ngrok http 5000
# Copy the https forwarding URL, e.g. https://abcd-12-34-56-78.ngrok-free.app
```

Set it in `backend/.env` (no trailing slash):

```ini
TWILIO_STATUS_CALLBACK_URL=https://abcd-12-34-56-78.ngrok-free.app
TWILIO_VALIDATE_SIGNATURE=true
```

The app uses `ProxyFix` so signature validation works behind the tunnel. To
test the webhook manually (without a valid signature), set
`TWILIO_VALIDATE_SIGNATURE=false` temporarily.

### 4. Testing SMS delivery end-to-end

1. Start the backend (`python app.py`) and frontend (`npm run dev`).
2. Register/log in, then add a trusted contact with a **verified** phone number.
3. Open the Dashboard and press-and-hold the SOS button for 2 seconds.
4. Grant location permission. The alert is created and SMS is sent to each
   contact. A toast summarizes delivery (e.g. "SMS sent to 2 of 3 contact(s).").
5. Open **Alerts** to see per-contact delivery status. A failed notification
   shows the Twilio error message and a **Retry failed** button.

### How SMS content looks

```
[SAFEHER EMERGENCY SOS]
Jane triggered an emergency alert.

Time: 2026-11-01 14:30:00 UTC
Location: 12.97160, 77.59460
Map: https://www.google.com/maps?q=12.97160,77.59460

If you are a trusted contact, please reach out or contact local emergency services (112 in India).
```

### Backend tests for notifications

The notification tests mock the Twilio client (no real messages sent):

```bash
cd women-safety-system/backend
pip install -r requirements-dev.txt
pytest tests/test_notifications.py -q
```

---

## Frontend setup

```bash
cd women-safety-system/frontend

# 1) Install dependencies
npm install

# 2) (Optional) configure the API base URL
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
# Leave VITE_API_URL empty to use the Vite dev proxy (recommended in dev),
# or set it to http://localhost:5000/api if you prefer direct calls.

# 3) Start the dev server
npm run dev
# Open http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:5000`, so you can run
the frontend and backend together without CORS configuration in development.

### Production build

```bash
npm run build      # outputs to dist/
npm run preview    # preview the production build locally
```

For a production deployment, set `VITE_API_URL` to the public backend URL and
build the frontend, then serve `dist/` with any static host.

---

## Running the backend tests

```bash
cd women-safety-system/backend
pip install -r requirements-dev.txt
pytest -q
```

Tests use an in-memory SQLite database and do not touch any files.

---

## Sample test accounts

After running `python seed.py`:

| Email                  | Password   | Notes                         |
| ---------------------- | ---------- | ----------------------------- |
| demo@womensafety.org   | demo1234   | Demo account with 3 contacts  |

You can also register a new account from the UI at any time.

---

## Features

- **Authentication:** register, log in, JWT-protected endpoints, password
  hashing with Werkzeug. Users can only access their own data.
- **Emergency SOS:** large press-and-hold SOS button (holds 2 seconds to
  prevent accidental activation) that captures your GPS location, records an
  alert, and automatically sends an SMS to every trusted contact via Twilio with
  the user's name, timestamp, coordinates, and a Google Maps link.
- **Alert management:** view alert history, filter by status, and update an
  alert's status (acknowledged / resolved / cancelled).
- **Trusted contacts:** add, edit, and delete contacts with one-tap quick-call
  (`tel:` links).
- **Location sharing:** browser Geolocation API + interactive Leaflet map,
  Google Maps link generation, copy-to-clipboard, and a clear "sharing active"
  indicator. Graceful fallback when GPS is unavailable or permission denied.
- **Safety resources:** Indian emergency helpline numbers (112, 181, etc.),
  preparedness guidance, and safety tips.
- **Dashboard:** SOS button, current location + sharing status, trusted
  contacts, recent alerts, safety tips, and quick emergency numbers.

## Security notes

- Passwords are hashed with Werkzeug's `generate_password_hash`.
- All endpoints that touch user data require a valid JWT, and every query is
  scoped to the authenticated user.
- Secrets are read from environment variables (see `.env.example`).
- For production, serve the app over HTTPS and set `CORS_ORIGINS` to your
  frontend domain instead of `*`.

## Tech notes & limitations

- Location and map require browser geolocation permission. If denied or
  unavailable, the SOS flow falls back to your last saved location; if none
  exists, it stops with a clear message asking you to call 112 directly.
- SMS delivery requires Twilio credentials in the backend `.env`. Without
  them, alerts are still recorded and each notification is marked failed with a
  "not configured" reason so the status is always transparent.
- Twilio's `messages.create` returns as soon as the message is *accepted*
  (queued). True delivery confirmation requires the status callback webhook
  (see the Twilio setup section); without it, accepted messages show as "sent"
  rather than "delivered".
- Twilio trial accounts can only send to verified numbers — verify each
  contact's number before testing.
