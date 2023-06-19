import firebase_admin
from firebase_admin import credentials, firestore
from googleapiclient.discovery import build
from apiKey import config
from googleapiclient.errors import HttpError
import re

def loop(selectedText):
    
    for i in range(len(selectedText)):
        token = selectedText[0:i + 1]
        if token not in tokenList:
            tokenList.append(token)

def remove_parentheses(string):
    # 括弧とその中身を含む正規表現パターンを定義する
    pattern = r'\([^()]*\)'

    # 正規表現パターンに一致する部分を空文字列で置換する
    result = re.sub(pattern, '', string)

    return result

flavor = "stg"
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
videos_docs = videos_ref.where('category', '==', 'music').get()

ngList = ["ver", "Ver", "VER", "feat", "Feat", "Prod", "prod", "mv", "MV"]

count = 0
# 各ドキュメントに対して処理を実行
for doc in videos_docs:
    print(count)
    # playlistIdとcelebritiesの取得
    title = doc.get('title')
    category = doc.get('category')
    if category != "music":
        continue

    tokenList = []
    titleWithoutKakko = remove_parentheses(title)
    print(titleWithoutKakko)
    insideKakko = []
    if title != titleWithoutKakko and title.count("(") == 1 and title.count(")") == 1:
        insideKakko = title[title.find("(")+1:title.find(")")]
        if not any((a in insideKakko) for a in ngList):
            loop(insideKakko)
            loop(insideKakko.upper())
            loop(insideKakko.lower())
            loop(insideKakko.capitalize())

    loop(titleWithoutKakko)
    loop(titleWithoutKakko.upper())
    loop(titleWithoutKakko.lower())
    loop(titleWithoutKakko.capitalize())
    

    try:
        doc_ref = db.collection('videos').document(doc.id)
        doc_ref.update({'tokenList': tokenList})
        print('done')
    except Exception as e:
        print('=== エラー内容 ===')
        print('type:' + str(type(e)))
        print('args:' + str(e.args))
        print('message:' + e.message)
        print('e自身:' + str(e))

    count = count + 1
