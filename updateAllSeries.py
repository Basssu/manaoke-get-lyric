import firebase_admin
from firebase_admin import credentials, firestore
import google.auth
from googleapiclient.discovery import build
import datetime

# Firebase Admin SDKの初期化
creds = credentials.Certificate("path/to/serviceAccountKey.json")
firebase_admin.initialize_app(creds)

# Firestoreのクライアント作成
db = firestore.client()

# Youtube Data APIの認証
creds, _ = google.auth.default()
youtube = build('youtube', 'v3', credentials=creds)

# newVideoIdsの初期化
newVideoIds = []

# seriesコレクションのドキュメントを取得
series_ref = db.collection('series')
series_docs = series_ref.get()

# 各ドキュメントに対して処理を実行
for doc in series_docs:
    # playlistIdとcelebritiesの取得
    playlistId = doc.get('playlistId')
    celebrities = doc.get('celebrities')
    
    # playlistIdが含まれるvideoドキュメントのうち、publishedAtが最新のものを取得
    videos_ref = db.collection('videos')
    query = videos_ref.where('playlistIds', 'array_contains', playlistId).order_by('publishedAt', direction=firestore.Query.DESCENDING).limit(1)
    video_docs = query.get()
    
    if len(video_docs) == 0:
        continue
        
    video_doc = video_docs[0]
    videoId = video_doc.get('videoId')
    publishedAt = video_doc.get('publishedAt')
    
    # Youtube Data APIで再生リストを検索
    playlist_response = youtube.playlists().list(
        part='snippet',
        id=playlistId
    ).execute()
    
    if 'items' not in playlist_response:
        continue
        
    playlist_item = playlist_response['items'][0]
    playlist_publishedAt = datetime.datetime.fromisoformat(playlist_item['snippet']['publishedAt'].replace('Z', '+00:00'))
    
    # 取得した動画よりも新しい時期にアップロードされた動画を検索
    if publishedAt < playlist_publishedAt:
        video_response = youtube.search().list(
            part='id',
            q=' '.join(celebrities),
            type='video',
            videoCaption='closedCaption',
            videoDefinition='high',
            videoEmbeddable='true',
            videoType='episode',
            publishedAfter=playlist_publishedAt.isoformat() + 'Z',
            order='date'
        ).execute()
        
        if 'items' not in video_response:
            continue
        
        # 韓国語または日本語の字幕がある動画を抽出
        for item in video_response['items']:
            video_id = item['id']['videoId']
            
            caption_response = youtube.captions().list(
                part='snippet',
                videoId=video_id
            ).execute()
            
            if 'items' not in caption_response:
                continue
            
            for caption_item in caption_response['items']:
                if caption_item['snippet']['language'] in ['ko', 'ja'] and caption_item['snippet']['trackKind'] == 'standard':
                    newVideoIds.append(video_id)
                    break
