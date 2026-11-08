import requests
import config

def get_musicbrainz_id(artist_name):
    """ Gets musicBrainzID from database for use in Setlist FM """
    mbid_query = 'https://musicbrainz.org/ws/2/artist/'
    mbid_headers = {'Accept': 'application/json; charset=UTF-8', 'User-Agent': 'SetlistCreator:/1.0 (jvald043)'}
    mreq = requests.get(mbid_query, params={'query': 'artist:' + artist_name, 'fmt': 'json'},
                        headers=mbid_headers, timeout=15)
    msetlist_data = mreq.json()
    return msetlist_data['artists'][0]['id']


def get_setlist_info(mbid):
    setlist_query = 'https://api.setlist.fm/rest/1.0/artist/{}/setlists?p=1'.format(mbid)
    set_headers = {'Accept': 'application/json', 'x-api-key': config.SETLIST_FM_ID}
    sreq = requests.get(setlist_query, headers=set_headers, timeout=15)
    # Get .json setlist_data
    setlist_data = sreq.json()
    return setlist_data

