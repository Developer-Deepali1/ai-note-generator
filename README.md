# AI-Powered Smart Note Generator & Engagement Tracker for Meetings and Online Classes

AI-Powered Smart Note Generator & Engagement Tracker is a web application for turning live meetings and online classes into structured, actionable knowledge.

## What it does

- Automatic speech-to-text conversion and note generation.
- AI-generated summaries, key points, and action items.
- Attendance and engagement tracking of participants.
- Analytical reports for educators and organizers.
- Reduced manual note-taking effort and better knowledge retention.

## Project structure

- `client/` contains the React + TypeScript frontend.
- `server/` contains the Flask backend and supporting modules.
- `docs/` contains setup, architecture, API, and deployment documentation.

## Getting started

1. Review `docs/SETUP_GUIDE.md` for local setup steps.
2. Start the backend from `server/` and the frontend from `client/`.
3. Open the app and record or upload a session to generate notes and engagement insights.

## Single-server launcher

You can use the provided `run_server.py` script from the repository root to build the frontend and start the backend with one command (requires Node.js/npm and Python):

```powershell
python run_server.py
```

Environment variables recognized by the launcher / Flask:
- `PORT` — port for the Flask server (default `5000`)
- `HOST` — host for the Flask server (default `0.0.0.0`)
- `FLASK_DEBUG` — set `1` or `true` to enable debug mode

If you prefer Windows batch automation, run the same command from Command Prompt or PowerShell. Ensure your Python virtual environment is activated if you're using one.
