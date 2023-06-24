import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
import os
import json
from uuid import uuid4

def toStorage(videoId: str, flavor: str, data: str, isUncompletedVideo: bool) -> str:
    if flavor == "prod":
        cred = credentials.Certificate("../firebaseKey/manaoke-8c082-firebase-adminsdk-37ba1-6de8dec42f.json")
        domain = "manaoke-8c082.appspot.com"
    else:
        cred = credentials.Certificate("../firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")
        domain = "manaoke-stg.appspot.com"

    documentId = f'ko_ja_{videoId}'
    firebase_admin.initialize_app(cred,{'storageBucket': f'gs://{domain}'})
    if isUncompletedVideo: #srtファイルのパスを格納
        filename = srtFilePath(documentId, data)
    else: #jsonファイルのパスを格納
        filename = jsonFilePath(documentId, data)

    bucket = storage.bucket(domain)
    blob = bucket.blob(filename)
    token = uuid4()
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_filename(filename) #ローカルファイルとFirebase storage, どっちも同じパスにしてます。ローカルはどうせ消すので。
    url = f'https://firebasestorage.googleapis.com/v0/b/{domain}/o/videos%2F{documentId}%2FallData.json?alt=media&token={token}'
    os.remove(filename)
    return url

def srtFilePath(documentId: str, srtData: str) -> str:
    dir = f'uncompletedVideos/{documentId}/'
    makeDirectory(dir)
    filename = f'{dir}caption.srt'
    with open(filename, 'w', encoding='utf-8') as f:
            f.write(srtData)
    return filename

def jsonFilePath(documentId: str, data: str) -> str:
    dir = f'videos/{documentId}/'
    makeDirectory(dir)
    filename = f'{dir}allData.json'
    jsonData = json.dumps(data, indent=4, ensure_ascii=False)
    with open(filename, 'w', encoding='utf-8') as f:
            f.write(jsonData)
    return filename

def makeDirectory(dir: str) -> None:
    if not os.path.exists(dir):
        os.makedirs(dir)