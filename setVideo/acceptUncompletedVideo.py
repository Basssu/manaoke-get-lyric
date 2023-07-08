import firebase_admin
from firebase_admin import firestore
from googleapiclient.discovery import build
import ConvenientFunctions as cf
import CaptionsToJson
import ToStorage
import ToFireStore
import urllib.request
import json
import pprint
import Notification

def makeFirebaseClient(flavor: str):
    creds = cf.firebaseCreds(flavor)
    domain = cf.firebaseDomain(flavor)
    firebase_admin.initialize_app(creds,{'storageBucket': f'gs://{domain}'})
    return firestore.client(), creds, domain

def getFlavor() -> str:
    return 'prod' if cf.answeredYes('flavorはどっち？(y = prod, n = stg)') else 'stg'

def videoIdLoop(db: firestore.firestore.Client, domain: str, flavor: str):
    while True:
        documentId = cf.inputText('ビデオのdocumentIdを入力してください(例: ko_ja_-L7eMf6Yf84)')
        setJson(documentId, db, domain, flavor)
        if not cf.answeredYes(f'引き続き別の動画の承認作業を続けますか？'):
            break

def setJson(documentId: str, db: firestore.firestore.Client, domain: str, flavor: str):
    doc_ref = db.collection('videos').document(documentId)
    doc = doc_ref.get()
    isUncompletedVideo = doc.get('isUncompletedVideo')
    isWaitingForReview = doc.get('isWaitingForReview')
    uncompletedJsonUrl = doc.get('uncompletedJsonUrl')
    uncompletedJsonUrl = doc.get('uncompletedJsonUrl')
    captionSubmitterUid = doc.get('captionSubmitterUid')
    if isUncompletedVideo != True or isWaitingForReview != True or uncompletedJsonUrl == None or captionSubmitterUid == None:
        print('この動画は承認作業ができません')
        print('isUncompletedVideo: ' + str(isUncompletedVideo))
        print('isWaitingForReview: ' + str(isWaitingForReview))
        print('uncompletedJsonUrl: ' + str(uncompletedJsonUrl))
        print('captionSubmitterUid: ' + str(captionSubmitterUid))
        return
    response = urllib.request.urlopen(uncompletedJsonUrl)
    uncompletedDictList: list[dict] = json.loads(response.read().decode())
    koreanCaptions = []
    japaneseCaptions = []
    hasJapaneseCaptions = uncompletedDictList[0]['ja'] != None
    for oneLine in uncompletedDictList:
        koreanCaptions.append({
            'time': oneLine['time'],
            'text': oneLine['ko'],
        })
        if hasJapaneseCaptions:
            japaneseCaptions.append({
                'time': oneLine['time'],
                'text': oneLine['ja'],
            })
    jsonData = CaptionsToJson.captionsToJson(
        koreanCaptions = koreanCaptions, 
        japaneseCaptions = japaneseCaptions,
        hasStrTime = True)
    url = ToStorage.toStorage(
        documentId = documentId,
        flavor = flavor,
        data = jsonData,
        availableCaptionLanguages = ['ko', 'ja'],
        domain = domain,
        firebaseAlreadyInitialized = True
    )
    document = ToFireStore.toFirestore(
        firestoreDict = {
            'isUncompletedVideo': False,
            'isWaitingForReview': False,
            'jsonUrl': url,
        }, 
        storageUrl = url, 
        flavor = flavor, 
        documentId = documentId,
        availableCaptionLanguages = ['ko', 'ja'],
        firebaseAlreadyInitialized = True
        )
    
    deviceTokens = Notification.uidsToDeviceTokens([captionSubmitterUid], db)
    Notification.sendNotificationByDeviceToken(
        deviceTokens = deviceTokens,
        title = 'あなたが送信した歌詞・字幕の承認が完了しました',
        body = 'ありがとうございます！これで他のオタクたちもこの動画を楽しめます！',
    )
    pprint.pprint(document)
    
    
def main():
    flavor = getFlavor()
    firebaseList = makeFirebaseClient(flavor)
    db = firebaseList[0]
    domain = firebaseList[2]
    videoIdLoop(db, domain, flavor)

if __name__ == '__main__':
    main()


