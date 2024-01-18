import firebase_admin
from firebase_admin import storage
from uuid import uuid4
import os
import json
import ConvenientFunctions as cf

videosDir = 'videos'
jsonFileName = 'caption.json'

def newJsonUrl(videoId: str, data: str) -> str:
    if not firebase_admin._apps:
        cf.initializeFirebase(cf.getFlavor())
    filePath = jsonFilePath(videoId, data)
    app = firebase_admin.get_app()
    domain = app.options.get('storageBucket')
    bucket = storage.bucket(domain)
    blob = bucket.blob(filePath)
    token = uuid4()
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_filename(filePath)
    url = f'https://firebasestorage.googleapis.com/v0/b/{domain}/o/{videosDir}%2F{videoId}%2F{jsonFileName}?alt=media&token={token}'
    os.remove(filePath)
    return url

def jsonFilePath(videoId: str, data: str) -> str:
    dir = f'{videosDir}/{videoId}/'
    makeDirectory(dir)
    filePath = f'{dir}{jsonFileName}'
    jsonData = json.dumps(data, indent=4, ensure_ascii=False)
    with open(filePath, 'w', encoding='utf-8') as f:
            f.write(jsonData)
    return filePath

def makeDirectory(dir: str) -> None:
    if not os.path.exists(dir):
        os.makedirs(dir)