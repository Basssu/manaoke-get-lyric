from firebase_admin import firestore
import firebase_admin
import ConvenientFunctions as cf
import pprint
import datetime
from typing import Optional

def to_firestore(
        firestore_dict: dict, 
        flavor: str, 
        document_id: str,
        caption_json_url: Optional[str],
        ):
    if not firebase_admin._apps:
        cf.firebaseInitialize(flavor)
    db = firestore.client()
    print(caption_json_url)
    if caption_json_url != None:
        firestore_dict["captionJsonUrl"] = caption_json_url
        
    doc_ref = db.collection('videos').document(document_id)
    # ドキュメントの存在を確認
    doc = doc_ref.get()
    if doc.exists:
        print('既存のドキュメントが存在します')
        # 既存のドキュメントがある場合はフィールドの値を更新
        delete_keys_from_dict( # 以下のフィールドは更新しない
            firestore_dict, 
            [
                'isUncompletedVideo', 
                'isWaitingForReview', 
                'uncompletedJsonUrl'
                ]
            )
        doc_ref.update(firestore_dict)
    else:
        # 存在しない場合は新しいドキュメントを作成
        doc_ref.set(firestore_dict)
    return firestore_dict

def delete_keys_from_dict(dict: dict, keys: list[str]):
    for key in keys:
        if key in dict:
            del dict[key]
    return dict

def celebrity_liker_uids(celebrity_id: str) -> list[str]:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    celebrity_docs = db.collection_group('likedCelebrities').where('celebrityId', '==', celebrity_id).get()
    uids = []
    for celebrity_doc in celebrity_docs:
        uids.append(celebrity_doc.reference.parent.parent.id)
    return list(set(uids)) #重複削除(念の為)

def completed_videos(youtube_video_ids: list[str]) -> list[str]:
    result = []
    for youtube_video_id in youtube_video_ids:
        if is_completed_video(youtube_video_id):
            result.append(youtube_video_id)
    return result

def is_completed_video(youtube_video_id: str) -> bool:
    video_doc_dict = fetch_video_by_youtube_video_id(youtube_video_id).to_dict()
    if not 'isUncompletedVideo' in video_doc_dict or video_doc_dict['isUncompletedVideo'] == None:
        return False
    if video_doc_dict['isUncompletedVideo'] == False:
        return True
    return False

def fetch_jasrac_code_list():
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    video_docs = db.collection('videos').order_by('jasracCode').get()
    print('取得したドキュメント数')
    print(len(video_docs))
    return video_docs

def fetch_user_by_uid(uid: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    user_doc = db.collection('users').document(uid).get()
    return user_doc

def fetch_user_birthday_by_uids(uid: str) -> Optional[datetime.datetime]:
    user_doc = fetch_user_by_uid(uid)
    birthday = user_doc.to_dict().get('birthday')
    return birthday

def fetch_video_by_youtube_video_id(youtube_video_id: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    videos_ref = db.collection('videos')
    query = videos_ref.where('videoId', '==', youtube_video_id).limit(1)
    list = query.get()
    print('長さ')
    print(len(list))
    return list[0]

def is_music_notification_enabled(uid: str, category: str) -> bool:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    doc_ref = db.collection('users').document(uid)
    field_name = 'isMusicNotificationEnabled'
    if category == 'video':
        field_name = 'isVideoNotificationEnabled'
    is_notification_enabled = doc_ref.get().to_dict().get(field_name)
    return is_notification_enabled if is_notification_enabled != None else False

def fetch_ranged_users(start: datetime.datetime, end: datetime.datetime) -> list[dict]:
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    lastDoc = None
    db = firestore.client()
    users = []
    query = db.collection('users').where('createdAt', '>=', start).order_by('createdAt').limit(1)
    while 1:
        if lastDoc == None:
            docs = query.get()
            print('読み込み')
        else:
            docs = query.start_after(lastDoc).get()
            print('読み込み')
        if len(docs) == 0:
            break
        user = docs[0].to_dict()
        if user['createdAt'] >= end:
            break
        lastDoc = docs[0]
        if user['birthday'] != None:
            users.append(user)
    return users
    

def fetch_videos_by_youtube_video_ids(youtube_video_ids: list[str]):
    result = []
    for i in range(len(youtube_video_ids)):
        result.append(fetch_video_by_youtube_video_id(youtube_video_ids[i]))
    return result

def fetch_doc_by_collection_name_and_documentId(collection_name: str, document_id: str):
    if not firebase_admin._apps:
        cf.initialize_firebase(cf.get_flavor())
    db = firestore.client()
    doc_ref = db.collection(collection_name).document(document_id)
    return doc_ref.get()
