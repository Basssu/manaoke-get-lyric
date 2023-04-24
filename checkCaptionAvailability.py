from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pprint

# YouTube Data APIのAPIキーを設定
API_KEY = 'AIzaSyCsm_qh58EORAOD8e00AXYDdlyT4yKRq2Y'  # 自分のAPIキーに置き換える
PLAYLIST_ID = 'PLNy-PdPlJT7EW4KwMfEOk_58Niq7gm-_0'  # 取得したい再生リストのIDに置き換える

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
                video_id = item['snippet']['resourceId']['videoId']
                captions = youtube.captions().list(
                    part='snippet',
                    videoId=video_id
                ).execute()
                pprint.pprint(captions)
                languageCount = 0
                for caption in captions['items']:
                    if caption['snippet']['language'] == 'ja' and caption['snippet']['trackKind'] == 'standard':
                        languageCount = languageCount + 1
                        break
                
                for caption in captions['items']:
                    if caption['snippet']['language'] == 'ko' and caption['snippet']['trackKind'] == 'standard':
                        languageCount = languageCount + 1
                        break
                
                if languageCount == 2:
                    video_ids.append(video_id)

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
