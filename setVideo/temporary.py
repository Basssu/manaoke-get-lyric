from firebase_admin import firestore
import firebase_admin
import ConvenientFunctions as cf
from typing import Optional

videosDir = 'videos'
jsonFileName = 'caption.json'
lastVideoId = None

def getVideoDocById() -> Optional[firestore.DocumentSnapshot]:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    doc = db.collection('videos').document(lastVideoId).get()
    if doc.exists:
        return doc
    else:
        return None

def do():
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    lastDoc = getVideoDocById()
    db = firestore.client()
    query = db.collection('videos').order_by('publishedAt').limit(1)
    count = 0
    while True:
        print(f'count: {count}')
        count = count + 1
        if lastDoc == None:
            docs = query.get()
        else:
            docs = query.start_after(lastDoc).get()
        if len(docs) == 0:
            break
        videoId = docs[0].reference.id
        print(f'処理中のvideoId: {videoId}')
        video = docs[0].to_dict()
        lastDoc = docs[0]
        if video.get('isUncompletedVideo') == False:
            db.collection('videos').document(videoId).update({'isVerified': True})
        else:
            db.collection('videos').document(videoId).update({'isVerified': False})
    return

def main():
    do()

if __name__ == '__main__':
    main()