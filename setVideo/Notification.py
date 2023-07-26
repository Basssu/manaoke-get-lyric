from firebase_admin import firestore
from firebase_admin import messaging

def uidsToDeviceTokens(uids: list[str]) -> list[str]:
    db = firestore.client()
    deviceTokens = []
    for uid in uids:
        deviceToken = db.collection('users').document(uid).get().to_dict()['deviceToken']
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