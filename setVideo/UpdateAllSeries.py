import ConvenientFunctions as cf
from firebase_admin import firestore

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
    print('構築中')

def main():
    flavor = cf.getFlavor()
    cf.initializeFirebase(flavor)
    SeriesDocsDictList = getCollectionDocsAsDictList('series')
    seriesLoop(SeriesDocsDictList)

if __name__ == '__main__':
    main()