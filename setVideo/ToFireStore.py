from firebase_admin import firestore
from firebase_admin import credentials
import firebase_admin
import ConvenientFunctions as cf

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
        firestoreDict["jsonUrl"] = storageUrl
    elif 'ja' in availableCaptionLanguages and 'ko' in availableCaptionLanguages:
        firestoreDict["jsonUrl"] = storageUrl
        
    doc_ref = db.collection('videos').document(documentId)
    # ドキュメントの存在を確認
    doc = doc_ref.get()
    if doc.exists:
        # 既存のドキュメントがある場合はフィールドの値を更新
        doc_ref.update(firestoreDict)
    else:
        # 存在しない場合は新しいドキュメントを作成
        doc_ref.set(firestoreDict)
    return firestoreDict