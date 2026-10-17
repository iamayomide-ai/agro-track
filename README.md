# AgroTrack

**A farmer performance dashboard for tracking, comparing, and analyzing agricultural output across company departments.**

AgroTrack lets a company enroll farmers, log their daily output, and see how each farmer and department is performing, by day, week, and month. Each department is measured in its own unit (kg for Fishery, crates for Poultry and Horticulture), and farmers are compared fairly against their own department's average.

---

## Features

- **Farmer enrollment:** register farmers with name, contact, department, and enrollment date. A unique farmer ID (`FMR-0001`, `FMR-0002`, ...) is generated automatically.
- **Edit and archive:** update farmer details, or archive a farmer. Archiving is a soft delete, so historical performance data is preserved.
- **Farmers directory:** search by name, ID, or contact, and filter by department and status (active/archived).
- **Daily performance logging:** record a farmer's output for a given day, with optional notes. Only active farmers can be logged, and only one log is allowed per farmer per day.
- **Farmer portfolio:** a profile page per farmer with average performance, peak single day, and a trend line chart of their output over time.
- **Department breakdown:** each department shows its active farmer count, core metric, and measurement unit.
- **Performance analysis:** weekly and monthly views with per-department totals, daily benchmark averages, and top performers, each in the department's own unit.
- **Normalized leaderboard:** farmers are ranked by how far above or below their own department's daily average they are (e.g. `+1.0% vs Dept Avg`), so farmers in departments with different units can be compared fairly.
- **Dark mode:** a light/dark theme toggle that remembers your choice in the browser.
- **Honest weekly charts:** partial weeks are labeled with the number of recorded days (e.g. `Sep 12-13 (2d)`) so short weeks aren't mistaken for low output.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14, Django 6.1.1 |
| Database | SQLite (`db.sqlite3`) |
| Styling | Tailwind CSS (CDN) |
| Icons | Font Awesome 6.4 (CDN) |
| Charts | Chart.js (CDN) |
| Dark mode | Tailwind `darkMode: 'class'` + `localStorage` |
| Server | Django development server on port 8080 |
| Launcher | `start_dashboard.bat` (one-click, Windows) |

## Getting Started

### Prerequisites

- Python 3.12 or newer (required by Django 6.1)
- `pip` and `venv`
- Git

### Installation

```bash
git clone https://github.com/iamayomide-ai/<repo-name>.git
cd <repo-name>

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Set up the database

```bash
python manage.py migrate
```

### Run the app

```bash
python manage.py runserver 8080
```

Then open <http://127.0.0.1:8080/> in your browser.

**Windows shortcut:** double-click `start_dashboard.bat` in the project folder to start the server in one click.

## How It Works

### Departments and metrics

Each department has one core metric and one unit, which determines what is tracked for every farmer in it.

| Department | Core metric | Unit |
|---|---|---|
| Fishery | Harvest Weight | kg |
| Horticulture | Harvest Volume | crates |
| Poultry | Egg Yield | crates |

### Logging rules

- One performance log per farmer per day.
- Only active farmers appear in the log form.
- Archived farmers keep all their historical logs but can no longer be logged.

### Analytics

- Weekly and monthly figures are computed from the daily logs, not stored separately.
- Totals and benchmarks are reported **per department**, in that department's own unit. Values in different units (kg and crates) are never added together.
- The leaderboard compares each farmer's **daily average** against their department's daily average, so farmers with a different number of logged days are compared on equal terms.
- A department with only one farmer has no peers to compare against and shows `On Department Avg`.

## Data Model

| Entity | Key fields |
|---|---|
| **Department** | name, core metric, measurement unit |
| **Farmer** | farmer ID (`FMR-0001`), full name, contact, department, enrollment date, status (active/archived) |
| **Performance log** | farmer, log date, metric value, notes |

## Roadmap

- [ ] User authentication and role-based access (admin, supervisor, viewer)
- [ ] Bulk daily entry: log a whole department's output in one form
- [ ] Extra farmer details: location and notes
- [ ] Per-department charts in the "All Departments" analytics view
- [ ] Export reports (CSV / PDF)
- [ ] Multi-company (multi-tenant) support

## Author

**Osoyan Daniel Ayomide**
GitHub: [@iamayomide-ai](https://github.com/iamayomide-ai)
