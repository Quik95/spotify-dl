#! /usr/bin/python3

from tqdm import tqdm
from pathlib import Path
import base64
import argparse
import subprocess
from mutagen.mp4 import MP4
from mutagen.mp4 import MP4Cover
from mutagen.mp4 import AtomDataType
import requests
import unicodedata
import re

parser = argparse.ArgumentParser()
parser.add_argument(
    "--user_id", help="Spotify Developer API User Id", required=True)
parser.add_argument(
    "--user_secret", help="Spotify Developer API User Secret", required=True)
parser.add_argument(
    "--uri", help="Spotify URI to the selected song", required=True)
parser.add_argument(
    "--url", help="Youtube URL to the selected song", required=True)
parser.add_argument(
    "--destination", help="Location to save songs into", default="./")
args = parser.parse_args()

spotify_api_key = base64.urlsafe_b64encode(
    f'{args.user_id}:{args.user_secret}'.encode()).decode()
basepath = Path(args.destination)


def slugify(value):
    """
    Modified function from Django codebase

    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    value = unicodedata.normalize('NFKC', value)
    value = re.sub(r'[^\w\s-]', '', value)
    return value.strip('-_')


def fetch_bearer(key):
    url = "https://accounts.spotify.com/api/token"
    auth = f'Basic {key}'
    data = {
        'grant_type': 'client_credentials'
    }
    headers = {
        'Authorization': auth,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = requests.post(url, data=data, headers=headers)
    b = res.json().get('access_token')
    if not b:
        raise Exception("Failed to fetch bearer")
    return b


def download_song(url, save_path):
    command = ['youtube-dlc', '-f', 'bestaudio[ext=m4a]',
               '--quiet', "-o", save_path.as_posix() + ".%(ext)s", url]
    return subprocess.run(command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE).stdout


def fetch_track_data(track_id):
    global bearer
    url = f"https://api.spotify.com/v1/tracks/{track_id}"
    auth = "Bearer " + bearer
    headers = {
        'Authorization': auth
    }
    res = requests.get(url, headers=headers).json()

    if res.get("error"):
        bearer = fetch_bearer(spotify_api_key)
        return fetch_track_data(track_id)

    return res


def extrack_data(met):
    if met.get("error"):
        raise Exception("Invalid ID")

    # Album section
    alb = met.get("album", {})
    album = alb.get("name", "")
    album_artists = ", ".join(
        [artist.get("name", "") for artist in alb.get("artists", [])]
    )
    total_tracks = alb.get("total_tracks", 1)
    cover_url = alb.get("images", [{}])[0].get("url", "")

    # General Section
    artists = ", ".join(
        [artist.get("name", "") for artist in met.get("artists", [])]
    )
    title = met.get("name", "")
    track_number = met.get("disc_number", 1)
    # 0 - for not rated
    # 1 - for explicit
    # 2 - for clean language
    # set to 2 if explicit is False else set to 1
    track_rating = [1 if met.get("explicit", False) else 2]

    return {
        'album': album,
        'album_artists': album_artists,
        'total_tracks': total_tracks,
        'artists': artists,
        'title': title,
        'track_number': track_number,
        'track_rating': track_rating,
        'cover': cover_url
    }


def add_metadata_to_song(path, m):
    if not path.exists():
        raise Exception("This song does not exists")

    song_file = MP4(path.as_posix())

    song_file["\xa9alb"] = m.get("album")

    song_file["\xa9ART"] = m.get("artists")
    song_file["aART"] = m.get("album_artists")

    song_file["trkn"] = [(m.get("track_number"), m.get("total_tracks"))]

    song_file["\xa9nam"] = m.get("title")

    song_file["rtng"] = m.get("track_rating")

    cover_img = requests.get(m.get("cover", "")).content
    cover = MP4Cover(data=cover_img, imageformat=AtomDataType.JPEG)
    song_file["covr"] = [cover]

    song_file.save()


bearer = fetch_bearer(spotify_api_key)

prefix = "spotify:track:"
raw_matadata = fetch_track_data(args.uri[len(prefix):])
metadata = extrack_data(raw_matadata)

title = metadata.get("artists", "") + " - " + metadata.get("title", "")
print(f"Track Found!\nDownloading: {title}")
save_path = basepath / (slugify(title) + ".m4a")
save_path_no_ext = basepath / slugify(title)

retries = 3
while retries >= 0:
    res = download_song(args.url, save_path_no_ext)
    if res:
        print(res, f"\nRetries remaining: {retries}")
        retries = retries - 1
    else:
        break
if 0 > retries:
    print("Failed to download song from youtube. Check if the link is correct")
else:
    add_metadata_to_song(save_path, metadata)
    print("Added Metadata\nDone!")
