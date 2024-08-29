from . import convenient_functions as cf
import youtube_transcript_api
from . import make_firestore_map as make_firestore_map
from . import to_firestore as to_firestore
import pprint
from typing import Optional, Tuple
from . import notification
from . import to_storage as to_storage

# ビデオIDを入力する
def input_video_ids() -> list[str]:
    video_ids = cf.input_text('videoIdを入力(複数ある場合は","で区切ってください)')
    video_ids = video_ids.split(",")
    result_video_ids = []
    for video_id in video_ids:
        if not video_id in result_video_ids:
            result_video_ids.append(video_id)
    return result_video_ids

def video_ids_loop(video_ids: list[str], flavor: str, policy: dict, is_non_stop: bool) -> list[str]: # 返り値は、スキップされた動画のvideoIdのリスト
    skipped_video_ids = []
    cf.initialize_firebase(flavor)
    for video_id in video_ids:
        is_not_skipped = set_each_video(video_id, flavor, policy, is_non_stop)
        if not is_not_skipped:
            skipped_video_ids.append(video_id)
        if not is_non_stop and not cf.answered_yes('次の動画に進みますか？'):
            return skipped_video_ids
    return skipped_video_ids

def set_each_video(video_id: str, flavor: str, policy: dict, is_non_stop: bool) -> bool: #返り値は、この動画が追加されたかどうか(true: 正常に追加された, false: 追加されなかった)
    caption_json_url = None
    is_uncompleted_video = True
    korean_captions, japanese_captions = fetch_captions(video_id)
    if korean_captions is not None and japanese_captions is not None:
        korean_captions = delete_if_one_caption_not_exist(korean_captions, japanese_captions)
        japanese_captions = delete_if_one_caption_not_exist(japanese_captions, korean_captions)
        is_uncompleted_video = False
        if not cf.answered_yes(f'{video_id}:字幕の行数は{len(korean_captions)}行です。続けますか？'):
            return False
    firestore_map = make_firestore_map.make_firestore_map(
        video_id, 
        policy, 
        is_uncompleted_video, 
        not (korean_captions == None or not korean_captions),
        not (japanese_captions == None or not japanese_captions),
        )
    if (not is_non_stop and cf.answered_yes('この動画をスキップしますか？')) or firestore_map == None: return False
    if not (korean_captions == None and japanese_captions == None):
        caption_json_url = get_caption_json_url(video_id, korean_captions, japanese_captions)
        
    document = to_firestore.to_firestore(firestore_map, flavor, f'ko_ja_{video_id}', caption_json_url)
    pprint.pprint(document) #Firestoreにアップロードした内容
    return True

def fetch_captions(videoId: str) -> Tuple[Optional[list[dict]], Optional[list[dict]]]:
    korean_captions = None
    japanese_captions = None
    available_languages = check_caption_availability(videoId)
    if not available_languages:
        print('この動画には字幕がありません')
        return korean_captions, japanese_captions
    if 'ko' in available_languages:
        korean_captions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId, 
            languages=['ko'],
            )
        print(f'この動画には{len(korean_captions)}行の韓国語字幕があります')
    if 'ja' in available_languages:
        japanese_captions = youtube_transcript_api.YouTubeTranscriptApi.get_transcript(
            videoId,
            languages=['ja'],
            )
        print(f'この動画には{len(japanese_captions)}行の日本語字幕があります')
    return korean_captions, japanese_captions

def check_caption_availability(videoId: str) -> list[str]:
    try:
        caption_list = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(videoId)
    except youtube_transcript_api._errors.TranscriptsDisabled:
        caption_list = []
    available_languages = []
    for caption in caption_list:
        if caption.language_code == 'ko' and not caption.is_generated:
            available_languages.append('ko')
        if caption.language_code == 'ja' and not caption.is_generated:
            available_languages.append('ja')
    return available_languages


def delete_if_one_caption_not_exist(main_captions: list[dict], sub_captions: list[dict]) -> list[dict]:
    captions = []
    for main_caption in main_captions:
        for sub_caption in sub_captions:
            if main_caption['start'] == sub_caption['start'] and main_caption['duration'] == sub_caption['duration']:
                captions.append(main_caption)
                break
    return captions

