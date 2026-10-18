# BuzzBD Event Scoreboard

A FastAPI event scoreboard with a live display, full admin controls, score-only admin access, animated ranking changes, glassmorphism styling, and audit logs.

## Live URLs

- **Live display:** `http://localhost:5000/`
- **Live display direct URL:** `http://localhost:5000/display`
- **Full admin:** `http://localhost:5000/main/`
- **Score-only admin:** `http://localhost:5000/admin`

The root URL `/` redirects to the live display.

## Admin Access

### Full admin — `/main/`

Full admin access includes:

- Edit team names and scores
- Add teams
- Delete teams
- Change the event name
- Reset all scores
- Restore all 24 default teams after deletions
- Open the live display

### Score-only admin — `/admin`

Score-only users can edit scores and cannot access the add-team, delete-team, reset, or event-name controls in the interface.

### Live display — `/display`

The display automatically refreshes every 3 seconds and shows ranked teams with animated movement when scores change.

## Default Teams

The scoreboard starts with these 24 teams:

1. Blackwood
2. Redline
3. Ironclad
4. Deadlock
5. Nightfall
6. Overdrive
7. Outlier
8. Darkhorse
9. Blackout
10. Vanguard
11. Renegade
12. Dominion
13. Fortune
14. Legacy
15. Empire
16. Reckoning
17. Gryffindor
18. Slytherin
19. Ravenclaw
20. Hufflepuff
21. Illuminati
22. Titans
23. Demigods
24. Eternals

Resetting scores restores all 24 teams with zero points.

## Design

- Original background image retained from `static/image.png`
- Warm ivory, beige, and gold color palette
- Glassmorphism cards with light backdrop blur
- Glowing borders and soft highlights inspired by the background
- Google Fonts: DM Sans and Playfair Display
- Responsive desktop and mobile layout
- Desktop content uses 70% screen width
- Print-friendly scoreboard styles

## Local Setup

Requirements: Python 3.10+

```bash
pip install -r requirements.txt
python app.py
```

Open locally:

- http://localhost:5000/
- http://localhost:5000/display
- http://localhost:5000/main/
- http://localhost:5000/admin

## Run with Docker

Build and start the container:

```bash
docker build -t buzzbd-scoreboard .
docker run -d --name buzzbd-scoreboard -p 5000:5000 \
  -e SCOREBOARD_DB_PATH=/data/scoreboard.db \
  -v buzzbd-scoreboard-data:/data \
  buzzbd-scoreboard
```

Open `http://localhost:5000/`. Stop and remove the container with `docker stop buzzbd-scoreboard` and `docker rm buzzbd-scoreboard`.

## Data and Audit Logs

- `scoreboard.db` stores teams, scores, settings, and the audit log locally. The Docker example mounts a named volume so data survives container replacement.

The app uses version checks so two people editing the same team do not silently overwrite each other. Different teams can be updated independently.

## Project Structure

```text
events/
├── app.py                 # FastAPI backend and API routes
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container image definition
├── .dockerignore          # Files excluded from the image
├── teams.json             # Legacy seed data for first database initialization
├── settings.json          # Legacy event-name seed data
├── templates/
│   ├── admin.html         # Full and score-only admin interface
│   └── display.html       # Live scoreboard
└── static/
    ├── style.css         # Theme, glassmorphism, responsive and print styles
    ├── admin.js           # Full admin interactions and ranking animation
    ├── score-only.js      # Score-only admin interactions
    ├── display.js         # Live display polling and ranking animation
    └── image.png          # Background image
```

## API Routes

- `GET /api/teams` — get ranked teams
- `PUT /api/teams/{team_id}` — update a team
- `POST /api/teams` — add a team
- `DELETE /api/teams/{team_id}` — delete a team
- `POST /api/reset` — restore all default teams and scores
- `GET /api/settings` — get event settings
- `PUT /api/settings` — update the event name
