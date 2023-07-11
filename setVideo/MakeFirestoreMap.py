import os
import sys
sys.path.append(os.pardir)
from apiKey import config
from googleapiclient.discovery import build
import ConvenientFunctions as cf
import re
import datetime
import pytz

def makeFirestoreMap(videoId: str, policy: dict, isGonneBeUncompletedVideo: bool, captionLanguages: list[str]):
    apikey = config.YOUTUBE_API_KEY
    youtube = build('youtube', 'v3', developerKey=apikey)
    response = youtube.videos().list(part='snippet,contentDetails', id=videoId).execute()

    youtubeTitle: str = response['items'][0]['snippet']['title']
    title = youtubeTitle
    channelId = response['items'][0]['snippet']['channelId']
    publishedAt = response['items'][0]['snippet']['publishedAt']
    channelTitle = response['items'][0]['snippet']['channelTitle'] 
    thumbnailUrl = response['items'][0]['snippet']['thumbnails']['medium']['url']
    defaultAudioLanguage = response['items'][0]['snippet']['defaultAudioLanguage']
    durationInMilliseconds = youtubeDurationToInMilliseconds(response['items'][0]['contentDetails']['duration'])
    print(f'videoId: {videoId}')
    print(f'title: {title}')

    if policy["setIfTitleIsSameAsYoutubeTitleEachTime"]:
        if not cf.answeredYes('タイトルはYoutubeのタイトルと同じですか？'):
            title = cf.inputText('タイトルを入力してください。')   
    else:
        if not policy["IsTitleSameAsYoutubeTitle"]:
            title = cf.inputText('タイトルを入力してください。')

    celebrityIds = cf.inputText('celebrityIdsを入力してください。(複数の場合、","で区切ってください)') .split(",")if policy["setCelebrityIdsEachTime"] else policy["celebrityIds"]
    if celebrityIds == ['']:
        celebrityIds = []
    
    playlistIds = cf.inputText('playlistIdsを入力してください。(複数の場合、","で区切ってください)') .split(",") if policy["setPlaylistIdsEachTime"] else policy["playlistIds"]
    if playlistIds == ['']: 
        playlistIds = []

    firestoreData = {
            "category": 
            policy['category'] 
            if not policy['setCategoryEachTime'] 
            else 'video' 
            if cf.answeredYes('カテゴリーはどっち？(y = video, n = music)') 
            else 'music',
            "celebrityIds": celebrityIds,
            "channelId": channelId,
            "channelTitle": channelTitle,
            "defaultAudioLanguage": defaultAudioLanguage,
            "durationInMilliseconds": durationInMilliseconds,
            "isInvisible": False,
            "isPremium": False,
            "isUncompletedVideo": isGonneBeUncompletedVideo,
            "isWaitingForReview": False,
            # "jsonUrl": None,
            # 'originnalCaptionLanguages': [],
            "playlistIds": playlistIds,
            "publishedAt": datetime.datetime.strptime(publishedAt, "%Y-%m-%dT%H:%M:%SZ"),
            "publishedIn": int(publishedAt.split("-")[0]),
            "thumbnailUrl": thumbnailUrl,
            "title": title,
            "tokenList": makeTokenListFromText(title),
            "translatedFrom": "ko",
            "translatedTo": "ja",
            "updatedAt": datetime.datetime.now(pytz.timezone('Asia/Tokyo')),
            "videoId": videoId,
            "youtubeTitle": youtubeTitle,
        }

    return firestoreData

def makeTokenListFromText(text: str) -> list[str]:
    tokenList = []
    ngList = ["ver", "Ver", "VER", "feat", "Feat", "Prod", "prod", "mv", "MV"]
    textWithoutKakko = removeBrackets(text, '()')
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

def removeBrackets(text: str, brackets: str) -> str:
    pattern = re.escape(brackets[0]) + r'[^\[{}\]()]*' + re.escape(brackets[1])
    result = re.sub(pattern, '', text)
    return result

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