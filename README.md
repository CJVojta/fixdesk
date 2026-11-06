# FixDesk

A local issue tracker for shared spaces. Report a maintenance issue, check the queue, and mark it resolved. The browser UI talks to a Python JSON API backed by SQLite.

## Try it locally

Requires Python 3.10 or newer. No dependencies to install.

```sh
python app.py
```

Open http://127.0.0.1:8000. Add an issue, resolve it, then reload the page to see the saved status.

## API

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/issues` | List issues, newest first |
| POST | `/api/issues` | Create an issue from a JSON object with a `title` |
| PATCH | `/api/issues/{id}/resolve` | Mark an issue resolved |

Titles must contain 1–120 characters. Issue titles are rendered as text in the browser. SQL statements bind user values as parameters, and repeating a resolve request keeps the issue resolved.

The server listens on localhost. The database is created on first run and excluded from Git.
