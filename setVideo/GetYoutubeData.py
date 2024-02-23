import sys
import os
sys.path.append(os.pardir)
from apiKey import config
from googleapiclient.discovery import build
from typing import Optional

def get_video(youtubeVideoId: str) -> Optional[dict]:
    youtube = built_youtube()
    response = youtube.videos().list(part='snippet,contentDetails', id=youtubeVideoId).execute()
    if len(response['items']) == 0:
        return None
    return response['items'][0]

def get_videos_in_playlist(
        youtubePlaylistId: str,
        nextPageToken: str = None,
        maxResults: int = 1
        ):
    youtube = built_youtube()
    playlist_items_response = youtube.playlistItems().list(
            part="snippet",
            playlistId = youtubePlaylistId,
            maxResults = maxResults,
            pageToken = nextPageToken
            ).execute()
    return playlist_items_response

def built_youtube():
    return build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)

def get_item_response_from_playlist(youtubePlaylistId: str):
    next_page_token = None
    playlistItemList = []
    while 1: 
        playlist_items_response = get_videos_in_playlist(
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