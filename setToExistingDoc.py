import firebase_admin
from firebase_admin import credentials, firestore
from googleapiclient.discovery import build
from apiKey import config
from googleapiclient.errors import HttpError


flavor = "prod"
video_ids = []
DEVELOPER_KEY = config.YOUTUBE_API_KEY

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
videos_ref = db.collection('videos')
videos_docs = videos_ref.get()

count = 0
# 各ドキュメントに対して処理を実行
for doc in videos_docs:
    print(count)
    # playlistIdとcelebritiesの取得
    videoId = doc.get('videoId')
    if videoId == None:
        continue
    
    # videos.listメソッドの実行
    videos_response = youtube.videos().list(
        part='snippet',
        id=videoId
    ).execute()

    try:
        # 動画のデフォルトオーディオ言語を取得
        default_audio_language = videos_response['items'][0]['snippet']['defaultAudioLanguage']
        doc_ref = db.collection('videos').document(doc.id)
        doc_ref.update({'defaultAudioLanguage': default_audio_language})
    except Exception as e:
        print('=== エラー内容 ===')
        print('type:' + str(type(e)))
        print('args:' + str(e.args))
        print('message:' + e.message)
        print('e自身:' + str(e))

    count = count + 1
