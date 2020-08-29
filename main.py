import os
import uuid
from pprint import pprint

import spotipy
import config
from spotipy.oauth2 import SpotifyOAuth
from flask_session import Session
from flask import Flask, session, request, redirect, render_template

from run_setlist import create_setlist, get_unique_songs, submit_to_spotify
from setlist_helper import client_credentials_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    if not session.get('uuid'):
        return False
    else:
        return caches_folder + session.get('uuid')


@app.route('/')
def index():
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    spotify_auth_manager = SpotifyOAuth(
        client_id=config.SPOTIPY_CLIENT_ID,
        client_secret=config.SPOTIPY_CLIENT_SECRET,
        scope='playlist-modify-public user-read-currently-playing',
        redirect_uri=config.SPOTIPY_REDIRECT_URI,
        cache_path=session_cache_path(),
        show_dialog=True
    )

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        spotify_auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not spotify_auth_manager.get_cached_token():
        # Step 2. Display sign in link when no token
        auth_url = spotify_auth_manager.get_authorize_url()
        return render_template('login.html', auth_url=auth_url)

    # Step 4. Signed in, display data
    spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager,
                              auth_manager=spotify_auth_manager)
    return render_template('main.html', name=spotify.me()["display_name"])


@app.route('/sign_out')
def sign_out():
    os.remove(session_cache_path())
    session.clear()
    if session_cache_path():
        try:
            # Remove the CACHE file (.cache-test) so that a new user can authorize.
            os.remove(session_cache_path())
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


@app.route('/results', methods=['POST'])
def results():
    form_submit = str(request.form['artist_name'])
    artist_name = form_submit.strip()
    result = create_setlist(artist_name)
    if type(result) == str:
        return render_template('main.html', error=result)
    else:
        session['song_data'] = result
        spot_songs = get_unique_songs(result)
        # Record last tour
        last_tour = 'N/A'
        for i in result:
            if i['tour'] != 'N/A':
                last_tour = i['tour']
                break
        return render_template('results.html', results=result, last_tour=last_tour, songs=spot_songs)


@app.route('/added')
def added():
    spot_songs = ''
    url = ''
    # get song list from session
    if session.get('song_data'):
        result_data = session.get('song_data')
        spot_songs = get_unique_songs(result_data)
        last_tour = 'N/A'
        for i in result_data:
            if i['tour'] != 'N/A':
                last_tour = i['tour']
                break

        spotify_auth_manager = SpotifyOAuth(
            client_id=config.SPOTIPY_CLIENT_ID,
            client_secret=config.SPOTIPY_CLIENT_SECRET,
            scope='playlist-modify-public user-read-currently-playing',
            redirect_uri=config.SPOTIPY_REDIRECT_URI,
            cache_path=session_cache_path(),
            show_dialog=True
        )

        spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager,
                                  auth_manager=spotify_auth_manager)

        url = submit_to_spotify(result_data[0]['artist'], last_tour, spot_songs, spotify)
        session.pop('song_data')
        message = 'Success'
    else:
        message = 'Error'
    return render_template('songsAdded.html', songs=spot_songs, url=url, message=message)


if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT", 8080)))
