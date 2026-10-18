from pathlib import Path
import json
import os
import sqlite3
from threading import Lock
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
LOCAL_DB = BASE_DIR / "scoreboard.db"
TEAM_WRITE_LOCK = Lock()

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def db_connection():
    remote_url = os.environ.get("TURSO_DATABASE_URL")
    if remote_url:
        try:
            import libsql
        except ImportError as exc:
            raise RuntimeError("TURSO_DATABASE_URL is set but libsql is not installed") from exc
        return libsql.connect(database=remote_url, auth_token=os.environ.get("TURSO_AUTH_TOKEN"))
    connection = sqlite3.connect(LOCAL_DB, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection

def default_teams():
    names = [
        "Blackwood", "Redline", "Ironclad", "Deadlock", "Nightfall", "Overdrive",
        "Outlier", "Darkhorse", "Blackout", "Vanguard", "Renegade", "Dominion",
        "Fortune", "Legacy", "Empire", "Reckoning", "Gryffindor", "Slytherin",
        "Ravenclaw", "Hufflepuff", "Illuminati", "Titans", "Demigods", "Eternals",
    ]
    return [{"id": index, "name": name, "points": 0, "version": 0} for index, name in enumerate(names, start=1)]

def initialize_database():
    connection = db_connection()
    connection.execute("CREATE TABLE IF NOT EXISTS teams (id INTEGER PRIMARY KEY, name TEXT NOT NULL, points INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 0)")
    connection.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, action TEXT NOT NULL, details TEXT, scores TEXT NOT NULL)")
    if connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 0:
        legacy = BASE_DIR / "teams.json"
        teams = json.loads(legacy.read_text(encoding="utf-8")) if legacy.exists() else default_teams()
        connection.executemany("INSERT INTO teams (id, name, points, version) VALUES (?, ?, ?, ?)", [(t["id"], t["name"], t.get("points", 0), t.get("version", 0)) for t in teams])
    if connection.execute("SELECT COUNT(*) FROM settings WHERE key = 'event_name'").fetchone()[0] == 0:
        legacy = BASE_DIR / "settings.json"
        event_name = json.loads(legacy.read_text(encoding="utf-8")).get("event_name", "On the Spot") if legacy.exists() else "On the Spot"
        connection.execute("INSERT INTO settings (key, value) VALUES ('event_name', ?)", (event_name,))
    connection.commit()
    connection.close()

initialize_database()
app = FastAPI(title="On the Spot Scoreboard")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

def load_teams():
    connection = db_connection()
    rows = connection.execute("SELECT id, name, points, version FROM teams").fetchall()
    connection.close()
    return [dict(row) for row in rows]

def ranked_teams():
    teams = sorted(load_teams(), key=lambda team: team["points"], reverse=True)
    for rank, team in enumerate(teams, start=1):
        team["rank"] = rank
    return teams

def load_settings():
    connection = db_connection()
    row = connection.execute("SELECT value FROM settings WHERE key = 'event_name'").fetchone()
    connection.close()
    return {"event_name": row[0] if row else "On the Spot"}

def log_scores(action, teams, details=None):
    connection = db_connection()
    connection.execute("INSERT INTO audit_log (timestamp, action, details, scores) VALUES (?, ?, ?, ?)", (timestamp(), action, json.dumps(details) if details else None, json.dumps([{"id": t["id"], "name": t["name"], "points": t["points"]} for t in teams])))
    connection.commit()
    connection.close()

def log_change(message):
    log_scores("change", load_teams(), {"message": message})

@app.get("/", include_in_schema=False)
def index():
    return RedirectResponse(url="/display")

@app.get("/admin", include_in_schema=False)
def admin(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={"teams": ranked_teams(), "event_name": load_settings()["event_name"], "full_access": False})

@app.get("/main/", include_in_schema=False)
def main_admin(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={"teams": ranked_teams(), "event_name": load_settings()["event_name"], "full_access": True})

@app.get("/display", include_in_schema=False)
def display(request: Request):
    return templates.TemplateResponse(request=request, name="display.html", context={"teams": ranked_teams(), "event_name": load_settings()["event_name"]})

@app.get("/api/teams")
def get_teams():
    return ranked_teams()

@app.get("/api/settings")
def get_settings():
    return load_settings()

@app.put("/api/settings")
async def update_settings(request: Request):
    data = await request.json()
    event_name = str(data.get("event_name", "On the Spot")).strip() or "On the Spot"
    connection = db_connection()
    connection.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('event_name', ?)", (event_name[:100],))
    connection.commit()
    connection.close()
    return {"success": True, "event_name": event_name[:100]}

@app.put("/api/teams/{team_id}")
async def update_team(team_id: int, request: Request):
    data = await request.json()
    with TEAM_WRITE_LOCK:
        connection = db_connection()
        current = connection.execute("SELECT id, name, points, version FROM teams WHERE id = ?", (team_id,)).fetchone()
        if not current:
            connection.close()
            return JSONResponse({"success": False, "message": "Team not found"}, status_code=404)
        if data.get("version") is not None and int(data["version"]) != current["version"]:
            connection.close()
            return JSONResponse({"success": False, "conflict": True, "message": "This team was updated by someone else. Refresh and try again."}, status_code=409)
        connection.execute("UPDATE teams SET name = ?, points = ?, version = version + 1 WHERE id = ?", (data.get("name", current["name"]), data.get("points", current["points"]), team_id))
        connection.commit()
        team = dict(connection.execute("SELECT id, name, points, version FROM teams WHERE id = ?", (team_id,)).fetchone())
        connection.close()
        log_scores("team_updated", load_teams(), {"team_id": team_id})
        return {"success": True, "team": team}

@app.delete("/api/teams/{team_id}")
def delete_team(team_id: int):
    with TEAM_WRITE_LOCK:
        connection = db_connection()
        deleted = connection.execute("SELECT id, name, points, version FROM teams WHERE id = ?", (team_id,)).fetchone()
        if not deleted:
            connection.close()
            return JSONResponse({"success": False, "message": "Team not found"}, status_code=404)
        connection.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        connection.commit()
        connection.close()
        log_scores("team_deleted", load_teams(), {"team_id": team_id, "team_name": deleted["name"]})
        return {"success": True, "team": dict(deleted)}

@app.post("/api/reset")
async def reset_teams(request: Request):
    data = await request.json()
    if data.get("confirm") != "reset":
        return JSONResponse({"success": False, "message": 'Type "reset" to confirm'}, status_code=400)
    with TEAM_WRITE_LOCK:
        connection = db_connection()
        connection.execute("DELETE FROM teams")
        connection.executemany("INSERT INTO teams (id, name, points, version) VALUES (?, ?, 0, 0)", [(t["id"], t["name"]) for t in default_teams()])
        connection.commit()
        connection.close()
    log_scores("scores_reset", load_teams())
    return {"success": True, "message": "Scores reset successfully"}

@app.post("/api/teams")
async def add_team(request: Request):
    data = await request.json()
    connection = db_connection()
    new_id = connection.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM teams").fetchone()[0]
    name = data.get("name", f"Team {new_id}")
    connection.execute("INSERT INTO teams (id, name, points, version) VALUES (?, ?, 0, 0)", (new_id, name))
    connection.commit()
    connection.close()
    team = {"id": new_id, "name": name, "points": 0, "version": 0}
    log_scores("team_added", load_teams(), {"team_id": new_id})
    return {"success": True, "team": team}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
