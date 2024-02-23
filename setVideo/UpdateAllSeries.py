import ConvenientFunctions as cf
from firebase_admin import firestore
import GetYoutubeData
import datetime
import SetVideo

def getCollectionDocsAsDictList(collectionName: str) -> list[dict]:
    db = firestore.client()
    collection_ref = db.collection(collectionName).where('isUpdatable', '==', True)
    docs = collection_ref.get()
    dictList = []
    for doc in docs:
        dictList.append(doc.to_dict())
    return dictList

def updatedPlaylistIdsAndTheVideoId(SeriesDocsDictList: list[dict]) -> dict:
    result = {}
    for seriesDict in SeriesDocsDictList:
        print(f'{SeriesDocsDictList.index(seriesDict)}/{len(SeriesDocsDictList)}')
        if not ('playlistId' in seriesDict) or seriesDict['playlistId'] == None:
            print('No playlistId')
            continue
        result[seriesDict["playlistId"]] = addNewVideoToSeries(seriesDict)
    return result

def addNewVideoToSeries(seriesDict: dict) -> list[str]:
    playlistId = seriesDict['playlistId']
    if playlistId == None:
        return
    latestVideoDocDict = latestVideoDocDictInSeries(seriesDict)
    updatedYoutubeVideoIds = getUpdatedYoutubeVideoIds(playlistId, latestVideoDocDict)
    return updatedYoutubeVideoIds
    
def latestVideoDocDictInSeries(seriesDict: dict) -> dict:
    db = firestore.client()
    seriesId = seriesDict['playlistId']
    videos_ref = db.collection('videos')
    query = videos_ref.where('playlistIds', 'array_contains', seriesId).order_by('publishedAt', direction=firestore.Query.DESCENDING).limit(1)
    latestVideoDoc = query.get()[0]
    return latestVideoDoc.to_dict()

def getUpdatedYoutubeVideoIds(youtubePlaylistId: str, latestVideoDocDict: dict) -> list[str]:
    youtubeVideoIds = []
    if isDescendantOfSeries(latestVideoDocDict, youtubePlaylistId): #アップロード日時の降順になっている
        youtubeVideoIds = fetchLatestVideoIdsWhenDesendant(latestVideoDocDict, youtubePlaylistId)
    else: #アップロード日時の昇順になっている
        print('このプレイリストは昇順になっています: ' + youtubePlaylistId)
        youtubeVideoIds = fetchLatestVideoIdsWhenAsendant(latestVideoDocDict, youtubePlaylistId)
    return youtubeVideoIds

def fetchLatestVideoIdsWhenDesendant(latestVideoDocDict: dict, youtubePlaylistId: str) -> list[str]:
    videoIds = []
    nextPagetoken = None
    for i in range(50): #while1だと無限ループになる可能性があるので
        playlistItemsResponse = GetYoutubeData.getVideosInPlaylist(
            youtubePlaylistId = youtubePlaylistId,
            maxResults= 1,
            nextPageToken = nextPagetoken
        )
        videoId = playlistItemsResponse["items"][0]["snippet"]["resourceId"]["videoId"]
        if videoId == latestVideoDocDict['videoId']:
            return videoIds
        videoIds.append(videoId)
        nextPagetoken = playlistItemsResponse.get("nextPageToken")

def fetchLatestVideoIdsWhenAsendant(latestVideoDocDict: dict, youtubePlaylistId: str) -> list[str]:
    playlistItemsResponse = GetYoutubeData.getItemResponseFromPlaylist(youtubePlaylistId)
    videoIds = []
    for playlistItem in playlistItemsResponse:
        publishedAt = publishedAtFromItemResponse(playlistItem)
        if publishedAt > latestVideoDocDict['publishedAt']:
            videoIds.append(playlistItem["snippet"]["resourceId"]["videoId"])
    return videoIds

def isDescendantOfSeries(latestVideoDocDict: dict, youtubePlaylistId: str) -> bool: #Youtubeプレイリストがアップロード日時の降順になっているか
    response = GetYoutubeData.getVideosInPlaylist(
    youtubePlaylistId = youtubePlaylistId,
    maxResults = 1
    )
    publishedAt = publishedAtFromItemResponse(response["items"][0])
    return latestVideoDocDict['publishedAt'] <= publishedAt

def publishedAtFromItemResponse(videoResponse) -> datetime.datetime:
    youtubeVideoId = videoResponse["snippet"]["resourceId"]["videoId"]
    response = GetYoutubeData.getVideo(youtubeVideoId) #動画一本釣りとplaylist経由での動画だとpublishedAtがズレるため
    return datetime.datetime.fromisoformat(response['snippet']['publishedAt'].replace('Z', '+00:00'))

def mergeAndRemoveDuplicates(dictData: dict) -> list[str]:
    mergedList = []
    for key, value in dictData.items():
        mergedList.extend(value)

    # 重複した要素を削除
    uniqueList = list(set(mergedList))
    return uniqueList

def main():
    flavor = cf.get_flavor()
    cf.initialize_firebase(flavor)
    SeriesDocsDictList = getCollectionDocsAsDictList('series')
    updatedVideosDict = updatedPlaylistIdsAndTheVideoId(SeriesDocsDictList) #キーはplaylistId、値はvideoIdの配列
    print('------------------')
    for key, value in updatedVideosDict.items():
        print(f"playlistId:\n{key}\n\nValue:\n{','.join(value)}")
        print('------------------')
    allVideoIds = mergeAndRemoveDuplicates(updatedVideosDict)
    print('全ての動画のvideoId:')
    print(','.join(allVideoIds)) #追加するべき動画のvideoIdを出力
    if not cf.answered_yes('実際にこれらの動画を追加しますか？'):
        return
    SetVideo.setVideos(flavor = flavor, youtubeVideoIds = allVideoIds)
    
if __name__ == '__main__':
    main()