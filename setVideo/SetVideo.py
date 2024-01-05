import ConvenientFunctions as cf
import youtube_transcript_api
import CaptionsToJson
import MakeFirestoreMap
import ToStorage
import ToFireStore
import pprint
from typing import Optional, Tuple
import Notification

# ビデオIDを入力する
def inputVideoIds() -> list[str]:
    videoIds = cf.inputText('videoIdを入力(複数ある場合は","で区切ってください)')
    videoIds = videoIds.split(",")
    resultVideoIds = []
    for videoId in videoIds:
        if not videoId in resultVideoIds:
            resultVideoIds.append(videoId)
    return resultVideoIds

def videoIdsLoop(videoIds: list[str], flavor: str, policy: dict, isNonStop: bool) -> list[str]: # 返り値は、スキップされた動画のvideoIdのリスト
    skippedVideoIds = []
    cf.initializeFirebase(flavor)
    for videoId in videoIds:
        isNotSkipped = setEachVideo(videoId, flavor, policy, isNonStop)
        if not isNotSkipped:
            skippedVideoIds.append(videoId)
        if not isNonStop and not cf.answeredYes('次の動画に進みますか？'):
            return skippedVideoIds
    return skippedVideoIds

def checkCaptionAvailability(videoId: str) -> list[str]:
    try:
        captionList = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(videoId)
    except youtube_transcript_api._errors.TranscriptsDisabled:
        captionList = []
    availableLanguages = []
    for caption in captionList:
        if caption.language_code == 'ko' and not caption.is_generated:
            availableLanguages.append('ko')
        if caption.language_code == 'ja' and not caption.is_generated:
            availableLanguages.append('ja')
    return availableLanguages

def setEachVideo(videoId: str, flavor: str, policy: dict, isNonStop: bool) -> bool: #返り値は、この動画が追加されたかどうか(true: 正常に追加された, false: 追加されなかった)
    availableLanguages = checkCaptionAvailability(videoId)
    if availableLanguages == []: # 日本語・韓国語字幕がない場合
        print(f"{videoId}: この動画には日本語・韓国語字幕どちらもありません")
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, True, availableLanguages)
        if (not isNonStop and cf.answeredYes('この動画をスキップしますか？')) or firestoreMap == None: return False
        url = None
    
    if availableLanguages == ['ko']: # 日本語字幕がない場合
        print(f"{videoId}: この動画には韓国語字幕があります")
        koreanCaptions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId, 
            languages=['ko'],
            )
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, True, availableLanguages)
        if (not isNonStop and cf.answeredYes('この動画をスキップしますか？')) or firestoreMap == None: return False
        uncompletedJsonData = convertCaptionsToUncompletedJson(koreanCaptions, None)
        # jsonData = CaptionsToJson.captionsToJson(koreanCaptions, None)
        url = ToStorage.toStorage(f'ko_ja_{videoId}', flavor, uncompletedJsonData, availableLanguages)
    
    if availableLanguages == ['ja']: # 韓国語字幕がない場合
        print(f"{videoId}: この動画には日本語字幕があります")
        japaneseCaptions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId, 
            languages=['ja'],
            )
        uncompletedJsonData = convertCaptionsToUncompletedJson(None, japaneseCaptions)
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, True, availableLanguages)
        if (not isNonStop and cf.answeredYes('この動画をスキップしますか？')) or firestoreMap == None: return False
        url = ToStorage.toStorage(f'ko_ja_{videoId}', flavor, uncompletedJsonData, availableLanguages)
    
    if 'ja' in availableLanguages and 'ko' in availableLanguages: # 日本語・韓国語字幕がある場合
        print(f"{videoId}: この動画には日本語・韓国語字幕があります")
        koreanCaptions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId, 
            languages=['ko'],
            )
        japaneseCaptions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId,
            languages=['ja'],
            )

        koreanCaptions, japaneseCaptions = makeValidCaptions(koreanCaptions, japaneseCaptions)

        if not cf.answeredYes(f'{videoId}:字幕の行数は{len(koreanCaptions)}行です。続けますか？'):
            return False
        jsonData = CaptionsToJson.captionsToJson(koreanCaptions, japaneseCaptions)
        if len(jsonData) != len(koreanCaptions):
            print(f'{videoId}: スクレイプした字幕の行数とjsonの行数が一致しないため、スキップします。')
            return False
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, False, availableLanguages)
        if (not isNonStop and cf.answeredYes('この動画をスキップしますか？')) or firestoreMap == None: return False
        url = ToStorage.toStorage(f'ko_ja_{videoId}', flavor, jsonData, availableLanguages)
    
    document = ToFireStore.toFirestore(firestoreMap, url, flavor, f'ko_ja_{videoId}', availableLanguages)
    pprint.pprint(document) #Firestoreにアップロードした内容

    return True

