from firebase_admin import firestore
from firebase_admin import storage
import convenient_functions as cf

def delete_videos_from_firebase(videoIds: list[str], flavor: str):
    for videoId in videoIds:
        delete_video_from_firebase(videoId, flavor)

def delete_video_from_firebase(videoId: str, flavor: str):
    delete_document_from_firebase('videos', videoId, will_delete_subcollections=True)
    delete_from_firebase_storage(f'videos/{videoId}/allData.json', flavor)
    delete_from_firebase_storage(f'videos/{videoId}/caption.json', flavor)
    delete_from_firebase_storage(f'uncompletedVideos/{videoId}/caption.json', flavor)

def delete_document_from_firebase(
        collection_name: str,
        document_id: str, 
        will_delete_subcollections: bool = False, 
        ):
    db = firestore.client()
    doc_ref = db.collection(collection_name).document(document_id)
    doc_ref.delete()
    subcollections = doc_ref.collections()
    if will_delete_subcollections: # サブコレクションの削除
        for subcollection in subcollections:
            delete_subcollection(subcollection)

def delete_subcollection(collection_ref):
    documents = collection_ref.stream()
    for document in documents:
        document.reference.delete()
    collection_ref.delete()

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