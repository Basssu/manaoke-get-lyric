from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin

def toFirestore(firestoreDict: dict, storageUrl: str, flavor: str):
    # if flavor == "prod":
    #     creds = credentials.Certificate("firebaseKey/manaoke-8c082-firebase-adminsdk-37ba1-6de8dec42f.json")
    #     domain = "manaoke-8c082.appspot.com"
    # else:
    #     creds = credentials.Certificate("firebaseKey/manaoke-stg-firebase-adminsdk-emiky-167e3b7113.json")
    #     domain = "manaoke-stg.appspot.com"
    # firebase_admin.initialize_app(creds)
    db = firestore.client()
    firestoreDict["srtUrl" if firestoreDict["isUncompletedVideo"] else "jsonUrl"] = storageUrl
    doc_ref = db.collection('videos').document(f'ko_ja_{firestoreDict["videoId"]}')
    # ドキュメントの存在を確認
    doc = doc_ref.get()
    if doc.exists:
        # 既存のドキュメントがある場合はフィールドの値を更新
        doc_ref.update(firestoreDict)
    else:
        # 存在しない場合は新しいドキュメントを作成
        doc_ref.set(firestoreDict)
    return firestoreDict