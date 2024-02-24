from firebase_admin import firestore
import firebase_admin
from . import convenient_functions as cf
from typing import Optional

LAST_VIDEO_ID = None

def get_video_doc_byId() -> Optional[firestore.DocumentSnapshot]:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    doc = db.collection('videos').document(LAST_VIDEO_ID).get()
    if doc.exists:
        return doc
    else:
        return None

def do():
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    last_doc = get_video_doc_byId()
    db = firestore.client()
    query = db.collection('videos').order_by('publishedAt').limit(1)
    count = 0
    while True:
        print(f'count: {count}')
        count = count + 1
        if last_doc == None:
            docs = query.get()
        else:
            docs = query.start_after(last_doc).get()
        if len(docs) == 0:
            break
        video_id = docs[0].reference.id
        print(f'処理中のvideoId: {video_id}')
        video = docs[0].to_dict()
        last_doc = docs[0]
        if video.get('isUncompletedVideo') == False:
            db.collection('videos').document(video_id).update({'isVerified': True})
        else:
            db.collection('videos').document(video_id).update({'isVerified': False})
    return

def main():
    do()

if __name__ == '__main__':
    main()