# On the Spot - Scoreboard Application

A FastAPI + Jinja neumorphic scoreboard for events with an admin panel and live display.

## Features

- **Admin Panel** (`/admin`): Edit team scores, add teams, reset all scores
- **Live Display** (`/display`): Real-time scoreboard for projector/screen
- **Neumorphic Design**: Modern soft UI with depth and shadows
- **Smooth Animations**: Teams slide up/down when rankings change
- **Score Change Animation**: Points pulse when updated
- **Reset Protection**: Must type "reset" to confirm
- **Auto-refresh**: Display updates every 3 seconds

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

Then open:
- **Admin Panel**: http://localhost:5000/admin
- **Live Display**: http://localhost:5000/display (open in new tab/window for projector)

## Deploy to Vercel

1. Push this folder to a GitHub repository.
2. In Vercel, choose **Add New Project** and import the repository.
3. Leave the framework preset and build command blank; Vercel uses `vercel.json` and `api/index.py`.
4. Deploy. The admin panel is at `/admin` and the live display is at `/display`.

The app currently stores scores in `teams.json`. Vercel serverless functions use temporary storage, so changes may be lost after a new deployment or cold start. For persistent production scores, replace `load_teams`/`save_teams` with a hosted database such as Vercel Postgres, Supabase, or MongoDB.

## Audit Logs

- `scores_log.jsonl` stores a timestamped full score snapshot after every score-related change.
- `changes.log` stores a readable audit trail of score edits, resets, team additions, and event-name changes.

These files are append-only during normal app use. On Vercel, they are temporary until logging is moved to persistent database storage.

## Admin Access

- **Full admin**: `/main/` — edit scores, change the event name, add teams, reset scores, and open the display.
- **Score-only admin**: `/admin` — edit team scores only.
- **Display**: `/display` — live scoreboard view.

## Usage
### Admin Panel
1. Click **Edit** beside any team to modify name/points
2. Click **+ Add Team** to add new teams
3. Click **Reset All Scores** → type "reset" → confirm to reset all to zero
4. Click **Open Display** to launch the scoreboard view

### Live Display
- Automatically updates every 3 seconds
- Shows ranked teams with medals for top 3
- Smooth row animations when positions change

## Project Structure

```
events/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── templates/
│   ├── admin.html      # Admin panel
│   └── display.html    # Live scoreboard
└── static/
    ├── style.css       # Neumorphic styles + animations
    ├── admin.js        # Admin panel logic
    └── display.js      # Display screen logic
```

## Data Storage

Teams stored in `teams.json` (created automatically on first run).

## Default Teams

On first run, creates 6 teams: Alpha, Beta, Gamma, Delta, Epsilon, Zeta.
