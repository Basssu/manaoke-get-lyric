import firebase_admin
from firebase_admin import credentials, firestore
import google.auth
from googleapiclient.discovery import build
import datetime
from apiKey import config
from googleapiclient.errors import HttpError
import youtube_transcript_api


flavor = "prod"
video_ids = []
DEVELOPER_KEY = config.YOUTUBE_API_KEY

def addVideos(latestVideoIdInFirestore, playlist_id):
    try:
        next_page_token = None
        playlist_items = []

        response = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=1,
                ).execute()
        
        if datetime.datetime.fromisoformat(response["items"][0]["snippet"]['publishedAt'].replace('Z', '+00:00')) < publishedAt: # 新しい動画が先にこない場合は全て取得する
            while 1: 
                playlist_items_response = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                    ).execute()
                playlist_items.append(playlist_items_response["items"][0])
                next_page_token = playlist_items_response.get('nextPageToken')
                if not next_page_token:
                    break
        else: #　新しい動画が最初に来る場合は、最初の方から動画を取得していく
            for i in range(50):
                playlist_items_response = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=playlist_id,
                    maxResults=1,
                    pageToken=next_page_token
                    ).execute()
                if playlist_items_response["items"][0]["snippet"]["resourceId"]["videoId"] == latestVideoIdInFirestore:
                    break
                playlist_items.append(playlist_items_response["items"][0])
                next_page_token = playlist_items_response.get('nextPageToken')
        
        for playlist_item in playlist_items:
            video_id = playlist_item["snippet"]["resourceId"]["videoId"]
            video_published_at = datetime.datetime.fromisoformat(playlist_item['snippet']['publishedAt'].replace('Z', '+00:00'))
            # 指定した動画よりも新しい投稿日時の動画IDを取得する
            if latestVideoIdInFirestore == video_id:
                continue
            if video_published_at < publishedAt:
                continue
            try:
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

    except HttpError as e:
        print("An HTTP error occurred: %s" % e)
        exit

# Firebase Admin SDKの初期化
if flavor == "prod":
    creds = credentials.Certificate("firebaseKey/manaoke-8c082-firebase-adminsdk-37ba1-6de8dec42f.json")
    domain = "manaoke-8c082.appspot.com"
else:
    creds = credentials.Certificate("firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")
    domain = "manaoke-stg.appspot.com"
firebase_admin.initialize_app(creds)

# Firestoreのクライアント作成
db = firestore.client()

# YouTube Data APIを利用するためのオブジェクトを作成する
youtube = build("youtube", "v3", developerKey=DEVELOPER_KEY)

# newVideoIdsの初期化
newVideoIds = []

# seriesコレクションのドキュメントを取得
series_ref = db.collection('series')
series_docs = series_ref.get()

# 各ドキュメントに対して処理を実行
for doc in series_docs:
    # playlistIdとcelebritiesの取得
    playlistId = doc.get('playlistId')
    if playlistId == None:
        continue
    
    # playlistIdが含まれるvideoドキュメントのうち、publishedAtが最新のものを取得
    videos_ref = db.collection('videos')
    query = videos_ref.where('playlistIds', 'array_contains', playlistId).order_by('publishedAt', direction=firestore.Query.DESCENDING).limit(1)
    video_docs = query.get()
    
    if len(video_docs) == 0:
        continue
        
    video_doc = video_docs[0]
    videoId = video_doc.get('videoId')
    publishedAt = video_doc.get('publishedAt')
    addVideos(videoId, playlistId)

print(video_ids)
print(' '.join(video_ids))
