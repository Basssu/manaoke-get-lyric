from firebase_admin import firestore
from firebase_admin import storage
import ConvenientFunctions as cf

def deleteVideosFromFirebase(videoIds: list[str], flavor: str):
    for videoId in videoIds:
        deleteVideoFromFirebase(videoId, flavor)

def deleteVideoFromFirebase(videoId: str, flavor: str):
    deleteDocumentFromFirebase('videos', videoId, willDeleteSubcollections=True)
    deleteFromFirebaseStorage(f'videos/{videoId}/allData.json', flavor)
    deleteFromFirebaseStorage(f'uncompletedVideos/{videoId}/caption.json', flavor)

def deleteDocumentFromFirebase(
        collectionName: str,
        documentId: str, 
        willDeleteSubcollections: bool = False, 
        ):
    db = firestore.client()
    doc_ref = db.collection(collectionName).document(documentId)
    doc_ref.delete()
    subcollections = doc_ref.collections()
    if willDeleteSubcollections: # サブコレクションの削除
        for subcollection in subcollections:
            deleteSubcollection(subcollection)

def deleteSubcollection(collectionRef):
    documents = collectionRef.stream()
    for document in documents:
        document.reference.delete()
    collectionRef.delete()

# 使用例
def deleteFromFirebaseStorage(path: str, flavor: str):
    domain = cf.firebaseDomain(flavor)
    bucket = storage.bucket(domain)
    blob = bucket.blob(path)
    try:
        blob.delete()
    except:
        print(f'{path}は存在しません')
    
def main():
    flavor = cf.getFlavor()
    cf.initializeFirebase(flavor)
    videoIds = cf.inputText('削除したい動画のvideoId(例: ko_ja_0rtV5esQT6I)を入力(複数の場合、","で区切る)').split(',')
    deleteVideosFromFirebase(videoIds, flavor)

if __name__ == '__main__':
    main()