from firebase_admin import firestore
import firebase_admin
import ConvenientFunctions as cf
import datetime
import urllib.request
from typing import Optional
import json
import ToFireStore
import NewToStorage

videosDir = 'videos'
jsonFileName = 'caption.json'
lastVideoId = None

def getVideoDocById() -> Optional[firestore.DocumentSnapshot]:
    if not firebase_admin._apps:
        cf.initializeFirebase(cf.getFlavor())
    db = firestore.client()
    doc = db.collection('videos').document(lastVideoId).get()
    if doc.exists:
        return doc
    else:
        return None

def do():
    if not firebase_admin._apps:
        cf.initializeFirebase(cf.getFlavor())
    lastDoc = getVideoDocById()
    db = firestore.client()
    query = db.collection('videos').order_by('publishedAt').limit(1)
    count = 0
    while True:
        print(f'count: {count}')
        count = count + 1
        if lastDoc == None:
            docs = query.get()
        else:
            docs = query.start_after(lastDoc).get()
        if len(docs) == 0:
            break
        videoId = docs[0].reference.id
        print(f'処理中のvideoId: {videoId}')
        video = docs[0].to_dict()
        video['id'] = videoId
        lastDoc = docs[0]
        serCaptionJsonUrl(video)
    return

def serCaptionJsonUrl(video: dict):
    isUncompletedVideo = video.get('isUncompletedVideo')
    uncompletedJsonUrl = video.get('uncompletedJsonUrl')
    jsonUrl = video.get('jsonUrl')
    videoId = video.get('id')
    newCaptionDictList: Optional[list[dict]] = None
    if isUncompletedVideo == False:
        if jsonUrl == None:
            print(f'jsonUrlがありませんでした。videoId: {videoId}')
            return
        response = urllib.request.urlopen(jsonUrl)
        oldCaptionDictList: list[dict] = json.loads(response.read().decode())
        newCaptionDictList = toNewDictListFromCompleted(oldCaptionDictList)
    
    elif isUncompletedVideo == True:
        if uncompletedJsonUrl == None:
            return
        else:
            response = urllib.request.urlopen(uncompletedJsonUrl)
            oldCaptionDictList: list[dict] = json.loads(response.read().decode())
            newCaptionDictList = toNewDictListFromUncompleted(oldCaptionDictList)
            
    else:
        print(f'isUncompletedVideoがnullです。videoId: {videoId}')
        return
    if newCaptionDictList == None:
        print(f'newCaptionDictListがnullです。videoId: {videoId}')
        return
    
    url = NewToStorage.newJsonUrl(videoId, newCaptionDictList)
    ToFireStore.afterReview(
        {
            'captionJsonUrl': url,
        },
        videoId,
    )
        
    return

def toNewDictListFromCompleted(oldCaptionDictList: list[dict]) -> list[dict]:
    newCaptionDictList = []
    for oldCaptionDict in oldCaptionDictList:
        koList = []
        for detail in oldCaptionDict['detail']:
            koList.append(detail['actualLyric'])
        ko = ' '.join(koList)
        newCaptionDict = {
            'time': oldCaptionDict['time'],
            'from': ko,
            'to': oldCaptionDict['fullMeaning'],
        }
        newCaptionDictList.append(newCaptionDict)
    return newCaptionDictList

def toNewDictListFromUncompleted(oldCaptionDictList: list[dict]) -> list[dict]:
    newCaptionDictList = []
    for oldCaptionDict in oldCaptionDictList:
        ko = oldCaptionDict.get('ko')
        ja = oldCaptionDict.get('ja')
        time = oldCaptionDict.get('time')
        newCaptionDict = {
            'time': time,
        }
        if ko != None:
            newCaptionDict['from'] = ko
        if ja != None:
            newCaptionDict['to'] = ja
        newCaptionDictList.append(newCaptionDict)
    return newCaptionDictList



def main():
    do()

if __name__ == '__main__':
    main()