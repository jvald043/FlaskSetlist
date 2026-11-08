import spotipy
from spotipy.exceptions import SpotifyException, SpotifyOauthError
from spotipy.cache_handler import FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, session, request, redirect, render_template, url_for

import config
from run_setlist import create_setlist, get_unique_songs, submit_to_spotify

app = Flask(__name__)
# A fixed key (from the environment) keeps sessions valid across restarts and
# across multiple workers. Sessions are signed cookies, so nothing is written to disk.
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = config.SPOTIPY_REDIRECT_URI.startswith('https://')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

SCOPE = 'playlist-modify-public user-read-currently-playing'
NOT_FOUND_MESSAGE = 'Not Enough Playlist Data or Artist does not have any setlist data on setlistFM'
SPOTIFY_ERROR_MESSAGE = ("Spotify didn't allow the playlist to be created. "
                         "The Spotify connection for this app may be temporarily unavailable.")


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


def signed_in(oauth):
    return bool(oauth.validate_token(oauth.cache_handler.get_cached_token()))


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
    # Spotify sends users back here after they approve (or cancel) access.
    # This must stay at "/" because it is the registered redirect URI.
    if request.args.get('code'):
        try:
            auth_manager().get_access_token(request.args.get('code'), as_dict=False)
        except SpotifyOauthError as e:
            app.logger.warning('Spotify token exchange failed: %s', e)
            return render_template('songsAdded.html', message='Error', error=SPOTIFY_ERROR_MESSAGE)
        # Finish what the user started: save the playlist they asked for.
        if session.get('artist_name'):
            return redirect(url_for('added'))
        return redirect(url_for('search'))

    if request.args.get('error'):
        # User clicked "Cancel" on Spotify's page.
        if session.get('artist_name'):
            return render_template('songsAdded.html', message='Error',
                                   error='Spotify access was not granted, so no playlist was created.')
        return redirect(url_for('search'))

    return render_template('login.html')


@app.route('/search')
def search():
    return render_template('main.html', signed_in=signed_in(auth_manager()))


@app.route('/sign_out')
def sign_out():
    session.clear()
    return redirect('/')


@app.route('/results', methods=['POST'])
def results():
    artist_name = request.form.get('artist_name', '').strip()
    if not artist_name:
        return render_template('main.html', error='Please enter an artist or band.',
                               signed_in=signed_in(auth_manager()))

    result, error = build_setlist(artist_name)
    if error:
        return render_template('main.html', error=error, signed_in=signed_in(auth_manager()))

    # Only the artist name goes in the session cookie; /added looks the setlist up again.
    session['artist_name'] = artist_name
    return render_template('results.html', results=result, last_tour=find_last_tour(result),
                           songs=get_unique_songs(result))


@app.route('/save/spotify')
def save_spotify():
    """Ask for Spotify access only now, when the user wants to save the playlist."""
    if not session.get('artist_name'):
        return redirect(url_for('search'))
    oauth = auth_manager()
    if signed_in(oauth):
        return redirect(url_for('added'))
    return redirect(oauth.get_authorize_url())


@app.route('/added')
def added():
    oauth = auth_manager()
    if not signed_in(oauth):
        return redirect(url_for('save_spotify'))

    artist_name = session.pop('artist_name', None)
    if not artist_name:
        return redirect(url_for('search'))

    result, error = build_setlist(artist_name)
    if error:
        return render_template('songsAdded.html', message='Error', error=error)

    spot_songs = get_unique_songs(result)
    spotify = spotipy.Spotify(auth_manager=oauth)
    try:
        url = submit_to_spotify(result[0]['artist'], find_last_tour(result), spot_songs, spotify)
    except SpotifyException as e:
        app.logger.warning('Creating playlist failed: %s', e)
        return render_template('songsAdded.html', message='Error', error=SPOTIFY_ERROR_MESSAGE)
    return render_template('songsAdded.html', songs=spot_songs, url=url, message='Success')


if __name__ == '__main__':
    import os
    app.run(threaded=True, port=int(os.environ.get('PORT', 8080)))
