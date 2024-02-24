import sys
import os
sys.path.append(os.pardir)
from api_key import config
from googleapiclient.discovery import build
from typing import Optional

def get_video(youtubeVideoId: str) -> Optional[dict]:
    youtube = built_youtube()
    response = youtube.videos().list(part='snippet,contentDetails', id=youtubeVideoId).execute()
    if len(response['items']) == 0:
        return None
    return response['items'][0]

def get_videos_in_playlist(
        youtube_playlist_id: str,
        next_page_token: str = None,
        max_results: int = 1
        ):
    youtube = built_youtube()
    playlist_items_response = youtube.playlistItems().list(
            part="snippet",
            playlistId = youtube_playlist_id,
            maxResults = max_results,
            pageToken = next_page_token
            ).execute()
    return playlist_items_response

def built_youtube():
    return build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY)

def get_item_response_from_playlist(youtube_playlist_id: str):
    next_page_token = None
    playlist_item_list = []
    while 1: 
        playlist_items_response = get_videos_in_playlist(
            youtube_playlist_id = youtube_playlist_id,
            next_page_token = next_page_token,
            max_results = 50,
        )
        for playlist_item in playlist_items_response["items"]:
            playlist_item_list.append(playlist_item)
        next_page_token = playlist_items_response.get('nextPageToken')
        if not next_page_token:
            break
    return playlist_item_list