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