def makeValidCaptions(koreanCaptions: list[dict], japaneseCaptions: list[dict]) -> list[dict]:
    for i in range(len(koreanCaptions)):
            koreanCaptions[i]['end'] = koreanCaptions[i]['start'] + koreanCaptions[i]['duration']
            koreanCaptions[i].pop('duration')
    for i in range(len(japaneseCaptions)):
        japaneseCaptions[i]['end'] = japaneseCaptions[i]['start'] + japaneseCaptions[i]['duration']
        japaneseCaptions[i].pop('duration')
        
    koreanCaptions, japaneseCaptions = filter_captions(koreanCaptions, japaneseCaptions)
    koreanCaptions, japaneseCaptions = deleteOverlappedCaptions(koreanCaptions, japaneseCaptions)
        
    for i in range(len(koreanCaptions)):
        koreanCaptions[i]['duration'] = koreanCaptions[i]['end'] - koreanCaptions[i]['start']
        koreanCaptions[i].pop('end')
    for i in range(len(japaneseCaptions)):
        japaneseCaptions[i]['duration'] = japaneseCaptions[i]['end'] - japaneseCaptions[i]['start']
        japaneseCaptions[i].pop('end')
        
    return koreanCaptions, japaneseCaptions


def filter_captions(mainCaptions, subCaptions): # mainCaptionsとsubCaptionsどちらかしかない時間帯の字幕を削除する。ここで、すべての字幕のstartとendは同じになる。
    filtered_main_captions = []
    filtered_sub_captions = []

    for main_caption in mainCaptions:
        for sub_caption in subCaptions:
            start_time = max(main_caption['start'], sub_caption['start'])
            end_time = min(main_caption['end'], sub_caption['end'])
            
            if start_time < end_time:
                filtered_main_captions.append({
                    'text': main_caption['text'],
                    'start': start_time,
                    'end': end_time
                })

                filtered_sub_captions.append({
                    'text': sub_caption['text'],
                    'start': start_time,
                    'end': end_time
                })

    return filtered_main_captions, filtered_sub_captions

