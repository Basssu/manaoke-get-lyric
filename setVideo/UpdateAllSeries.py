import ConvenientFunctions as cf
from firebase_admin import firestore
import GetYoutubeData
import datetime
import SetVideo

def get_collection_docs_as_dict_list(collectionName: str) -> list[dict]:
    db = firestore.client()
    collection_ref = db.collection(collectionName).where('isUpdatable', '==', True)
    docs = collection_ref.get()
    dictList = []
    for doc in docs:
        dictList.append(doc.to_dict())
    return dictList

def updated_playlist_ids_and_the_video_id(SeriesDocsDictList: list[dict]) -> dict:
    result = {}
    for seriesDict in SeriesDocsDictList:
        print(f'{SeriesDocsDictList.index(seriesDict)}/{len(SeriesDocsDictList)}')
        if not ('playlistId' in seriesDict) or seriesDict['playlistId'] == None:
            print('No playlistId')
            continue
        result[seriesDict["playlistId"]] = add_new_video_to_series(seriesDict)
    return result

def add_new_video_to_series(seriesDict: dict) -> list[str]:
    playlistId = seriesDict['playlistId']
    if playlistId == None:
        return
    latestVideoDocDict = latest_video_doc_dict_in_series(seriesDict)
    updatedYoutubeVideoIds = get_updated_youtube_video_ids(playlistId, latestVideoDocDict)
    return updatedYoutubeVideoIds
    
def latest_video_doc_dict_in_series(seriesDict: dict) -> dict:
    db = firestore.client()
    seriesId = seriesDict['playlistId']
    videos_ref = db.collection('videos')
    query = videos_ref.where('playlistIds', 'array_contains', seriesId).order_by('publishedAt', direction=firestore.Query.DESCENDING).limit(1)
    latestVideoDoc = query.get()[0]
    return latestVideoDoc.to_dict()

def get_updated_youtube_video_ids(youtubePlaylistId: str, latestVideoDocDict: dict) -> list[str]:
    youtubeVideoIds = []
    if is_descendant_of_series(latestVideoDocDict, youtubePlaylistId): #アップロード日時の降順になっている
        youtubeVideoIds = fetch_latest_video_ids_when_desendant(latestVideoDocDict, youtubePlaylistId)
    else: #アップロード日時の昇順になっている
        print('このプレイリストは昇順になっています: ' + youtubePlaylistId)
        youtubeVideoIds = fetch_latest_video_ids_when_asendant(latestVideoDocDict, youtubePlaylistId)
    return youtubeVideoIds

def fetch_latest_video_ids_when_desendant(latestVideoDocDict: dict, youtubePlaylistId: str) -> list[str]:
    videoIds = []
    nextPagetoken = None
    for i in range(50): #while1だと無限ループになる可能性があるので
        playlistItemsResponse = GetYoutubeData.get_videos_in_playlist(
            youtubePlaylistId = youtubePlaylistId,
            maxResults= 1,
            nextPageToken = nextPagetoken
        )
        videoId = playlistItemsResponse["items"][0]["snippet"]["resourceId"]["videoId"]
        if videoId == latestVideoDocDict['videoId']:
            return videoIds
        videoIds.append(videoId)
        nextPagetoken = playlistItemsResponse.get("nextPageToken")

def fetch_latest_video_ids_when_asendant(latestVideoDocDict: dict, youtubePlaylistId: str) -> list[str]:
    playlistItemsResponse = GetYoutubeData.get_item_response_from_playlist(youtubePlaylistId)
    videoIds = []
    for playlistItem in playlistItemsResponse:
        publishedAt = published_at_from_item_response(playlistItem)
        if publishedAt > latestVideoDocDict['publishedAt']:
            videoIds.append(playlistItem["snippet"]["resourceId"]["videoId"])
    return videoIds

def is_descendant_of_series(latestVideoDocDict: dict, youtubePlaylistId: str) -> bool: #Youtubeプレイリストがアップロード日時の降順になっているか
    response = GetYoutubeData.get_videos_in_playlist(
    youtubePlaylistId = youtubePlaylistId,
    maxResults = 1
    )
    publishedAt = published_at_from_item_response(response["items"][0])
    return latestVideoDocDict['publishedAt'] <= publishedAt

def published_at_from_item_response(videoResponse) -> datetime.datetime:
    youtubeVideoId = videoResponse["snippet"]["resourceId"]["videoId"]
    response = GetYoutubeData.get_video(youtubeVideoId) #動画一本釣りとplaylist経由での動画だとpublishedAtがズレるため
    return datetime.datetime.fromisoformat(response['snippet']['publishedAt'].replace('Z', '+00:00'))

def merge_and_remove_duplicates(dictData: dict) -> list[str]:
    mergedList = []
    for key, value in dictData.items():
        mergedList.extend(value)

    # 重複した要素を削除
    uniqueList = list(set(mergedList))
    return uniqueList

def main():
    flavor = cf.get_flavor()
    cf.initialize_firebase(flavor)
    SeriesDocsDictList = get_collection_docs_as_dict_list('series')
    updatedVideosDict = updated_playlist_ids_and_the_video_id(SeriesDocsDictList) #キーはplaylistId、値はvideoIdの配列
    print('------------------')
    for key, value in updatedVideosDict.items():
        print(f"playlistId:\n{key}\n\nValue:\n{','.join(value)}")
        print('------------------')
    allVideoIds = merge_and_remove_duplicates(updatedVideosDict)
    print('全ての動画のvideoId:')
    print(','.join(allVideoIds)) #追加するべき動画のvideoIdを出力
    if not cf.answered_yes('実際にこれらの動画を追加しますか？'):
        return
    SetVideo.set_videos(flavor = flavor, youtubeVideoIds = allVideoIds)
    
if __name__ == '__main__':
    main()