# BuzzBD Event Scoreboard

A FastAPI event scoreboard with a live display, full admin controls, score-only admin access, animated ranking changes, glassmorphism styling, and audit logs.

## Live URLs

- **Live display:** https://buzzbd.vercel.app/
- **Live display direct URL:** https://buzzbd.vercel.app/display
- **Full admin:** https://buzzbd.vercel.app/main/
- **Score-only admin:** https://buzzbd.vercel.app/admin

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

## Deploy to Vercel

1. Push the project to GitHub.
2. In Vercel, select **Add New Project**.
3. Import the GitHub repository.
4. Leave the framework preset and build command at their defaults or blank.
5. Deploy.

Vercel uses `vercel.json` and `api/index.py` to serve the FastAPI app.

To deploy future changes:

```bash
git add .
git commit -m "Update scoreboard"
git push origin main
```

Vercel will redeploy automatically when the GitHub branch is connected.

## Data and Audit Logs

- `teams.json` stores the current teams, scores, and update versions.
- `settings.json` stores the event name.
- `scores_log.jsonl` stores a timestamped full score snapshot after score-related changes.
- `changes.log` stores a readable audit trail of edits, resets, additions, deletions, and event-name changes.

The app uses version checks so two people editing the same team do not silently overwrite each other. Different teams can be updated independently.

### Important Vercel storage note

Vercel serverless storage is temporary. `teams.json`, `settings.json`, and the log files may reset after a cold start or redeployment. For permanent production data, replace the file helpers in `app.py` with a hosted database such as Supabase, Neon, Vercel Postgres, or MongoDB.

## Project Structure

```text
events/
├── app.py                 # FastAPI backend and API routes
├── requirements.txt       # Python dependencies
├── vercel.json            # Vercel configuration
├── api/index.py           # Vercel FastAPI entry point
├── teams.json             # Current team data
├── settings.json          # Current event name
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
