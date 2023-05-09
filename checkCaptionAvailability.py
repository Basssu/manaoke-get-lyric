from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pprint
from apiKey import config
import youtube_transcript_api

# YouTube Data APIのAPIキーを設定
API_KEY = config.YOUTUBE_API_KEY  # 自分のAPIキーに置き換える
PLAYLIST_ID = 'PL2NKTOu-b3XG25ZS2_ni7k_-enzZ9L-H6'  # 取得したい再生リストのIDに置き換える

def get_video_ids_with_subtitles(api_key, playlist_id):
    youtube = build('youtube', 'v3', developerKey=api_key)

    try:
        video_ids = []
        next_page_token = None

        # ページングを使って再生リスト内の全ての動画を取得
        while True:
            # 再生リスト内の動画を取得
            playlist_items = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50,  # 1リクエストあたりの最大取得件数は50件
                pageToken=next_page_token
            ).execute()

            # 取得した動画のSnippet情報をチェックし、日本語字幕と韓国語字幕の設定がある動画の場合、Video IDを配列に追加
            for item in playlist_items['items']:
                try:
                    video_id = item['snippet']['resourceId']['videoId']
                    transcript_list = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
                    languageCount1 = 0
                    for transcript in transcript_list:
                        if transcript.language_code == 'ko' and not transcript.is_generated:
                            languageCount1 = languageCount1 + 1
                            break
                    for transcript in transcript_list:
                        if transcript.language_code == 'ja' and not transcript.is_generated:
                            languageCount1 = languageCount1 + 1
                            break
                    if languageCount1 == 2:
                        video_ids.append(video_id)
                except:
                    print('error')
            # 次のページがあれば次のページトークンを設定し、なければループを終了
            next_page_token = playlist_items.get('nextPageToken')
            if not next_page_token:
                break

        return video_ids

    except HttpError as e:
        print(f'エラーが発生しました: {e}')
        return None

# 再生リスト内の動画のうち、日本語字幕と韓国語字幕の設定がある動画のVideo IDを取得
video_ids = get_video_ids_with_subtitles(API_KEY, PLAYLIST_ID)
if video_ids is not None:
    print(f'日本語字幕と韓国語字幕のある動画のVideo ID: {video_ids}')
    print(' '.join(video_ids))
