import firebase_admin
from firebase_admin import storage
from uuid import uuid4
import os
import json
from . import convenient_functions as cf

VIDEOS_DIR = 'videos'
JSON_FILE_NAME = 'caption.json'

def new_json_url(videoId: str, data: str) -> str:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    file_path = json_file_path(videoId, data)
    app = firebase_admin.get_app()
    domain = app.options.get('storageBucket')
    bucket = storage.bucket(domain)
    blob = bucket.blob(file_path)
    token = uuid4()
    blob.metadata = {"firebaseStorageDownloadTokens": token}
    blob.upload_from_filename(file_path)
    url = f'https://firebasestorage.googleapis.com/v0/b/{domain}/o/{VIDEOS_DIR}%2F{videoId}%2F{JSON_FILE_NAME}?alt=media&token={token}'
    os.remove(file_path)
    return url

def json_file_path(video_id: str, data: str) -> str:
    dir = f'{VIDEOS_DIR}/{video_id}/'
    make_directory(dir)
    file_path = f'{dir}{JSON_FILE_NAME}'
    json_data = json.dumps(data, indent=4, ensure_ascii=False)
    with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_data)
    return file_path

def make_directory(dir: str) -> None:
    if not os.path.exists(dir):
        os.makedirs(dir)