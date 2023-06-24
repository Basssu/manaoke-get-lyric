import ConvenientFunctions as cf
import youtube_transcript_api
import CaptionsToJson
import MakeFirestoreMap
import ToStorage
import ToFireStore
import pprint

# ビデオIDを入力する
def inputVideoIds() -> list[str]:
    videoIds = cf.inputText('videoIdを入力(複数ある場合は","で区切ってください)')
    videoIds = videoIds.split(",")
    return videoIds

def videoIdsLoop(videoIds: list[str]):
    for videoId in videoIds:
        setEachVideo(videoId)
        if not cf.answeredYes('次の動画に進みますか？'):
            unfinishedVideoIds = videoIds[videoIds.index(videoId):]
            break

def checkCaptionAvailability(videoId: str) -> list[str]:
    captionList = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(videoId)
    availableLanguages = []
    for caption in captionList:
        if caption.language_code == 'ko' and not caption.is_generated:
            availableLanguages.append('ko')
        if caption.language_code == 'ja' and not caption.is_generated:
            availableLanguages.append('ja')
    return availableLanguages

def setEachVideo(videoId: str):
    availableLanguages = checkCaptionAvailability(videoId)
    if availableLanguages == []: # 日本語・韓国語字幕がない場合
        print(f"{videoId}: この動画には日本語・韓国語字幕がないため、スキップします")
        skippedVideoIdsAndReasons.append(f'{videoId}:日本語・韓国語字幕がありません')
        return
    
    if availableLanguages == ['ko']: # 日本語字幕がない場合
        print(f"{videoId}: この動画には韓国語字幕しかないため、スキップします")
        skippedVideoIdsAndReasons.append(f'{videoId}: 韓国語字幕しかありません')
        return
    
    if availableLanguages == ['ja']: # 韓国語字幕がない場合
        print(f"{videoId}: この動画には日本語字幕があるため、続行します")
        japaneseCaptions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId, 
            languages=['ja'],
            )
        srtData = convertCaptionsToSrt(japaneseCaptions)
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, True)
        url = ToStorage.toStorage(videoId, flavor, srtData, True)
    
    if 'ja' in availableLanguages and 'ko' in availableLanguages: # 日本語・韓国語字幕がある場合
        print(f"{videoId}: この動画には日本語・韓国語字幕があるため、続行します")
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
            skippedVideoIdsAndReasons.append(f'{videoId}: 字幕の行数を見てスキップすると自分で判断しました。')
            return
        jsonData = CaptionsToJson.captionsToJson(koreanCaptions, japaneseCaptions)
        if len(jsonData) != len(koreanCaptions):
            print(f'{videoId}: スクレイプした字幕の行数とjsonの行数が一致しないため、スキップします。')
            skippedVideoIdsAndReasons.append(f'{videoId}: スクレイプした字幕の行数とjsonの行数が一致しない')
            return
        firestoreMap = MakeFirestoreMap.makeFirestoreMap(videoId, policy, False)
        url = ToStorage.toStorage(videoId, flavor, jsonData, False)
    
    document = ToFireStore.toFirestore(firestoreMap, url, flavor)
    pprint.pprint(document) #Firestoreにアップロードした内容

def deleteIfOneCaptionNotExist(mainCaptions: list[dict], subCaptions: list[dict]) -> list[dict]:
    captions = []
    for mainCaption in mainCaptions:
        for subCaption in subCaptions:
            if mainCaption['start'] == subCaption['start'] and mainCaption['duration'] == subCaption['duration']:
                captions.append(mainCaption)
                break
    return captions

def convertCaptionsToSrt(captions: list) -> str:
    srt = ''
    for i, line in enumerate(captions, start=1):
        start = line['start']
        end = start + line['duration']
        text = line['text']
        srt += f'{i}\n{cf.formatTime(start)} --> {cf.formatTime(end)}\n{text}\n\n'
    return srt

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

def getFlavor() -> str:
    return 'prod' if cf.answeredYes('flavorはどっち？(y = prod, n = stg)') else 'stg'

def main():
    videoIdsLoop(inputVideoIds())
    print('以下の動画はスキップしました。')
    print(",".join(skippedVideoIdsAndReasons))
    print('\n')
    print('スキップした理由は以下の通りです。')
    print("\n".join(skippedVideoIdsAndReasons))
    print('\n')
    print('以下の動画は手を付けていません。')
    print(",".join(unfinishedVideoIds))

skippedVideoIdsAndReasons = []
unfinishedVideoIds = []
flavor = getFlavor()
policy = setPolicy()
main()