def get_caption_json_url(video_id: str, main_captions: Optional[list[dict]], sub_captions: Optional[list[dict]]) -> str:
    data = make_caption_dict_list(main_captions, sub_captions)
    url = to_storage.new_json_url(video_id, data)
    return url

def make_caption_dict_list(main_captions: Optional[list[dict]], sub_captions: Optional[list[dict]]) -> list[dict]:
    caption_dict_list = []
    captions_length = 0
    if main_captions != None:
        captions_length = len(main_captions)
    else:
        captions_length = len(sub_captions)
    for i in range(captions_length):
        caption_dict = {}
        if main_captions != None:
            caption_dict['time'] = convert_time_to_srt_format(main_captions[i]['start'], main_captions[i]['duration'])
        else:
            caption_dict['time'] = convert_time_to_srt_format(sub_captions[i]['start'], sub_captions[i]['duration'])
        if main_captions != None:
            caption_dict['from'] = main_captions[i]['text'].replace('\n', ' ')
        if sub_captions != None:
            caption_dict['to'] = sub_captions[i]['text'].replace('\n', ' ')
        caption_dict_list.append(caption_dict)
    return caption_dict_list

def convert_time_to_srt_format(start: float, duration: float) -> str:
    end = start + duration
    time = f'{cf.format_time(start)} --> {cf.format_time(end)}'
    return time

def set_policy() -> dict:
    process_policy = {
        'setCelebrityIdsEachTime': cf.answered_yes('毎回celebrityIdsを入力しますか？'),
        'setIfTitleIsSameAsYoutubeTitleEachTime': cf.answered_yes('タイトルはYoutubeのタイトルと同じか毎回決めますか？'),
        'setCategoryEachTime': cf.answered_yes('毎回カテゴリーを入力しますか？'),
        'setPlaylistIdsEachTime': cf.answered_yes('毎回playlistIdsを入力しますか？'),
    }
    if(not process_policy['setCelebrityIdsEachTime']):
        process_policy['celebrityIds'] = cf.input_text('celebrityIdsを入力してください。(複数の場合、","で区切ってください)').split(",")
    if(not process_policy['setIfTitleIsSameAsYoutubeTitleEachTime']):
        process_policy['IsTitleSameAsYoutubeTitle'] = cf.answered_yes('タイトルはYoutubeのタイトルと同じですか？')
    if(not process_policy['setCategoryEachTime']):
        process_policy['category'] = 'video' if cf.answered_yes('カテゴリーはどっち？(y = video, n = music)') else 'music'
    if(not process_policy['setPlaylistIdsEachTime']):
        process_policy['playlistIds'] = cf.input_text('playlistIdsを入力してください。(複数の場合、","で区切ってください)').split(",")
    return process_policy

def set_videos(flavor: str, youtube_video_ids: list[str] = None, is_non_stop: bool = False):
    policy = set_policy()
    youtube_video_ids = youtube_video_ids if youtube_video_ids != None else input_video_ids()
    skipped_youtube_video_ids = video_ids_loop(youtube_video_ids, flavor, policy, is_non_stop)
    added_youtube_video_ids = [x for x in youtube_video_ids if x not in skipped_youtube_video_ids]
    print(f'スキップした動画の数: {len(skipped_youtube_video_ids)}')
    print(f'スキップした動画のYoutubeVideoID: {skipped_youtube_video_ids}')
    print('\n')
    print(f'追加した動画の数: {len(added_youtube_video_ids)}')
    print(f'追加した動画のYoutubeVideoID: {added_youtube_video_ids}')
    if not cf.answered_yes('通知処理に進みますか？'):
        return
    completed_videos = to_firestore.completed_videos(added_youtube_video_ids)
    completed_video_docs = to_firestore.fetch_videos_by_youtube_video_ids(completed_videos)
    notification.send_celebrity_likers_by_video_docs(completed_video_docs)

def main():
    flavor = cf.get_flavor()
    set_videos(flavor, is_non_stop = cf.answered_yes('動画ごとの確認をスキップしますか？'))