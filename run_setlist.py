import pprint

import config
from setlist_helper import get_musicbrainz_id, get_setlist_info


def create_setlist(artist_name):
    # This Function will retrieve the songs from setlist FM
    # and create a setlist on Spotify from the latest songs played.
    # Intention is to have a setlist of any band's show based on the songs they have previously played
    # and create a playlist out of it, to prepare for the show

    # Retrieve mbrainz ID for use in Setlist FM
    mbid = get_musicbrainz_id(artist_name)

    # Get .json setlist_data from setlist FM
    setlist_data = get_setlist_info(mbid)

    # store artist, tour, venue_name, song, and set in lists
    artist_info = []

    try:
        int(setlist_data['total']) > 5
    except:
        message = 'Not Enough Playlist Data or Does not have any setlist data on setlistFM'
        return message

    # Loop through most recent 15 setlists unless setlists is less than 7
    counter = 15

    if len(setlist_data['setlist']) < counter:
        counter = len(setlist_data['setlist'])

    # Create a Setlist from just the latest Tour name, and one of all songs, later make a set out of it.
    # Last Tour Name
    current_tour_name = ''

    for i in range(counter):
        is_tour = False
        current_tour = 'N/A'
        # If tour is not blank, record name of tour
        if 'tour' in setlist_data['setlist'][i]:
            is_tour = True
            if is_tour:
                current_tour = setlist_data['setlist'][i]['tour']['name']
            if not current_tour_name:
                current_tour_name = setlist_data['setlist'][i]['tour']['name']
        # If no setlist_data Available
        if len(setlist_data['setlist'][i]['sets']['set']) == 0:
            row_dict = {
                'artist': setlist_data['setlist'][i]['artist']['name'],
                'tour': current_tour,
                'venue': setlist_data['setlist'][i]['venue']['name'],
                'song': 'No Setlist Created Yet',
                'set': 'N/A'
            }
            artist_info.append(row_dict)
        else:
            for sets in setlist_data['setlist'][i]['sets']['set']:
                song_set = 'Main'
                for songs in sets['song']:
                    if 'encore' in sets:
                        song_set = 'encore ' + str(sets['encore'])
                    try:
                        # If last tour name is equal to setlist of this set
                        if is_tour:
                            current_tour = setlist_data['setlist'][i]['tour']['name']
                        else:
                            current_tour = 'N/A'
                        row_dict = {
                            'artist': setlist_data['setlist'][i]['artist']['name'],
                            'tour': current_tour,
                            'venue': setlist_data['setlist'][i]['venue']['name'],
                            'song': songs['name'],
                            'set': song_set
                        }
                        artist_info.append(row_dict)
                    except:
                        row_dict = {
                            'artist': setlist_data['setlist'][i]['artist']['name'],
                            'tour': current_tour,
                            'venue': setlist_data['setlist'][i]['venue']['name'],
                            'song': 'No Setlist Created Yet',
                            'set': 'N/A'
                        }
                        artist_info.append(row_dict)
    return artist_info


def get_unique_songs(artist_info):
    song_list = []
    for info in artist_info:
        if info['song'] != 'No Setlist Created Yet':
            song_list.append(info['song'])
    song_list = list(dict.fromkeys(song_list))
    return song_list


def submit_to_spotify(artist_name, current_tour_name, song_list, spot):
    # get URI for Track
    spotify_songs = {}
    for songs in song_list:
        spot_results = spot.search(q='track:' + songs + ' artist:' + artist_name, type='track', limit=5)
        if spot_results['tracks']['total'] != 0:
            spotify_songs[songs] = spot_results['tracks']['items'][0]['uri']

    # create a playlist with Artist Name
    playlist = spot.user_playlist_create(
        config.CLIENT_USER_ID,
        'Upcoming ' + artist_name + ' tour playlist',
        public=True,
        description='Playlist created of songs played by '
                    + artist_name +
                    ' during their ' +
                    current_tour_name + ' tour')

    for uri in spotify_songs.values():
        spot.user_playlist_add_tracks(
            config.CLIENT_USER_ID,
            playlist['id'],
            [uri])
    return playlist['external_urls']['spotify']
