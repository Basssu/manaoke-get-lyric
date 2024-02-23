import ConvenientFunctions as cf
import youtube_transcript_api
import CaptionsToJson
import MakeFirestoreMap
import ToStorage
import ToFireStore
import pprint
from typing import Optional, Tuple
import Notification
import NewToStorage

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
    captionJsonUrl = None
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
        captionJsonUrl = getCaptionJsonUrl(f'ko_ja_{videoId}', koreanCaptions, None)
    
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
        captionJsonUrl = getCaptionJsonUrl(f'ko_ja_{videoId}', None, japaneseCaptions)
    
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

        koreanCaptions = deleteIfOneCaptionNotExist(koreanCaptions, japaneseCaptions)
        japaneseCaptions = deleteIfOneCaptionNotExist(japaneseCaptions, koreanCaptions)

        if not cf.answeredYes(f'{videoId}:字幕の行数は{len(koreanCaptions)}行です。続けますか？'):
            return False
        jsonData = CaptionsToJson.captionsToJson(koreanCaptions, japaneseCaptions)
        if len(jsonData) != len(koreanCaptions):
            print(f'{videoId}: スクレイプした字幕の行数とjsonの行数が一致しないため、スキップします。')
            return False
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, False, availableLanguages)
        if (not isNonStop and cf.answeredYes('この動画をスキップしますか？')) or firestoreMap == None: return False
        url = ToStorage.toStorage(f'ko_ja_{videoId}', flavor, jsonData, availableLanguages)
        captionJsonUrl = getCaptionJsonUrl(f'ko_ja_{videoId}', koreanCaptions, japaneseCaptions)
        
    document = ToFireStore.toFirestore(firestoreMap, url, flavor, f'ko_ja_{videoId}', availableLanguages, captionJsonUrl)
    pprint.pprint(document) #Firestoreにアップロードした内容

    return True

def deleteIfOneCaptionNotExist(mainCaptions: list[dict], subCaptions: list[dict]) -> list[dict]:
    captions = []
    for mainCaption in mainCaptions:
        for subCaption in subCaptions:
            if mainCaption['start'] == subCaption['start'] and mainCaption['duration'] == subCaption['duration']:
                captions.append(mainCaption)
                break
    return captions

def getCaptionJsonUrl(videoId: str, mainCaptions: Optional[list[dict]], subCaptions: Optional[list[dict]]) -> str:
    data = makeCaptionDictList(mainCaptions, subCaptions)
    url = NewToStorage.newJsonUrl(videoId, data)
    return url

def makeCaptionDictList(mainCaptions: Optional[list[dict]], subCaptions: Optional[list[dict]]) -> list[dict]:
    captionDictList = []
    captionsLength = 0
    if mainCaptions != None:
        captionsLength = len(mainCaptions)
    else:
        captionsLength = len(subCaptions)
    for i in range(captionsLength):
        captionDict = {}
        if mainCaptions != None:
            captionDict['time'] = CaptionsToJson.convertTimeToSrtFormat(mainCaptions[i]['start'], mainCaptions[i]['duration'])
        else:
            captionDict['time'] = CaptionsToJson.convertTimeToSrtFormat(subCaptions[i]['start'], subCaptions[i]['duration'])
        if mainCaptions != None:
            captionDict['from'] = mainCaptions[i]['text'].replace('\n', ' ')
        if subCaptions != None:
            captionDict['to'] = subCaptions[i]['text'].replace('\n', ' ')
        captionDictList.append(captionDict)
    return captionDictList

def makeValidCaptions(koreanCaptions: list[dict], japaneseCaptions: list[dict]) -> list[dict]:
    for i in range(len(koreanCaptions)):
            koreanCaptions[i]['end'] = koreanCaptions[i]['start'] + koreanCaptions[i]['duration']
            koreanCaptions[i].pop('duration')
    for i in range(len(japaneseCaptions)):
        japaneseCaptions[i]['end'] = japaneseCaptions[i]['start'] + japaneseCaptions[i]['duration']
        japaneseCaptions[i].pop('duration')
        
    koreanCaptions, japaneseCaptions = filter_captions(koreanCaptions, japaneseCaptions)
    koreanCaptions, japaneseCaptions = deleteGap(koreanCaptions, japaneseCaptions)
    koreanCaptions, japaneseCaptions = deleteOverlappedCaptions(koreanCaptions, japaneseCaptions)
    for i in range(len(koreanCaptions)):
        print('\n')
        print(koreanCaptions[i])
        print(japaneseCaptions[i])
    
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

def deleteGap(mainCaptions: list[dict], subCaptions: list[dict]):
    # mainCaptionsとsubCaptionsのstartとendが同じという前提
    # mainCaptionsとsubCaptionsの長さが同じという前提
    # enumerateを使用してリストの要素とインデックスを同時に取得
    mainCaptions = [caption for i, caption in enumerate(mainCaptions) if abs(caption['end'] - caption['start']) > 0.1]
    subCaptions = [caption for i, caption in enumerate(subCaptions) if abs(caption['end'] - caption['start']) > 0.1]
    
    mainCaptions = list(map(roundCaption,mainCaptions))
    subCaptions = list(map(roundCaption,subCaptions))
    
    # そのendの値が次のstartと同じか大きい場合、そのendの値を次のstartより0.001秒小さくする。ただし、startよりendが小さくなってはならない。
    for i in range(len(mainCaptions)):
        if i == len(mainCaptions) - 1:
            break
        if mainCaptions[i]['end'] >= mainCaptions[i + 1]['start'] and mainCaptions[i]['end'] - 0.001 > mainCaptions[i]['start']:
            mainCaptions[i]['end'] = round(mainCaptions[i + 1]['start'] - 0.001, 3)
            subCaptions[i]['end'] = round(subCaptions[i + 1]['start'] - 0.001, 3)
    return mainCaptions, subCaptions

def roundCaption(caption: dict):
    return {
        'text': caption['text'],
        'start': round(caption['start'], 3),
        'end': round(caption['end'], 3)
    }

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
            if i + overlapCount + count >= len(mainCaptions):
                return overlapCount
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
            if i + overlapCount + count >= len(mainCaptions):
                return overlapCount
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

def main():
    flavor = cf.getFlavor()
    setVideos(flavor, isNonStop = cf.answeredYes('動画ごとの確認をスキップしますか？'))

if __name__ == '__main__':
    main()