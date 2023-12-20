from firebase_admin import firestore
import firebase_admin
import ConvenientFunctions as cf
import datetime

def do():
    if not firebase_admin._apps:
        cf.initializeFirebase(cf.getFlavor())
    lastDoc = None
    db = firestore.client()
    query = db.collection('celebrities').order_by('popularity').limit(1)
    while 1:
        if lastDoc == None:
            docs = query.get()
        else:
            docs = query.start_after(lastDoc).get()
        if len(docs) == 0:
            break
        celebrityId = docs[0].reference.id
        print(f'処理中のcelebrityId: {celebrityId}')
        celebrity = docs[0].to_dict()
        lastDoc = docs[0]
        if celebrity['likedBy'] != None:
            likeCelebrityByUids(celebrity['likedBy'], celebrityId)
    return

def likeCelebrityByUids(uids: list[str], celebrityId: str):
    db = firestore.client()
    for uid in uids:
        likeCelebrityByUid(uid, celebrityId)
    return

def likeCelebrityByUid(uid: str, celebrityId: str):
    if isAlreadyLiked(uid, celebrityId):
        print(f'すでに {uid} は {celebrityId} をlikeしています')
        return
    db = firestore.client()
    likedCelebritiesRef = db.collection('users').document(uid).collection('likedCelebrities')
    likedCelebritiesRef.add({
        'celebrityId': celebrityId,
        'likedAt': datetime.datetime.now(),
    })
    return

def isAlreadyLiked(uid: str, celebrityId: str) -> bool:
    db = firestore.client()
    likedCelebritiesRef = db.collection('users').document(uid).collection('likedCelebrities')
    query = likedCelebritiesRef.where('celebrityId', '==', celebrityId).limit(1)
    docs = query.get()
    return len(docs) != 0


def main():
    do()

if __name__ == '__main__':
    main()