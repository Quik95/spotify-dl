# Spotify-dl

**spotify-dl** is a simple python script for downloading songs and tagging them using tags from spotify.

Usage
---
`spotify-dl.py --user-id <user-id> --user-secret <user-secret> --destination <destination> --uri <spotify URI> --url <video link>`

Options
---
    --user-id       Spotify API user id
    --user-secret   Spotify API user secret
    --uri           Spotify Track URI. You can get it by right clicking on the song in spotify client, selecting share and Copy Spotify URI
    --url           Link to the music video from youtube or any other site supported by youtube-dl
    --destination   Where to save a resulting song. Defaults to current working directory