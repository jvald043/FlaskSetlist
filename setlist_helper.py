import requests
import config
from spotipy.oauth2 import SpotifyClientCredentials

client_credentials_manager = SpotifyClientCredentials(
    client_id=config.SPOTIPY_CLIENT_ID,
    client_secret=config.SPOTIPY_CLIENT_SECRET)


def get_musicbrainz_id(artist_name):
    """ Gets musicBrainzID from database for use in Setlist FM """
    mbid_query = 'http://musicbrainz.org/ws/2/artist/?query=artist:{}'.format(artist_name)
    mbid_headers = {'Accept': 'application/json; charset=UTF-8', 'User-Agent': 'SetlistCreator:/1.0 (jvald043)'}
    mreq = requests.get(mbid_query, headers=mbid_headers)
    msetlist_data = mreq.json()
    return msetlist_data['artists'][0]['id']


def get_setlist_info(mbid):
    setlist_query = 'https://api.setlist.fm/rest/1.0/artist/{}/setlists?p=1'.format(mbid)
    set_headers = {'Accept': 'application/json', 'x-api-key': config.SETLIST_FM_ID}
    sreq = requests.get(setlist_query, headers=set_headers)
    # Get .json setlist_data
    setlist_data = sreq.json()
    return setlist_data

