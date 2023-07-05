import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
import os
import json
from uuid import uuid4

unvompletedVideosDir = 'uncompletedVideos'
videosDir = 'videos'
uncompletedVideosJsonFileName = 'caption.json'
videosJsonFileName = 'allData.json'

def toStorage(videoId: str, flavor: str, data: str, availableCaptionLanguages: list[str]) -> str:
    if flavor == "prod":
        cred = credentials.Certificate("../firebaseKey/manaoke-8c082-firebase-adminsdk-37ba1-6de8dec42f.json")
        domain = "manaoke-8c082.appspot.com"
    else:
        cred = credentials.Certificate("../firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")
        domain = "manaoke-stg.appspot.com"

    documentId = f'ko_ja_{videoId}'
    firebase_admin.initialize_app(cred,{'storageBucket': f'gs://{domain}'})
    if availableCaptionLanguages == ['ja']: #srtファイルのパスを格納
        dirName = unvompletedVideosDir
        fileName = uncompletedVideosJsonFileName
        filePath = uncompletedJsonFilePath(documentId, data)
    elif 'ja' in availableCaptionLanguages and 'ko' in availableCaptionLanguages: #jsonファイルのパスを格納
        dirName = videosDir
        fileName = videosJsonFileName
        filePath = jsonFilePath(documentId, data)

    bucket = storage.bucket(domain)
    blob = bucket.blob(filePath)
    token = uuid4()
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_filename(filePath) #ローカルファイルとFirebase storage, どっちも同じパスにしてます。ローカルはどうせ消すので。
    url = f'https://firebasestorage.googleapis.com/v0/b/{domain}/o/{dirName}%2F{documentId}%2F{fileName}?alt=media&token={token}'
    os.remove(filePath)
    return url

def uncompletedJsonFilePath(documentId: str, jsonData: str) -> str:
    dir = f'{unvompletedVideosDir}/{documentId}/'
    makeDirectory(dir)
    filePath = f'{dir}{uncompletedVideosJsonFileName}'
    jsonData = json.dumps(jsonData, indent=4, ensure_ascii=False)
    with open(filePath, 'w', encoding='utf-8') as f:
            f.write(jsonData)
    return filePath

def jsonFilePath(documentId: str, data: str) -> str:
    dir = f'{videosDir}/{documentId}/'
    makeDirectory(dir)
    filePath = f'{dir}{videosJsonFileName}'
    jsonData = json.dumps(data, indent=4, ensure_ascii=False)
    with open(filePath, 'w', encoding='utf-8') as f:
            f.write(jsonData)
    return filePath

def makeDirectory(dir: str) -> None:
    if not os.path.exists(dir):
        os.makedirs(dir)