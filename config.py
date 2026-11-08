"""App settings, read from environment variables.

Set these in Render's dashboard (or your shell / a .env loader when running locally):
    SECRET_KEY             - any long random string; keeps users logged in across restarts
    SETLIST_FM_ID          - setlist.fm API key
    MBRAINZ_TOKEN          - optional, currently unused by the app
    SPOTIPY_CLIENT_ID      - from the Spotify developer dashboard
    SPOTIPY_CLIENT_SECRET  - from the Spotify developer dashboard
    SPOTIPY_REDIRECT_URI   - must exactly match a redirect URI in the Spotify dashboard,
                             e.g. https://flasksetlist.onrender.com/
"""
import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-only-change-me')
SETLIST_FM_ID = os.environ.get('SETLIST_FM_ID', '')
MBRAINZ_TOKEN = os.environ.get('MBRAINZ_TOKEN', '')
SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID', '')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET', '')
SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8080/')
