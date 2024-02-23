from firebase_admin import firestore
import firebase_admin
import ConvenientFunctions as cf
import pprint
import datetime
from typing import Optional

def toFirestore(
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
        deleteKeysFromDict( # 以下のフィールドは更新しない
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

def afterReview(dict: dict, documentId: str):
    db = firestore.client()
    doc_ref = db.collection('videos').document(documentId)
    doc_ref.update(dict)
    print('firestoreに反映しました')
    pprint.pprint(dict)
    return 

def deleteKeysFromDict(dict: dict, keys: list[str]):
    for key in keys:
        if key in dict:
            del dict[key]
    return dict

def celebrityLikerUids(celebrityId: str) -> list[str]:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.getFlavor())
    db = firestore.client()
    celebrityDocs = db.collection_group('likedCelebrities').where('celebrityId', '==', celebrityId).get()
    uids = []
    for celebrityDoc in celebrityDocs:
        uids.append(celebrityDoc.reference.parent.parent.id)
    return list(set(uids)) #重複削除(念の為)

def completedVideos(youtubeVideoIds: list[str]) -> list[str]:
    result = []
    for youtubeVideoId in youtubeVideoIds:
        if isCompletedVideo(youtubeVideoId):
            result.append(youtubeVideoId)
    return result

def isCompletedVideo(youtubeVideoId: str) -> bool:
    videoDocDict = fetchVideoByYoutubeVideoId(youtubeVideoId).to_dict()
    if not 'isUncompletedVideo' in videoDocDict or videoDocDict['isUncompletedVideo'] == None:
        return False
    if videoDocDict['isUncompletedVideo'] == False:
        return True
    return False

def fetchJasracCodeList():
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.getFlavor())
    db = firestore.client()
    videoDocs = db.collection('videos').order_by('jasracCode').get()
    print('取得したドキュメント数')
    print(len(videoDocs))
    return videoDocs

def fetchUserByUid(uid: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.getFlavor())
    db = firestore.client()
    userDoc = db.collection('users').document(uid).get()
    return userDoc

def fetchUserBirthdayByUids(uid: str) -> Optional[datetime.datetime]:
    userDoc = fetchUserByUid(uid)
    birthday = userDoc.to_dict().get('birthday')
    return birthday

def fetchVideoByYoutubeVideoId(youtubeVideoId: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.getFlavor())
    db = firestore.client()
    videos_ref = db.collection('videos')
    query = videos_ref.where('videoId', '==', youtubeVideoId).limit(1)
    list = query.get()
    print('長さ')
    print(len(list))
    return list[0]

def isMusicNotificationEnabled(uid: str, category: str) -> bool:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.getFlavor())
    db = firestore.client()
    docRef = db.collection('users').document(uid)
    fieldName = 'isMusicNotificationEnabled'
    if category == 'video':
        fieldName = 'isVideoNotificationEnabled'
    isNotificationEnabled = docRef.get().to_dict().get(fieldName)
    return isNotificationEnabled if isNotificationEnabled != None else False

def fetchRangedUsers(start: datetime.datetime, end: datetime.datetime) -> list[dict]:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.getFlavor())
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
    

def fetchVideosByYouttubeVideoIds(youtubeVideoIds: list[str]):
    result = []
    for i in range(len(youtubeVideoIds)):
        result.append(fetchVideoByYoutubeVideoId(youtubeVideoIds[i]))
    return result

def fetchDocbyCollectionNameAndDocumentId(collectionName: str, documentId: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.getFlavor())
    db = firestore.client()
    docRef = db.collection(collectionName).document(documentId)
    return docRef.get()

def updatedSeriesIdList(youtubeVideoIds: list[str]) -> list[str]:
    seriesIds = []
    for youtubeVideoId in youtubeVideoIds:
        videoDocDict = fetchVideoByYoutubeVideoId(youtubeVideoId).to_dict()
        if not 'playlistIds' in videoDocDict or videoDocDict['playlistIds'] == None:
            continue
        seriesIds.extend(videoDocDict['playlistIds'])
    return (set(seriesIds))