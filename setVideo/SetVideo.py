import ConvenientFunctions as cf
import youtube_transcript_api
import MakeFirestoreMap
import ToFireStore
import pprint
from typing import Optional, Tuple
import Notification
import NewToStorage

# ビデオIDを入力する
def input_video_ids() -> list[str]:
    videoIds = cf.input_text('videoIdを入力(複数ある場合は","で区切ってください)')
    videoIds = videoIds.split(",")
    resultVideoIds = []
    for videoId in videoIds:
        if not videoId in resultVideoIds:
            resultVideoIds.append(videoId)
    return resultVideoIds

def video_ids_loop(videoIds: list[str], flavor: str, policy: dict, isNonStop: bool) -> list[str]: # 返り値は、スキップされた動画のvideoIdのリスト
    skippedVideoIds = []
    cf.initialize_firebase(flavor)
    for videoId in videoIds:
        isNotSkipped = set_each_video(videoId, flavor, policy, isNonStop)
        if not isNotSkipped:
            skippedVideoIds.append(videoId)
        if not isNonStop and not cf.answered_yes('次の動画に進みますか？'):
            return skippedVideoIds
    return skippedVideoIds

def set_each_video(videoId: str, flavor: str, policy: dict, isNonStop: bool) -> bool: #返り値は、この動画が追加されたかどうか(true: 正常に追加された, false: 追加されなかった)
    captionJsonUrl = None
    isUncompletedVideo = True
    koreanCaptions, japaneseCaptions = fetch_captions(videoId)
    if koreanCaptions is not None and japaneseCaptions is not None:
        koreanCaptions = delete_if_one_caption_not_exist(koreanCaptions, japaneseCaptions)
        japaneseCaptions = delete_if_one_caption_not_exist(japaneseCaptions, koreanCaptions)
        isUncompletedVideo = False
        if not cf.answered_yes(f'{videoId}:字幕の行数は{len(koreanCaptions)}行です。続けますか？'):
            return False
    firestoreMap = MakeFirestoreMap.make_firestore_map(
        videoId, 
        policy, 
        isUncompletedVideo, 
        not (koreanCaptions == None or not koreanCaptions),
        not (japaneseCaptions == None or not japaneseCaptions),
        )
    if (not isNonStop and cf.answered_yes('この動画をスキップしますか？')) or firestoreMap == None: return False
    if not (koreanCaptions == None and japaneseCaptions == None):
        captionJsonUrl = get_caption_json_url(videoId, koreanCaptions, japaneseCaptions)
        
    document = ToFireStore.to_firestore(firestoreMap, flavor, f'ko_ja_{videoId}', captionJsonUrl)
    pprint.pprint(document) #Firestoreにアップロードした内容
    return True

def fetch_captions(videoId: str) -> Tuple[Optional[list[dict]], Optional[list[dict]]]:
    koreanCaptions = None
    japaneseCaptions = None
    availableLanguages = check_caption_availability(videoId)
    if not availableLanguages:
        print('この動画には字幕がありません')
        return koreanCaptions, japaneseCaptions
    if 'ko' in availableLanguages:
        print('この動画には韓国語字幕があります')
        koreanCaptions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId, 
            languages=['ko'],
            )
    if 'ja' in availableLanguages:
        print('この動画には日本語字幕があります')
        japaneseCaptions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId,
            languages=['ja'],
            )
    return koreanCaptions, japaneseCaptions

def check_caption_availability(videoId: str) -> list[str]:
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


def delete_if_one_caption_not_exist(mainCaptions: list[dict], subCaptions: list[dict]) -> list[dict]:
    captions = []
    for mainCaption in mainCaptions:
        for subCaption in subCaptions:
            if mainCaption['start'] == subCaption['start'] and mainCaption['duration'] == subCaption['duration']:
                captions.append(mainCaption)
                break
    return captions

def get_caption_json_url(videoId: str, mainCaptions: Optional[list[dict]], subCaptions: Optional[list[dict]]) -> str:
    data = make_caption_dict_list(mainCaptions, subCaptions)
    url = NewToStorage.new_json_url(videoId, data)
    return url

