from firebase_admin import firestore
from firebase_admin import messaging
from typing import Optional
from . import to_firestore as to_firestore

def uids_to_device_tokens(uids: list[str]) -> list[str]:
    db = firestore.client()
    device_tokens = []
    for uid in uids:
        try:
            device_token = db.collection('users').document(uid).get().to_dict()['deviceToken']
        except:
            device_token = None
        if(device_token != None):
            device_tokens.append(device_token)

    return device_tokens

def send_notification_by_device_token(
        device_tokens: list[str], 
        title: str, 
        body: str,
        data: dict[str, str] = {},
        ):
    print(f'合計{len(device_tokens)}人に通知を送信します。')
    try:
        sendable_tokens = []
        for i in range(len(device_tokens)): # MulticastMessageで一度に送れるのは500人までのため
            sendable_tokens.append(device_tokens[i])
            if (i + 1) % 500 != 0 and i != len(device_tokens) - 1:
                continue
            message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
                ),
            tokens=sendable_tokens,
            data=data,
            )
            response = messaging.send_multicast(message)
            print('Successfully sent message:', response)
            print(f'{len(device_tokens)}人中の{len(sendable_tokens)}人に送信完了。')
            sendable_tokens.clear()
    except Exception as e:
        print('=== エラー内容 ===')
        print('type:' + str(type(e)))
        print('args:' + str(e.args))
        print('e自身:' + str(e))

def send_notification_to_celebrity_likers(
    celebrity_id: str, 
    body: Optional[str] = None,
    category: Optional[str] = None,
    id: Optional[str] = None,
    ):
    celebrity_doc_dict = to_firestore.fetch_doc_by_collection_name_and_documentId("celebrities", celebrity_id).to_dict()
    liked_by = to_firestore.celebrity_liker_uids(celebrity_id)
    uids = uids_to_send_notification(liked_by, category)
    device_tokens = uids_to_device_tokens(uids)
    if body == None:
        body = '韓国語を理解しながら楽しもう！'
    title = f'{celebrity_doc_dict["name"]}の新着動画'
    if category == 'music':
        title =  f'{celebrity_doc_dict["name"]}の曲が追加されました！'
    elif category == 'video':
        title = f'{celebrity_doc_dict["name"]}の新着エピソード'
    print(f'{celebrity_doc_dict["name"]}をお気に入り登録している人に通知を送信します' if celebrity_doc_dict['name'] != None else '')
    send_notification_by_device_token(device_tokens, title, body, {'id': id, 'route': 'video'} if id != None else {})

def send_celebrity_likers_by_video_docs(video_docs: list[firestore.DocumentSnapshot]):
    for video_doc in video_docs:
        video_doc_dict = video_doc.to_dict()
        celebrity_ids = video_doc_dict.get('celebrityIds')
        category = video_doc_dict.get('category')
        body = ''
        if category == 'music':
            body = body = f'「{video_doc_dict["title"]}」を韓国語で歌おう♫'
        else:
            body = f'「{video_doc_dict["title"]}」を韓国語で楽しもう！'
        for celebrity_id in celebrity_ids if celebrity_ids != None else [] :
            send_notification_to_celebrity_likers(celebrity_id, body, category, video_doc.id)
            
def uids_to_send_notification(uids: list[str], category: str):
    result = []
    for uid in uids:
        if to_firestore.is_music_notification_enabled(uid, category):
            result.append(uid)
    return result
