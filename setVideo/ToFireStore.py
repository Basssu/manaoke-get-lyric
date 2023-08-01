from firebase_admin import firestore
import firebase_admin
import ConvenientFunctions as cf
import pprint

def toFirestore(
        firestoreDict: dict, 
        storageUrl: str, 
        flavor: str, 
        documentId: str,
        availableCaptionLanguages: str,
        ):
    if not firebase_admin._apps:
        cf.firebaseInitialize(flavor)
    db = firestore.client()
    if availableCaptionLanguages == ['ja']:
        firestoreDict["uncompletedJsonUrl"] = storageUrl
    elif availableCaptionLanguages == ['ko']:
        firestoreDict["uncompletedJsonUrl"] = storageUrl
    elif 'ja' in availableCaptionLanguages and 'ko' in availableCaptionLanguages:
        firestoreDict["jsonUrl"] = storageUrl
        
    doc_ref = db.collection('videos').document(documentId)
    # ドキュメントの存在を確認
    doc = doc_ref.get()
    if doc.exists:
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

def fetchVideoByYoutubeVideoId(youtubeVideoId: str):
    if not firebase_admin._apps:
        cf.initializeFirebase(cf.getFlavor())
    db = firestore.client()
    videos_ref = db.collection('videos')
    query = videos_ref.where('videoId', '==', youtubeVideoId).limit(1)
    list = query.get()
    print('長さ')
    print(len(list))
    return list[0]

def fetchDocbyCollectionNameAndDocumentId(collectionName: str, documentId: str):
    if not firebase_admin._apps:
        cf.initializeFirebase(cf.getFlavor())
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