def deleteOverlappedCaptions(mainCaptions: list[dict], subCaptions: list[dict]) -> list[dict]:
    while True:
        for i in range(len(mainCaptions)):
            foundError = False
            if i == len(mainCaptions) - 1:
                break
            if mainCaptions[i]['text'] == mainCaptions[i + 1]['text'] or subCaptions[i]['text'] == subCaptions[i + 1]['text']:
                foundError = True
                if mainCaptions[i]['text'] == mainCaptions[i + 1]['text']:
                    chainCount = captionConnectedCount(mainCaptions, subCaptions, i)
                    mainCaptionsTextList = []
                    for j in range(chainCount):
                        mainCaptionsTextList.append(mainCaptions[i + j]['text'])
                    mainCaptionsTextList = list(dict.fromkeys(mainCaptionsTextList))
                    mainCaptionText = ' '.join(mainCaptionsTextList)
                    
                    subCaptionsTextList = []
                    for j in range(chainCount):
                        subCaptionsTextList.append(subCaptions[i + j]['text'])
                    subCaptionsTextList = list(dict.fromkeys(subCaptionsTextList))
                    subCaptionText = ' '.join(subCaptionsTextList)
                    
                    endTime = mainCaptions[i + chainCount - 1]['end']
                    mainCaptions[i]['text'] = mainCaptionText
                    subCaptions[i]['text'] = subCaptionText
                    mainCaptions[i]['end'] = endTime
                    subCaptions[i]['end'] = endTime
                    del mainCaptions[i + 1:i + chainCount]
                    del subCaptions[i + 1:i + chainCount]
                    break
                
                if subCaptions[i]['text'] == subCaptions[i + 1]['text']:
                    chainCount = captionConnectedCount(subCaptions, mainCaptions, i)
                    subCaptionsTextList = []
                    for j in range(chainCount):
                        subCaptionsTextList.append(subCaptions[i + j]['text'])
                    subCaptionsTextList = list(dict.fromkeys(subCaptionsTextList))
                    subCaptionText = ' '.join(subCaptionsTextList)
                    
                    mainCaptionsTextList = []
                    for j in range(chainCount):
                        mainCaptionsTextList.append(mainCaptions[i + j]['text'])
                    mainCaptionsTextList = list(dict.fromkeys(mainCaptionsTextList))
                    
                    mainCaptionText = ' '.join(mainCaptionsTextList)
                    
                    endTime = subCaptions[i + chainCount - 1]['end']
                    subCaptions[i]['text'] = subCaptionText
                    mainCaptions[i]['text'] = mainCaptionText
                    subCaptions[i]['end'] = endTime
                    mainCaptions[i]['end'] = endTime
                    del subCaptions[i + 1:i + chainCount]
                    del mainCaptions[i + 1:i + chainCount]
                    break
                    
        if not foundError:
            break
    return mainCaptions, subCaptions

def captionConnectedCount(mainCaptions: list[dict], subCaptions: list[dict], i: int):
    reachToFinish = False
    overlapCount = 1
    while True:
        count = 0
        while True:
            if mainCaptions[i + overlapCount - 1 + count]['text'] == mainCaptions[i + overlapCount+ count]['text']:
                overlapCount = overlapCount + 1
                count = count + 1
                reachToFinish = False
            else:
                if count == 0:
                    if reachToFinish:
                        return overlapCount
                    reachToFinish = True
                break
        count = 0
        while True:
            if subCaptions[i + overlapCount - 1 + count]['text'] == subCaptions[i + overlapCount + count]['text']:
                overlapCount = overlapCount + 1
                count = count + 1
                reachToFinish = False
            else:
                if count == 0:
                    if reachToFinish:
                        return overlapCount
                    reachToFinish = True
                break

def convertCaptionsToUncompletedJson(koreanCaptions: Optional[list], japaneseCaptions: Optional[list],) -> dict:
    jsonData = []
    notOptionalCaptions = koreanCaptions if koreanCaptions != None else japaneseCaptions
    for i in range(len(notOptionalCaptions)):
        start = notOptionalCaptions[i]['start']
        end = start + notOptionalCaptions[i]['duration']
        thisLineMap = {}
        thisLineMap["time"] = f'{cf.formatTime(start)} --> {cf.formatTime(end)}'
        if koreanCaptions != None:
            thisLineMap["ko"] = koreanCaptions[i]['text'].replace('\n', ' ')
        if japaneseCaptions != None:
            thisLineMap["ja"] = japaneseCaptions[i]['text'].replace('\n', ' ')
        jsonData.append(thisLineMap)
    return jsonData

