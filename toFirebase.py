import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import json
import sys
import datetime
from firebase_admin import credentials,initialize_app,storage
from google.cloud import firestore
from google.protobuf.timestamp_pb2 import Timestamp
from uuid import uuid4

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

params = sys.argv[1:]
video_id = params[0]
flavor = params[1]
print(flavor)

with open(f'videos/{video_id}/firestore.json', 'r') as f:
    json_data = json.load(f)

firestoreDict = dict(json_data)
publishedAtDatetime = datetime.datetime.strptime(firestoreDict["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
# publishedAtTimestamp = Timestamp.from_datetime(publishedAtDatetime)
translatedFrom = firestoreDict["translatedFrom"]
translatedTo = firestoreDict["translatedTo"]

if flavor == "prod":
    cred = credentials.Certificate("firebaseKey/manaoke-8c082-firebase-adminsdk-37ba1-6de8dec42f.json")
    domain = "manaoke-8c082.appspot.com"
else:
    cred = credentials.Certificate("firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")
    domain = "manaoke-stg.appspot.com"

documentId = f'{translatedFrom}_{translatedTo}_{video_id}'

firebase_admin.initialize_app(cred,{'storageBucket': f'gs://{domain}'})

a = open(f'videos/{video_id}/allData.json', 'r')
data = a.read()
a.close()

# with open(f'videos/{video_id}/allData.json', 'r') as f:
#     all_json_data = json.load(f)

# alldDataDict = dict(all_json_data)
if data == '[]':
    print("配列が空のため中断します")
    sys.exit()

path = f'videos/{video_id}/'
filename = f'videos/{documentId}/allData.json'
bucket = storage.bucket(domain)
blob = bucket.blob(filename)
token = uuid4()
metadata = {"firebaseStorageDownloadTokens": token}
blob.metadata = metadata
blob.upload_from_filename(f'videos/{video_id}/allData.json')
url = f'https://firebasestorage.googleapis.com/v0/b/{domain}/o/videos%2F{documentId}%2FallData.json?alt=media&token={token}'
print(url)

firestoreDict["jsonUrl"] = url

json_data = json.dumps(firestoreDict, indent=4, ensure_ascii=False)
with open(f'videos/{video_id}/firestore.json', 'w') as f:
    f.write(json_data)

firestoreDict["publishedAt"] = publishedAtDatetime
firestoreDict["updatedAt"] = datetime.datetime.now()
db= firestore.client()
doc_ref = db.collection('videos').document(documentId)

# ドキュメントの存在を確認
doc = doc_ref.get()
if doc.exists:
    # 既存のドキュメントがある場合はフィールドの値を更新
    doc_ref.update(firestoreDict)
else:
    # 存在しない場合は新しいドキュメントを作成
    doc_ref.set(firestoreDict)