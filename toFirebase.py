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

with open(f'videos/{video_id}/firestore.json', 'r') as f:
    json_data = json.load(f)

firestoreDict = dict(json_data)
publishedAtDatetime = datetime.datetime.strptime(firestoreDict["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
# publishedAtTimestamp = Timestamp.from_datetime(publishedAtDatetime)
translatedFrom = firestoreDict["translatedFrom"]
translatedTo = firestoreDict["translatedTo"]

cred = credentials.Certificate("firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")
documentId = f'{translatedFrom}_{translatedTo}_{video_id}'
firebase_admin.initialize_app(cred,{'storageBucket': f'gs://manaoke-stg.appspot.com'})

path = f'videos/{video_id}/'
filename = f'videos/{documentId}/allData.json'
bucket = storage.bucket('manaoke-stg.appspot.com')
blob = bucket.blob(filename)
token = uuid4()
metadata = {"firebaseStorageDownloadTokens": token}
blob.metadata = metadata
blob.upload_from_filename(f'videos/{video_id}/allData.json')
url = f'https://firebasestorage.googleapis.com/v0/b/manaoke-stg.appspot.com/o/videos%2F{documentId}%2FallData.json?alt=media&token={token}'
print(url)

firestoreDict["jsonUrl"] = url

json_data = json.dumps(firestoreDict, indent=4, ensure_ascii=False)
with open(f'videos/{video_id}/firestore.json', 'w') as f:
    f.write(json_data)

firestoreDict["publishedAt"] = publishedAtDatetime
db= firestore.client()
doc_ref = db.collection('videos').document(documentId)
doc_ref.set(firestoreDict)
