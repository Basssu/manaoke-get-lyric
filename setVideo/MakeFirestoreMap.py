import os
import sys
sys.path.append(os.pardir)
from googleapiclient.discovery import build
import ConvenientFunctions as cf
import GetYoutubeData
import datetime
import pytz

def makeFirestoreMap(
    videoId: str, 
    policy: dict, 
    isGonneBeUncompletedVideo: bool, 
    hasTranslationFrom: bool,
    hasTranslationTo: bool,
    ):
    response = GetYoutubeData.getVideo(videoId)
    if response is None:
        print('動画情報無し')
        return None
    youtubeTitle: str = response['snippet']['title']
    title = youtubeTitle
    channelId = response['snippet']['channelId']
    publishedAt = response['snippet']['publishedAt']
    channelTitle = response['snippet']['channelTitle'] 
    thumbnailUrl = response['snippet']['thumbnails']['medium']['url']
    durationInMilliseconds = youtubeDurationToInMilliseconds(response['contentDetails']['duration'])
    print(f'videoId: {videoId}')
    print(f'title: {title}')

    if policy["setIfTitleIsSameAsYoutubeTitleEachTime"]:
        if not cf.answered_yes('タイトルはYoutubeのタイトルと同じですか？'):
            title = cf.input_text('タイトルを入力してください。')   
    else:
        if not policy["IsTitleSameAsYoutubeTitle"]:
            title = cf.input_text('タイトルを入力してください。')

    celebrityIds = cf.input_text('celebrityIdsを入力してください。(複数の場合、","で区切ってください)') .split(",")if policy["setCelebrityIdsEachTime"] else policy["celebrityIds"]
    if celebrityIds == ['']:
        celebrityIds = []
    
    playlistIds = cf.input_text('playlistIdsを入力してください。(複数の場合、","で区切ってください)') .split(",") if policy["setPlaylistIdsEachTime"] else policy["playlistIds"]
    if playlistIds == ['']: 
        playlistIds = []

    firestoreData = {
            "category": 
            policy['category'] 
            if not policy['setCategoryEachTime'] 
            else 'video' 
            if cf.answered_yes('カテゴリーはどっち？(y = video, n = music)') 
            else 'music',
            "celebrityIds": celebrityIds,
            "channelId": channelId,
            "channelTitle": channelTitle,
            "createdAt": datetime.datetime.now(pytz.timezone('Asia/Tokyo')),
            "durationInMilliseconds": durationInMilliseconds,
            "hasTranslationAfterSubtitles": hasTranslationTo,
            "hasTranslationBeforeSubtitles": hasTranslationFrom,
            "isCaptionFromModified": False, #仮
            "isCaptionToModified": False, #仮
            "isInvisible": durationInMilliseconds < 60000,
            "isPremium": False,
            "isUncompletedVideo": isGonneBeUncompletedVideo,
            "isVerified": not isGonneBeUncompletedVideo,
            "playlistIds": playlistIds,
            "publishedAt": datetime.datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ"),
            "thumbnailUrl": thumbnailUrl,
            "title": title,
            "translatedFrom": "ko",
            "translatedTo": "ja",
            "updatedAt": datetime.datetime.now(pytz.timezone('Asia/Tokyo')),
            "videoId": videoId,
            "youtubeTitle": youtubeTitle,
        }
    if firestoreData['category'] == 'music':
        firestoreData["tokenList"] = makeTokenListFromText(title)

    return firestoreData

def makeTokenListFromText(text: str) -> list[str]:
    tokenList = []
    ngList = ["ver", "Ver", "VER", "feat", "Feat", "Prod", "prod", "mv", "MV"]
    textWithoutKakko = cf.remove_brackets(text, '()')
    if text != textWithoutKakko and text.count("(") == 1 and text.count(")") == 1:
        insideKakko = text[text.find("(")+1:text.find(")")]
        if not any((a in insideKakko) for a in ngList):
            tokenList = makeTokenListFromEachLetterCaseOfText(insideKakko)

    tokenList = list(set(makeTokenListFromEachLetterCaseOfText(textWithoutKakko) + tokenList)) #重複を削除
    return sorted(tokenList)

def makeTokenListFromEachLetterCaseOfText(text: str) -> list[str]:
    resultList = []
    for letterSize in [text, text.upper(), text.lower(), text.capitalize()]:
        resultList = list(set(makeNGram(letterSize) + resultList)) #重複を削除
    return resultList

def makeNGram(text: str) -> list[str]:
    resultList = []
    for i in range(len(text)):
        token = text[0:i + 1]
        resultList.append(token)
    return list(set(resultList)) #重複を削除

def youtubeDurationToInMilliseconds(durationStr: str) -> int:
    # 時間の部分（PT1H30M）と秒の部分（PT30S）に分割します
    time_part = durationStr.replace('PT', '').replace('H', 'H ').replace('M', 'M ').replace('S', 'S')
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