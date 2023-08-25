from firebase_admin import firestore
from firebase_admin import messaging
from typing import Optional
import ConvenientFunctions
import ToFireStore

def uidsToDeviceTokens(uids: list[str]) -> list[str]:
    db = firestore.client()
    deviceTokens = []
    for uid in uids:
        try:
            deviceToken = db.collection('users').document(uid).get().to_dict()['deviceToken']
        except:
            deviceToken = None
        if(deviceToken != None):
            deviceTokens.append(deviceToken)

    return deviceTokens

def sendNotificationByDeviceToken(deviceTokens: list[str], title: str, body: str):
    print(f'{len(deviceTokens)}人に通知を送信します。')
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            tokens=deviceTokens,
        )
        response = messaging.send_multicast(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print('=== エラー内容 ===')
        print('type:' + str(type(e)))
        print('args:' + str(e.args))
        print('e自身:' + str(e))

def sendNotificationToCelebrityLikers(celebrityId: str, body: Optional[str] = None):
    CelebrityDocDict = ToFireStore.fetchDocbyCollectionNameAndDocumentId("celebrities", celebrityId).to_dict()
    if CelebrityDocDict == None or not 'likedBy' in CelebrityDocDict or CelebrityDocDict['likedBy'] == None:
        print(f'celebrities/{celebrityId} のlikedByをうまく取得できませんでした。')
        return
    likedBy = CelebrityDocDict['likedBy']
    deviceTokens = uidsToDeviceTokens(likedBy)
    if body == None:
        body = '韓国語を理解しながら楽しもう！'
    print(f'{CelebrityDocDict["name"]}をお気に入り登録している人に通知を送信します' if CelebrityDocDict['name'] != None else '')
    sendNotificationByDeviceToken(deviceTokens, f'{CelebrityDocDict["name"]}の新着動画', body)

def sendCelebrityLikersByMusicVideoDocs(musicVideoDocs: list[firestore.DocumentSnapshot]):
    for musicVideoDoc in musicVideoDocs:
        musicVideoDocDict = musicVideoDoc.to_dict()
        if musicVideoDoc == None or not 'celebrityIds' in musicVideoDocDict or musicVideoDocDict['celebrityIds'] == None:
            continue
        for celebrityId in musicVideoDocDict['celebrityIds']:
            body = f'「{musicVideoDocDict["title"]}」を韓国語で歌おう♫'
            sendNotificationToCelebrityLikers(celebrityId, body)

def sendToSeriesLiker(seriesId: str):
    seriesDocDict = ToFireStore.fetchDocbyCollectionNameAndDocumentId("series", seriesId).to_dict()
    if seriesDocDict == None or not 'likedBy' in seriesDocDict or seriesDocDict['likedBy'] == None:
        print(f'series/{seriesId} のlikedByをうまく取得できませんでした。')
        return
    likedBy = seriesDocDict['likedBy']
    deviceTokens = uidsToDeviceTokens(likedBy)
    print(f'{seriesDocDict["name"]}をお気に入り登録している人に通知を送信します' if seriesDocDict['name'] != None else '')
    sendNotificationByDeviceToken(deviceTokens, 'お気に入りシリーズの新着動画', f'韓国語を理解しながら「{seriesDocDict["name"]}」を楽しもう！')