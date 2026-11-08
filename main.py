import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.cache_handler import FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, session, request, redirect, render_template

import config
from run_setlist import create_setlist, get_unique_songs, submit_to_spotify

app = Flask(__name__)
# A fixed key (from the environment) keeps sessions valid across restarts and
# across multiple workers. Sessions are signed cookies, so nothing is written to disk.
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = config.SPOTIPY_REDIRECT_URI.startswith('https://')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

SCOPE = 'playlist-modify-public user-read-currently-playing'
SPOTIFY_ERROR_MESSAGE = ('Spotify declined the request. The app may be temporarily unavailable; '
                         'please try again later.')
NOT_FOUND_MESSAGE = 'Not Enough Playlist Data or Artist does not have any setlist data on setlistFM'


def auth_manager():
    """Spotify OAuth helper that stores the user's token in their Flask session."""
    return SpotifyOAuth(
        client_id=config.SPOTIPY_CLIENT_ID,
        client_secret=config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=config.SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
        cache_handler=FlaskSessionCacheHandler(session),
        show_dialog=True,
    )


def find_last_tour(result):
    for row in result:
        if row['tour'] != 'N/A':
            return row['tour']
    return 'N/A'


def build_setlist(artist_name):
    """Returns (rows, None) on success or (None, error_message) on failure."""
    try:
        result = create_setlist(artist_name)
    except Exception as e:  # artist not found, API error, timeout, etc.
        app.logger.warning('Setlist lookup failed for %r: %s', artist_name, e)
        return None, NOT_FOUND_MESSAGE
    if isinstance(result, str):
        return None, result
    return result, None


@app.route('/')
def index():
    oauth = auth_manager()

    if request.args.get('code'):
        # Being redirected back from Spotify's sign-in page
        oauth.get_access_token(request.args.get('code'), as_dict=False)
        return redirect('/')

    if not oauth.validate_token(oauth.cache_handler.get_cached_token()):
        # Not signed in yet: show the sign-in link
        return render_template('login.html', auth_url=oauth.get_authorize_url())

    spotify = spotipy.Spotify(auth_manager=oauth)
    try:
        name = spotify.me()['display_name']
    except SpotifyException as e:
        app.logger.warning('Spotify /me failed: %s', e)
        session.clear()
        return render_template('login.html', auth_url=oauth.get_authorize_url(),
                               error=SPOTIFY_ERROR_MESSAGE)
    return render_template('main.html', name=name)


@app.route('/sign_out')
def sign_out():
    session.clear()
    return redirect('/')


@app.route('/results', methods=['POST'])
def results():
    artist_name = request.form.get('artist_name', '').strip()
    if not artist_name:
        return render_template('main.html', error='Please enter an artist or band.')

    result, error = build_setlist(artist_name)
    if error:
        return render_template('main.html', error=error)

    # Only the artist name goes in the session cookie; /added looks the setlist up again.
    session['artist_name'] = artist_name
    return render_template('results.html', results=result, last_tour=find_last_tour(result),
                           songs=get_unique_songs(result))


@app.route('/added')
def added():
    oauth = auth_manager()
    if not oauth.validate_token(oauth.cache_handler.get_cached_token()):
        return redirect('/')

    artist_name = session.pop('artist_name', None)
    if not artist_name:
        return render_template('songsAdded.html', songs='', url='', message='Error')

    result, error = build_setlist(artist_name)
    if error:
        return render_template('songsAdded.html', songs='', url='', message='Error')

    spot_songs = get_unique_songs(result)
    spotify = spotipy.Spotify(auth_manager=oauth)
    try:
        url = submit_to_spotify(result[0]['artist'], find_last_tour(result), spot_songs, spotify)
    except SpotifyException as e:
        app.logger.warning('Creating playlist failed: %s', e)
        return render_template('songsAdded.html', songs='', url='', message='Error')
    return render_template('songsAdded.html', songs=spot_songs, url=url, message='Success')


if __name__ == '__main__':
    import os
    app.run(threaded=True, port=int(os.environ.get('PORT', 8080)))