def make_caption_dict_list(mainCaptions: Optional[list[dict]], subCaptions: Optional[list[dict]]) -> list[dict]:
    captionDictList = []
    captionsLength = 0
    if mainCaptions != None:
        captionsLength = len(mainCaptions)
    else:
        captionsLength = len(subCaptions)
    for i in range(captionsLength):
        captionDict = {}
        if mainCaptions != None:
            captionDict['time'] = convert_time_to_srt_format(mainCaptions[i]['start'], mainCaptions[i]['duration'])
        else:
            captionDict['time'] = convert_time_to_srt_format(subCaptions[i]['start'], subCaptions[i]['duration'])
        if mainCaptions != None:
            captionDict['from'] = mainCaptions[i]['text'].replace('\n', ' ')
        if subCaptions != None:
            captionDict['to'] = subCaptions[i]['text'].replace('\n', ' ')
        captionDictList.append(captionDict)
    return captionDictList

def convert_time_to_srt_format(start: float, duration: float) -> str:
    end = start + duration
    time = f'{cf.format_time(start)} --> {cf.format_time(end)}'
    return time

def set_policy() -> dict:
    processPolicy = {
        'setCelebrityIdsEachTime': cf.answered_yes('毎回celebrityIdsを入力しますか？'),
        'setIfTitleIsSameAsYoutubeTitleEachTime': cf.answered_yes('タイトルはYoutubeのタイトルと同じか毎回決めますか？'),
        'setCategoryEachTime': cf.answered_yes('毎回カテゴリーを入力しますか？'),
        'setPlaylistIdsEachTime': cf.answered_yes('毎回playlistIdsを入力しますか？'),
    }
    if(not processPolicy['setCelebrityIdsEachTime']):
        processPolicy['celebrityIds'] = cf.input_text('celebrityIdsを入力してください。(複数の場合、","で区切ってください)').split(",")
    if(not processPolicy['setIfTitleIsSameAsYoutubeTitleEachTime']):
        processPolicy['IsTitleSameAsYoutubeTitle'] = cf.answered_yes('タイトルはYoutubeのタイトルと同じですか？')
    if(not processPolicy['setCategoryEachTime']):
        processPolicy['category'] = 'video' if cf.answered_yes('カテゴリーはどっち？(y = video, n = music)') else 'music'
    if(not processPolicy['setPlaylistIdsEachTime']):
        processPolicy['playlistIds'] = cf.input_text('playlistIdsを入力してください。(複数の場合、","で区切ってください)').split(",")
    return processPolicy

def set_videos(flavor: str, youtubeVideoIds: list[str] = None, isNonStop: bool = False):
    policy = set_policy()
    youtubeVideoIds = youtubeVideoIds if youtubeVideoIds != None else input_video_ids()
    skippedYoutubeVideoIds = video_ids_loop(youtubeVideoIds, flavor, policy, isNonStop)
    addedYoutubeVideoIds = [x for x in youtubeVideoIds if x not in skippedYoutubeVideoIds]
    print(f'スキップした動画の数: {len(skippedYoutubeVideoIds)}')
    print(f'スキップした動画のYoutubeVideoID: {skippedYoutubeVideoIds}')
    print('\n')
    print(f'追加した動画の数: {len(addedYoutubeVideoIds)}')
    print(f'追加した動画のYoutubeVideoID: {addedYoutubeVideoIds}')
    if not cf.answered_yes('通知処理に進みますか？'):
        return
    completedVideos = ToFireStore.completed_videos(addedYoutubeVideoIds)
    completedVideoDocs = ToFireStore.fetch_videos_by_youtube_video_ids(completedVideos)
    Notification.send_celebrity_likers_by_video_docs(completedVideoDocs)

def main():
    flavor = cf.get_flavor()
    set_videos(flavor, isNonStop = cf.answered_yes('動画ごとの確認をスキップしますか？'))

if __name__ == '__main__':
    main()