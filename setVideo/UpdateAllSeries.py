import ConvenientFunctions as cf
from firebase_admin import firestore
import GetYoutubeData
import datetime

def getCollectionDocsAsDictList(collectionName: str) -> list[dict]:
    db = firestore.client()
    collection_ref = db.collection(collectionName)
    docs = collection_ref.get()
    dictList = []
    for doc in docs:
        dictList.append(doc.to_dict())
    return dictList

def seriesLoop(SeriesDocsDictList: list[dict]):
    for seriesDict in SeriesDocsDictList:
        addNewVideoToSeries(seriesDict)

def addNewVideoToSeries(seriesDict: dict):
    playlistId = seriesDict['playlistId']
    if playlistId == None:
        return
    latestVideoDocDict = latestVideoDocDictInSeries(seriesDict)
    updatedYoutubeVideoIds = getUpdatedYoutubeVideoIds(seriesDict, latestVideoDocDict)
    
def latestVideoDocDictInSeries(seriesDict: dict) -> dict:
    db = firestore.client()
    seriesId = seriesDict['playlistId']
    videos_ref = db.collection('videos')
    videos_ref.where('playlistIds', 'array_contains', seriesId)
    videos_ref.order_by('publishedAt', direction=firestore.Query.DESCENDING)
    videos_ref.limit(1)
    latestVideoDoc = videos_ref.get()[0]
    return latestVideoDoc.to_dict()

def getUpdatedYoutubeVideoIds(youtubePlaylistId: str, latestVideoDocDict: dict) -> list[str]:
    youtubeVideoIds = []
    if isDescendantOfSeries(latestVideoDocDict, youtubePlaylistId): #アップロード日時の降順になっている
        youtubeVideoIds = fetchLatestVideoIdsWhenDesendant(latestVideoDocDict, youtubePlaylistId)
    else: #アップロード日時の昇順になっている
        youtubeVideoIds = fetchLatestVideoIdsWhenAsendant(latestVideoDocDict, youtubePlaylistId)

def fetchLatestVideoIdsWhenDesendant(latestVideoDocDict: dict, youtubePlaylistId: str) -> list[str]:
    videoIds = []
    nextPagetoken = None
    for i in range(50): #while1だと無限ループになる可能性があるので
        playlistItemsResponse = GetYoutubeData.getVideosInPlaylist(
            youtubePlaylistId = youtubePlaylistId,
            maxResults= 1,
            pageToken = nextPagetoken
        )
        videoId = playlistItemsResponse["items"][0]["snippet"]["resourceId"]["videoId"]
        if videoId == latestVideoDocDict['videoId']:
            return videoIds
        videoIds.append(videoId)
        nextPagetoken = playlistItemsResponse.get("nextPageToken")
def fetchLatestVideoIdsWhenAsendant(latestVideoDocDict: dict, youtubePlaylistId: str) -> list[str]:
    print('構築中')

def isDescendantOfSeries(videoDocDict: dict, youtubePlaylistId: str) -> bool: #Youtubeプレイリストがアップロード日時の降順になっているか
    response = GetYoutubeData.getVideosInPlaylist(
    youtubePlaylistId = youtubePlaylistId,
    maxResults= 1
    )
    publishedAt = datetime.datetime.fromisoformat(response["items"][0]["snippet"]['publishedAt'].replace('Z', '+00:00'))
    return videoDocDict['publishedAt'] >= publishedAt

def main():
    flavor = cf.getFlavor()
    cf.initializeFirebase(flavor)
    SeriesDocsDictList = getCollectionDocsAsDictList('series')
    seriesLoop(SeriesDocsDictList)

if __name__ == '__main__':
    main()