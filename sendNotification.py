import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from firebase_admin import firestore
import sys


flavor = "prod"
type = "celebrities" #"series"か"celebrities"が入る
content_id = "mBJtnYpwgVbCxoOkMKSV" #seriesIdかcelebrityIdが入る

if flavor == "prod":
    cred = credentials.Certificate("firebaseKey/manaoke-8c082-firebase-adminsdk-37ba1-6de8dec42f.json")
    domain = "manaoke-8c082.appspot.com"
else:
    cred = credentials.Certificate("firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")
    domain = "manaoke-stg.appspot.com"
# Firebaseアプリの初期化

firebase_admin.initialize_app(cred)

# Firestoreクライアントの取得
db = firestore.client()

# body = "韓国語の意味を理解しながら推しの動画を見よう！"
body = "新曲「Party O’Clock」を韓国語で歌おう！"
if type == "series":
    title = "お気に入りシリーズ新着動画"
else:
    # 取得するドキュメントのパス（例：'collection/document_id'）
    document_path = f'{"celebrities"}/{content_id}'

    # ドキュメントの参照
    doc_ref = db.document(document_path)

    # ドキュメントのデータ取得
    doc_data = doc_ref.get().to_dict()

    # "name" フィールドの値取得
    name = doc_data.get('name')
    title = f'{name}の新着動画'

# ドキュメント名
document_name = f'{type}/{content_id}'

# ドキュメントの参照
doc_ref = db.document(document_name)

# ドキュメントのデータ取得
doc_data = doc_ref.get().to_dict()

# likedByフィールドの値取得
liked_by = doc_data.get('likedBy')

if liked_by == None:
    sys.exit()

# "users"コレクションの参照
users_ref = db.collection('users')

# "deviceToken"フィールドが格納される新たな文字列の配列
device_token_list = []

# "liked_by"文字列配列の各要素に対して処理を行う
for user_id in liked_by:
    # ドキュメントの参照
    doc_ref = users_ref.document(user_id)

    # ドキュメントのデータ取得
    doc_data = doc_ref.get().to_dict()

    # "deviceToken"フィールドの値取得
    device_token = doc_data.get('deviceToken')

    # "deviceToken"フィールドがnullでない場合、"device_token_list"に追加
    if device_token is not None:
        device_token_list.append(device_token)

print(len(device_token_list))

for device_token in device_token_list:
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=device_token
        )
        print('エラーではない')
        print(device_token)
    except:
        print('エラー')
        print(device_token)

# 通知の送信
response = messaging.send(message)

print('通知が送信されました:', response)
