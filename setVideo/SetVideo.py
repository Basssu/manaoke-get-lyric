import ConvenientFunctions as cf
import youtube_transcript_api
import CaptionsToJson
import MakeFirestoreMap
import ToStorage
import ToFireStore
import pprint
from typing import Optional
import firebase_admin

# ビデオIDを入力する
def inputVideoIds() -> list[str]:
    videoIds = cf.inputText('videoIdを入力(複数ある場合は","で区切ってください)')
    videoIds = videoIds.split(",")
    return videoIds

def videoIdsLoop(videoIds: list[str], flavor: str, policy: dict) -> list[str]: # 返り値は、スキップされた動画のvideoIdのリスト
    skippedVideoIds = []
    cf.initializeFirebase(flavor)
    for videoId in videoIds:
        isNotSkipped = setEachVideo(videoId, flavor, policy)
        if not isNotSkipped:
            skippedVideoIds.append(videoId)
        if not cf.answeredYes('次の動画に進みますか？'):
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

def setEachVideo(videoId: str, flavor: str, policy: dict) -> bool: #返り値は、この動画が追加されたかどうか(true: 正常に追加された, false: 追加されなかった)
    availableLanguages = checkCaptionAvailability(videoId)
    if availableLanguages == []: # 日本語・韓国語字幕がない場合
        print(f"{videoId}: この動画には日本語・韓国語字幕どちらもありません")
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, True, availableLanguages)
        if cf.answeredYes('この動画をスキップしますか？'): return False
        url = None
    
    if availableLanguages == ['ko']: # 日本語字幕がない場合
        print(f"{videoId}: この動画には韓国語字幕があります")
        koreanCaptions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId, 
            languages=['ko'],
            )
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, True, availableLanguages)
        if cf.answeredYes('この動画をスキップしますか？'): return False
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
        if cf.answeredYes('この動画をスキップしますか？'): return False
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
        koreanCaptions = deleteIfOneCaptionNotExist(koreanCaptions, japaneseCaptions)
        japaneseCaptions = deleteIfOneCaptionNotExist(japaneseCaptions, koreanCaptions)
        if not cf.answeredYes(f'{videoId}:字幕の行数は{len(koreanCaptions)}行です。続けますか？'):
            return False
        jsonData = CaptionsToJson.captionsToJson(koreanCaptions, japaneseCaptions)
        if len(jsonData) != len(koreanCaptions):
            print(f'{videoId}: スクレイプした字幕の行数とjsonの行数が一致しないため、スキップします。')
            return False
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, False, availableLanguages)
        if cf.answeredYes('この動画をスキップしますか？'): return False
        url = ToStorage.toStorage(f'ko_ja_{videoId}', flavor, jsonData, availableLanguages)
    
    document = ToFireStore.toFirestore(firestoreMap, url, flavor, f'ko_ja_{videoId}', availableLanguages)
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

def main():
    flavor = cf.getFlavor()
    policy = setPolicy()
    skippedVideoList = videoIdsLoop(inputVideoIds(), flavor, policy)
    print(f'スキップした動画の数は{len(skippedVideoList)}です。')
    print(f'スキップした動画のIDは{skippedVideoList}です。')

if __name__ == '__main__':
    main()