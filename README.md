# FlaskSetlist
This was created to automate the process of gathering songs from past setlists of an artist's concert you will attend in the future.

Retrieves songs last played at venues from setlist.fm and creates a playlist in Spotify.

## Configuration
Settings are read from environment variables (see `config.py`):

| Variable | Where it comes from |
| --- | --- |
| `SECRET_KEY` | Any long random string (Render generates one automatically) |
| `SETLIST_FM_ID` | Your setlist.fm API key |
| `SPOTIPY_CLIENT_ID` | Spotify developer dashboard |
| `SPOTIPY_CLIENT_SECRET` | Spotify developer dashboard |
| `SPOTIPY_REDIRECT_URI` | Your app's URL, e.g. `https://flasksetlist.onrender.com/`. It must also be added as a Redirect URI in the Spotify dashboard. |

## Run locally
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export SETLIST_FM_ID=... SPOTIPY_CLIENT_ID=... SPOTIPY_CLIENT_SECRET=...
export SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/
python main.py
```

## Deploy on Render
`render.yaml` describes the service. In Render, choose **New → Blueprint**, pick this repo, and fill in the secret values when asked.
Or create a **Web Service** by hand with build command `pip install -r requirements.txt` and start command `gunicorn main:app`.

Sessions are signed cookies and Spotify tokens live in the session, so the app writes nothing to disk.
