import os
import sys
sys.path.append(os.pardir)
from googleapiclient.discovery import build
import convenient_functions as cf
import get_youtube_data as get_youtube_data
import datetime
import pytz

def make_firestore_map(
    video_id: str, 
    policy: dict, 
    is_gonne_be_uncompleted_video: bool, 
    has_translation_from: bool,
    has_translation_to: bool,
    ):
    response = get_youtube_data.get_video(video_id)
    if response is None:
        print('動画情報無し')
        return None
    youtube_title: str = response['snippet']['title']
    title = youtube_title
    channel_id = response['snippet']['channelId']
    published_at = response['snippet']['publishedAt']
    channel_title = response['snippet']['channelTitle'] 
    thumbnail_url = response['snippet']['thumbnails']['medium']['url']
    duration_in_milliseconds = youtube_duration_to_in_milliseconds(response['contentDetails']['duration'])
    print(f'videoId: {video_id}')
    print(f'title: {title}')

    if policy["setIfTitleIsSameAsYoutubeTitleEachTime"]:
        if not cf.answered_yes('タイトルはYoutubeのタイトルと同じですか？'):
            title = cf.input_text('タイトルを入力してください。')   
    else:
        if not policy["IsTitleSameAsYoutubeTitle"]:
            title = cf.input_text('タイトルを入力してください。')

    celebrity_ids = cf.input_text('celebrityIdsを入力してください。(複数の場合、","で区切ってください)') .split(",")if policy["setCelebrityIdsEachTime"] else policy["celebrityIds"]
    if celebrity_ids == ['']:
        celebrity_ids = []
    
    playlist_ids = cf.input_text('playlistIdsを入力してください。(複数の場合、","で区切ってください)') .split(",") if policy["setPlaylistIdsEachTime"] else policy["playlistIds"]
    if playlist_ids == ['']: 
        playlist_ids = []

    firestore_data = {
            "category": 
            policy['category'] 
            if not policy['setCategoryEachTime'] 
            else 'video' 
            if cf.answered_yes('カテゴリーはどっち？(y = video, n = music)') 
            else 'music',
            "celebrityIds": celebrity_ids,
            "channelId": channel_id,
            "channelTitle": channel_title,
            "createdAt": datetime.datetime.now(pytz.timezone('Asia/Tokyo')),
            "durationInMilliseconds": duration_in_milliseconds,
            "hasTranslationAfterSubtitles": has_translation_to,
            "hasTranslationBeforeSubtitles": has_translation_from,
            "isCaptionFromModified": False, #仮
            "isCaptionToModified": False, #仮
            "isInvisible": duration_in_milliseconds < 60000,
            "isPremium": False,
            "isUncompletedVideo": is_gonne_be_uncompleted_video,
            "isVerified": not is_gonne_be_uncompleted_video,
            "playlistIds": playlist_ids,
            "publishedAt": datetime.datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ"),
            "thumbnailUrl": thumbnail_url,
            "title": title,
            "translatedFrom": "ko",
            "translatedTo": "ja",
            "updatedAt": datetime.datetime.now(pytz.timezone('Asia/Tokyo')),
            "videoId": video_id,
            "youtubeTitle": youtube_title,
        }
    if firestore_data['category'] == 'music':
        firestore_data["tokenList"] = make_token_list_from_text(title)

    return firestore_data

def make_token_list_from_text(text: str) -> list[str]:
    token_list = []
    ng_list = ["ver", "Ver", "VER", "feat", "Feat", "Prod", "prod", "mv", "MV"]
    text_without_kakko = cf.remove_brackets(text, '()')
    if text != text_without_kakko and text.count("(") == 1 and text.count(")") == 1:
        inside_kakko = text[text.find("(")+1:text.find(")")]
        if not any((a in inside_kakko) for a in ng_list):
            token_list = make_token_list_from_each_letter_case_of_text(inside_kakko)

    token_list = list(set(make_token_list_from_each_letter_case_of_text(text_without_kakko) + token_list)) #重複を削除
    return sorted(token_list)

def make_token_list_from_each_letter_case_of_text(text: str) -> list[str]:
    result_list = []
    for letter_size in [text, text.upper(), text.lower(), text.capitalize()]:
        result_list = list(set(make_n_gram(letter_size) + result_list)) #重複を削除
    return result_list

def make_n_gram(text: str) -> list[str]:
    result_list = []
    for i in range(len(text)):
        token = text[0:i + 1]
        result_list.append(token)
    return list(set(result_list)) #重複を削除

def youtube_duration_to_in_milliseconds(duration_str: str) -> int:
    # 時間の部分（PT1H30M）と秒の部分（PT30S）に分割します
    time_part = duration_str.replace('PT', '').replace('H', 'H ').replace('M', 'M ').replace('S', 'S')
    time_parts = time_part.split()
    minutes = 0
    seconds = 0
    for part in time_parts:
        if part.endswith('H'):
            hours = int(part[:-1])
            minutes += hours * 60
        elif part.endswith('M'):
            minutes += int(part[:-1])
        elif part.endswith('S'):
            seconds += int(part[:-1])

    return (minutes * 60 + seconds) * 1000