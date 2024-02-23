from firebase_admin import firestore
import firebase_admin
import ConvenientFunctions as cf
import pprint
import datetime
from typing import Optional

def to_firestore(
        firestoreDict: dict, 
        flavor: str, 
        documentId: str,
        captionJsonUrl: Optional[str],
        ):
    if not firebase_admin._apps:
        cf.firebaseInitialize(flavor)
    db = firestore.client()
    print(captionJsonUrl)
    if captionJsonUrl != None:
        firestoreDict["captionJsonUrl"] = captionJsonUrl
        
    doc_ref = db.collection('videos').document(documentId)
    # ドキュメントの存在を確認
    doc = doc_ref.get()
    if doc.exists:
        print('既存のドキュメントが存在します')
        # 既存のドキュメントがある場合はフィールドの値を更新
        delete_keys_from_dict( # 以下のフィールドは更新しない
            firestoreDict, 
            [
                'isUncompletedVideo', 
                'isWaitingForReview', 
                'uncompletedJsonUrl'
                ]
            )
        doc_ref.update(firestoreDict)
    else:
        # 存在しない場合は新しいドキュメントを作成
        doc_ref.set(firestoreDict)
    return firestoreDict

def delete_keys_from_dict(dict: dict, keys: list[str]):
    for key in keys:
        if key in dict:
            del dict[key]
    return dict

def celebrity_liker_uids(celebrityId: str) -> list[str]:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    celebrityDocs = db.collection_group('likedCelebrities').where('celebrityId', '==', celebrityId).get()
    uids = []
    for celebrityDoc in celebrityDocs:
        uids.append(celebrityDoc.reference.parent.parent.id)
    return list(set(uids)) #重複削除(念の為)

def completed_videos(youtubeVideoIds: list[str]) -> list[str]:
    result = []
    for youtubeVideoId in youtubeVideoIds:
        if is_completed_video(youtubeVideoId):
            result.append(youtubeVideoId)
    return result

def is_completed_video(youtubeVideoId: str) -> bool:
    videoDocDict = fetch_video_by_youtube_video_id(youtubeVideoId).to_dict()
    if not 'isUncompletedVideo' in videoDocDict or videoDocDict['isUncompletedVideo'] == None:
        return False
    if videoDocDict['isUncompletedVideo'] == False:
        return True
    return False

def fetch_jasrac_code_list():
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    videoDocs = db.collection('videos').order_by('jasracCode').get()
    print('取得したドキュメント数')
    print(len(videoDocs))
    return videoDocs

def fetch_user_by_uid(uid: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    userDoc = db.collection('users').document(uid).get()
    return userDoc

def fetch_user_birthday_by_uids(uid: str) -> Optional[datetime.datetime]:
    userDoc = fetch_user_by_uid(uid)
    birthday = userDoc.to_dict().get('birthday')
    return birthday

def fetch_video_by_youtube_video_id(youtubeVideoId: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    videos_ref = db.collection('videos')
    query = videos_ref.where('videoId', '==', youtubeVideoId).limit(1)
    list = query.get()
    print('長さ')
    print(len(list))
    return list[0]

def is_music_notification_enabled(uid: str, category: str) -> bool:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    docRef = db.collection('users').document(uid)
    fieldName = 'isMusicNotificationEnabled'
    if category == 'video':
        fieldName = 'isVideoNotificationEnabled'
    isNotificationEnabled = docRef.get().to_dict().get(fieldName)
    return isNotificationEnabled if isNotificationEnabled != None else False

def fetch_ranged_users(start: datetime.datetime, end: datetime.datetime) -> list[dict]:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    lastDoc = None
    db = firestore.client()
    users = []
    query = db.collection('users').where('createdAt', '>=', start).order_by('createdAt').limit(1)
    while 1:
        if lastDoc == None:
            docs = query.get()
            print('読み込み')
        else:
            docs = query.start_after(lastDoc).get()
            print('読み込み')
        if len(docs) == 0:
            break
        user = docs[0].to_dict()
        if user['createdAt'] >= end:
            break
        lastDoc = docs[0]
        if user['birthday'] != None:
            users.append(user)
    return users
    

def fetch_videos_by_youtube_video_ids(youtubeVideoIds: list[str]):
    result = []
    for i in range(len(youtubeVideoIds)):
        result.append(fetch_video_by_youtube_video_id(youtubeVideoIds[i]))
    return result

def fetch_doc_by_collection_name_and_documentId(collectionName: str, documentId: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    docRef = db.collection(collectionName).document(documentId)
    return docRef.get()
