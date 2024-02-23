from firebase_admin import firestore
from firebase_admin import messaging
from typing import Optional
import ToFireStore

def uids_to_device_tokens(uids: list[str]) -> list[str]:
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

def send_notification_by_device_token(
        deviceTokens: list[str], 
        title: str, 
        body: str,
        data: dict[str, str] = {},
        ):
    print(f'合計{len(deviceTokens)}人に通知を送信します。')
    try:
        sendableTokens = []
        for i in range(len(deviceTokens)): # MulticastMessageで一度に送れるのは500人までのため
            sendableTokens.append(deviceTokens[i])
            if (i + 1) % 500 != 0 and i != len(deviceTokens) - 1:
                continue
            message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
                ),
            tokens=sendableTokens,
            data=data,
            )
            response = messaging.send_multicast(message)
            print('Successfully sent message:', response)
            print(f'{len(deviceTokens)}人中の{len(sendableTokens)}人に送信完了。')
            sendableTokens.clear()
    except Exception as e:
        print('=== エラー内容 ===')
        print('type:' + str(type(e)))
        print('args:' + str(e.args))
        print('e自身:' + str(e))

def send_notification_to_celebrity_likers(
    celebrityId: str, 
    body: Optional[str] = None,
    category: Optional[str] = None,
    id: Optional[str] = None,
    ):
    CelebrityDocDict = ToFireStore.fetch_doc_by_collection_name_and_documentId("celebrities", celebrityId).to_dict()
    likedBy = ToFireStore.celebrity_liker_uids(celebrityId)
    uids = uids_to_send_notification(likedBy, category)
    deviceTokens = uids_to_device_tokens(uids)
    if body == None:
        body = '韓国語を理解しながら楽しもう！'
    title = f'{CelebrityDocDict["name"]}の新着動画'
    if category == 'music':
        title =  f'{CelebrityDocDict["name"]}の曲が追加されました！'
    elif category == 'video':
        title = f'{CelebrityDocDict["name"]}の新着エピソード'
    print(f'{CelebrityDocDict["name"]}をお気に入り登録している人に通知を送信します' if CelebrityDocDict['name'] != None else '')
    send_notification_by_device_token(deviceTokens, title, body, {'id': id, 'route': 'video'} if id != None else {})

def send_celebrity_likers_by_video_docs(videoDocs: list[firestore.DocumentSnapshot]):
    for videoDoc in videoDocs:
        videoDocDict = videoDoc.to_dict()
        celebrityIds = videoDocDict.get('celebrityIds')
        category = videoDocDict.get('category')
        body = ''
        if category == 'music':
            body = body = f'「{videoDocDict["title"]}」を韓国語で歌おう♫'
        else:
            body = f'「{videoDocDict["title"]}」を韓国語で楽しもう！'
        for celebrityId in celebrityIds if celebrityIds != None else [] :
            send_notification_to_celebrity_likers(celebrityId, body, category, videoDoc.id)
            
def uids_to_send_notification(uids: list[str], category: str):
    result = []
    for uid in uids:
        if ToFireStore.is_music_notification_enabled(uid, category):
            result.append(uid)
    return result
