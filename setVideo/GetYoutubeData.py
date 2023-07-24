import sys
import os
sys.path.append(os.pardir)
from apiKey import config
from googleapiclient.discovery import build

def getVideo(youtubeVideoId: str):
    youtube = builtYoutube()
    response = youtube.videos().list(part='snippet,contentDetails', id=youtubeVideoId).execute()
    return response['items'][0]

def getVideosInPlaylist(
        youtubePlaylistId: str,
        nextPageToken: str = None,
        maxResults: int = 1
        ):
    youtube = builtYoutube()
    playlist_items_response = youtube.playlistItems().list(
            part="snippet",
            playlistId = youtubePlaylistId,
            maxResults = maxResults,
            pageToken = nextPageToken
            ).execute()
    return playlist_items_response

def builtYoutube():
    return build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)

def getItemResponseFromPlaylist(youtubePlaylistId: str):
    next_page_token = None
    playlistItemList = []
    while 1: 
        playlist_items_response = getVideosInPlaylist(
            youtubePlaylistId = youtubePlaylistId,
            nextPageToken = next_page_token,
            maxResults = 50,
        )
        for playlist_item in playlist_items_response["items"]:
            playlistItemList.append(playlist_item)
        next_page_token = playlist_items_response.get('nextPageToken')
        if not next_page_token:
            break
    return playlistItemList