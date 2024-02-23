from firebase_admin import firestore
from firebase_admin import storage
import ConvenientFunctions as cf

def delete_videos_from_firebase(videoIds: list[str], flavor: str):
    for videoId in videoIds:
        delete_video_from_firebase(videoId, flavor)

def delete_video_from_firebase(videoId: str, flavor: str):
    delete_document_from_firebase('videos', videoId, willDeleteSubcollections=True)
    delete_from_firebase_storage(f'videos/{videoId}/allData.json', flavor)
    delete_from_firebase_storage(f'videos/{videoId}/caption.json', flavor)
    delete_from_firebase_storage(f'uncompletedVideos/{videoId}/caption.json', flavor)

def delete_document_from_firebase(
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
            delete_subcollection(subcollection)

def delete_subcollection(collectionRef):
    documents = collectionRef.stream()
    for document in documents:
        document.reference.delete()
    collectionRef.delete()

# 使用例
def delete_from_firebase_storage(path: str, flavor: str):
    domain = cf.firebase_domain(flavor)
    bucket = storage.bucket(domain)
    blob = bucket.blob(path)
    try:
        blob.delete()
    except:
        print(f'{path}は存在しません')
    
def main():
    flavor = cf.get_flavor()
    cf.initialize_firebase(flavor)
    videoIds = cf.input_text('削除したい動画のvideoId(例: ko_ja_0rtV5esQT6I)を入力(複数の場合、","で区切る)').split(',')
    delete_videos_from_firebase(videoIds, flavor)

if __name__ == '__main__':
    main()