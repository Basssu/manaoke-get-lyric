import convenient_functions as cf
from firebase_admin import firestore
import get_youtube_data as get_youtube_data
import datetime
import set_video as set_video

def get_collection_docs_as_dict_list(collection_name: str) -> list[dict]:
    db = firestore.client()
    collection_ref = db.collection(collection_name).where('isUpdatable', '==', True)
    docs = collection_ref.get()
    dict_list = []
    for doc in docs:
        dict_list.append(doc.to_dict())
    return dict_list

def updated_playlist_ids_and_the_video_id(series_docs_dict_list: list[dict]) -> dict:
    result = {}
    for series_dict in series_docs_dict_list:
        print(f'{series_docs_dict_list.index(series_dict)}/{len(series_docs_dict_list)}')
        if not ('playlistId' in series_dict) or series_dict['playlistId'] == None:
            print('No playlistId')
            continue
        result[series_dict["playlistId"]] = add_new_video_to_series(series_dict)
    return result

def add_new_video_to_series(series_dict: dict) -> list[str]:
    playlist_id = series_dict['playlistId']
    if playlist_id == None:
        return
    latest_video_doc_dict = latest_video_doc_dict_in_series(series_dict)
    updated_youtube_video_ids = get_updated_youtube_video_ids(playlist_id, latest_video_doc_dict)
    return updated_youtube_video_ids
    
def latest_video_doc_dict_in_series(series_dict: dict) -> dict:
    db = firestore.client()
    series_id = series_dict['playlistId']
    videos_ref = db.collection('videos')
    query = videos_ref.where('playlistIds', 'array_contains', series_id).order_by('publishedAt', direction=firestore.Query.DESCENDING).limit(1)
    latest_video_doc = query.get()[0]
    return latest_video_doc.to_dict()

def get_updated_youtube_video_ids(youtube_playlist_id: str, latest_video_doc_dict: dict) -> list[str]:
    youtube_video_ids = []
    if is_descendant_of_series(latest_video_doc_dict, youtube_playlist_id): #アップロード日時の降順になっている
        youtube_video_ids = fetch_latest_video_ids_when_desendant(latest_video_doc_dict, youtube_playlist_id)
    else: #アップロード日時の昇順になっている
        print('このプレイリストは昇順になっています: ' + youtube_playlist_id)
        youtube_video_ids = fetch_latest_video_ids_when_asendant(latest_video_doc_dict, youtube_playlist_id)
    return youtube_video_ids

def fetch_latest_video_ids_when_desendant(latest_video_doc_dict: dict, youtube_playlist_id: str) -> list[str]:
    video_ids = []
    next_pagetoken = None
    for i in range(50): #while1だと無限ループになる可能性があるので
        playlist_items_response = get_youtube_data.get_videos_in_playlist(
            youtube_playlist_id = youtube_playlist_id,
            max_results= 1,
            next_page_token = next_pagetoken
        )
        video_id = playlist_items_response["items"][0]["snippet"]["resourceId"]["videoId"]
        if video_id == latest_video_doc_dict['videoId']:
            return video_ids
        video_ids.append(video_id)
        next_pagetoken = playlist_items_response.get("nextPageToken")

def fetch_latest_video_ids_when_asendant(latest_video_doc_dict: dict, youtube_playlist_id: str) -> list[str]:
    playlist_items_response = get_youtube_data.get_item_response_from_playlist(youtube_playlist_id)
    video_ids = []
    for playlist_item in playlist_items_response:
        published_at = published_at_from_item_response(playlist_item)
        if published_at > latest_video_doc_dict['publishedAt']:
            video_ids.append(playlist_item["snippet"]["resourceId"]["videoId"])
    return video_ids

def is_descendant_of_series(latest_video_doc_dict: dict, youtube_playlist_id: str) -> bool: #Youtubeプレイリストがアップロード日時の降順になっているか
    response = get_youtube_data.get_videos_in_playlist(
    youtube_playlist_id = youtube_playlist_id,
    max_results = 1
    )
    published_at = published_at_from_item_response(response["items"][0])
    return latest_video_doc_dict['publishedAt'] <= published_at

def published_at_from_item_response(video_response) -> datetime.datetime:
    youtube_video_id = video_response["snippet"]["resourceId"]["videoId"]
    response = get_youtube_data.get_video(youtube_video_id) #動画一本釣りとplaylist経由での動画だとpublishedAtがズレるため
    return datetime.datetime.fromisoformat(response['snippet']['publishedAt'].replace('Z', '+00:00'))

def merge_and_remove_duplicates(dict_data: dict) -> list[str]:
    merged_list = []
    for key, value in dict_data.items():
        merged_list.extend(value)

    # 重複した要素を削除
    unique_list = list(set(merged_list))
    return unique_list

def main():
    flavor = cf.get_flavor()
    cf.initialize_firebase(flavor)
    series_docs_dict_list = get_collection_docs_as_dict_list('series')
    updated_videos_dict = updated_playlist_ids_and_the_video_id(series_docs_dict_list) #キーはplaylistId、値はvideoIdの配列
    print('------------------')
    for key, value in updated_videos_dict.items():
        print(f"playlistId:\n{key}\n\nValue:\n{','.join(value)}")
        print('------------------')
    all_video_ids = merge_and_remove_duplicates(updated_videos_dict)
    print('全ての動画のvideoId:')
    print(','.join(all_video_ids)) #追加するべき動画のvideoIdを出力
    if not cf.answered_yes('実際にこれらの動画を追加しますか？'):
        return
    set_video.set_videos(flavor = flavor, youtube_video_ids = all_video_ids)
    
if __name__ == '__main__':
    main()