def setPolicy() -> dict:
    processPolicy = {
        'setCelebrityIdsEachTime': cf.answeredYes('毎回celebrityIdsを入力しますか？'),
        'setIfTitleIsSameAsYoutubeTitleEachTime': cf.answeredYes('タイトルはYoutubeのタイトルと同じか毎回決めますか？'),
        'setCategoryEachTime': cf.answeredYes('毎回カテゴリーを入力しますか？'),
        'setPlaylistIdsEachTime': cf.answeredYes('毎回playlistIdsを入力しますか？'),
    }
    if(not processPolicy['setCelebrityIdsEachTime']):
        processPolicy['celebrityIds'] = cf.inputText('celebrityIdsを入力してください。(複数の場合、","で区切ってください)').split(",")
    if(not processPolicy['setIfTitleIsSameAsYoutubeTitleEachTime']):
        processPolicy['IsTitleSameAsYoutubeTitle'] = cf.answeredYes('タイトルはYoutubeのタイトルと同じですか？')
    if(not processPolicy['setCategoryEachTime']):
        processPolicy['category'] = 'video' if cf.answeredYes('カテゴリーはどっち？(y = video, n = music)') else 'music'
    if(not processPolicy['setPlaylistIdsEachTime']):
        processPolicy['playlistIds'] = cf.inputText('playlistIdsを入力してください。(複数の場合、","で区切ってください)').split(",")
    return processPolicy

# def classifyYoutubeVideoDocs(youtubeVideoIds: list[str]) -> Tuple:
#     musicVideoDocs: list = []
#     videoVideoDocs: list = []
#     for youtubeVideoId in youtubeVideoIds:
#         videoDoc = ToFireStore.fetchVideoByYoutubeVideoId(youtubeVideoId)
#         videoDocDict = videoDoc.to_dict()
#         if videoDocDict == None or not 'category' in videoDocDict or videoDocDict['category'] == None:
#             continue
#         category = videoDocDict['category']
#         if category == 'music':
#             musicVideoDocs.append(videoDoc)
#         elif category == 'video':
#             videoVideoDocs.append(videoDoc)
    
#     return musicVideoDocs, videoVideoDocs

# def videoVideoDocsToSeriesIds(videoVideoDocs: list) -> list:
#     seriesIds = []
#     for videoVideoDoc in videoVideoDocs:
#         videoVideoDocDict = videoVideoDoc.to_dict()
#         if videoVideoDocDict == None or not 'playlistIds' in videoVideoDocDict or videoVideoDocDict['playlistIds'] == None:
#             continue
#         seriesIds.extend(videoVideoDocDict['playlistIds'])
#     return list(set(seriesIds))

def setVideos(flavor: str, youtubeVideoIds: list[str] = None, isNonStop: bool = False):
    policy = setPolicy()
    youtubeVideoIds = youtubeVideoIds if youtubeVideoIds != None else inputVideoIds()
    skippedYoutubeVideoIds = videoIdsLoop(youtubeVideoIds, flavor, policy, isNonStop)
    addedYoutubeVideoIds = [x for x in youtubeVideoIds if x not in skippedYoutubeVideoIds]
    print(f'スキップした動画の数: {len(skippedYoutubeVideoIds)}')
    print(f'スキップした動画のYoutubeVideoID: {skippedYoutubeVideoIds}')
    print('\n')
    print(f'追加した動画の数: {len(addedYoutubeVideoIds)}')
    print(f'追加した動画のYoutubeVideoID: {addedYoutubeVideoIds}')
    if not cf.answeredYes('通知処理に進みますか？'):
        return
    completedVideos = ToFireStore.completedVideos(addedYoutubeVideoIds)
    completedVideoDocs = ToFireStore.fetchVideosByYouttubeVideoIds(completedVideos)
    Notification.sendCelebrityLikersByVideoDocs(completedVideoDocs)
    
    # musicVideoDocs, videoVideoDocs = classifyYoutubeVideoDocs(completedVideos)
    # Notification.sendCelebrityLikersByMusicVideoDocs(musicVideoDocs)
    # updatedSeriesIds = videoVideoDocsToSeriesIds(videoVideoDocs)
    # for seriesId in updatedSeriesIds:
    #     Notification.sendToSeriesLiker(seriesId)

def main():
    flavor = cf.getFlavor()
    setVideos(flavor, isNonStop = cf.answeredYes('動画ごとの確認をスキップしますか？'))

if __name__ == '__main__':
    main()