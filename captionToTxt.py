import youtube_transcript_api
import datetime
import requests
import pprint
from requests_oauthlib import OAuth1
import os
import json
from apiclient.discovery import build



def outputFirestoreJson(video_id):
    #ここのパラメーターを決める
    celebrityIds = [] #いちいち決める場合は[]
    isTitleSame = False
    category = "music" #いちいち決める場合はNone。それ以外はmusicかvideoを選択
    playlistIds = [] #いちいち決める場合は[]

    try:
        # YouTubeのAPIキーを設定する
        api_key = 'AIzaSyCsm_qh58EORAOD8e00AXYDdlyT4yKRq2Y'
        # YouTubeのAPIを使用して動画情報を取得する
        youtube = build('youtube', 'v3', developerKey=api_key)
        response = youtube.videos().list(part='snippet', id=video_id).execute()

        # 動画情報からタイトルを取得する
        title = response['items'][0]['snippet']['title']
        channelId = response['items'][0]['snippet']['channelId']
        publishedAt = response['items'][0]['snippet']['publishedAt']
        channelTitle = response['items'][0]['snippet']['channelTitle'] 
        thumbnailUrl = response['items'][0]['snippet']['thumbnails']['medium']['url']

        pprint.pprint(response)

        firestoreData = {
            "category": "music",
            "celebrityIds": None,
            "channelId": channelId,
            "channelTitle": channelTitle,
            "isInvisible": False,
            "jsonUrl": None,
            "playlistIds": None,
            "publishedAt": publishedAt,
            "publishedIn": int(publishedAt.split("-")[0]),
            "thumbnailUrl": thumbnailUrl,
            "title": None,
            "translatedFrom": "ko",
            "translatedTo": "ja",
            "videoId": video_id,
            "youtubeTitle": title,
        }

        print("これがjsonDataです:")
        pprint.pprint(firestoreData)

        while 1:
            if category == None:
                while 1:
                    print("カテゴリはvideoかmusicどっち？(v/m)")
                    category = input()
                    if category == "v" or category == "m":
                        if category == "v":
                            category = "video"
                        else:
                            category = "music"
                        break
            
            if not isTitleSame:
                print("タイトルはなんですか？")
                title = input()

            if bool(celebrityIds) == False:
                print("含まれているアーティストのCelebrityIdを入力してください。複数ある場合は','で区切ってください")
                celebrityIdsStr = input()
                celebrityIds = celebrityIdsStr.split(",")

            if bool(playlistIds) == False:
                print("含まれているプレイリストのplaylistIdを入力してください。複数ある場合は','で区切ってください")
                playlistIdsStr = input()
                if playlistIdsStr == "":
                    playlistIds = []
                else:
                    playlistIds = playlistIdsStr.split(",")

            isPremium = False
            #プレミアム設定は一旦なし
            # while 1:
            #     print("これはpremium動画ですか？(y/n)")
            #     isPremiumYN = input()
            #     if isPremiumYN == "y":
            #         isPremium = True
            #         break
            #     if isPremiumYN == "n":
            #         isPremium = False
            #         break
        
            print("これでよろしいですか？(y/n)")
            pprint.pprint({
                "title": title,
                "celebrityIds": celebrityIds,
                "playlistIds": playlistIds,
                "isPremium": isPremium,
                "category": category
            })
            isGood = input()
            if isGood == "y":
                firestoreData["title"] = title
                firestoreData["celebrityIds"] = celebrityIds
                firestoreData["playlistIds"] = playlistIds
                firestoreData["isPremium"] = isPremium
                firestoreData["category"] = category
                break


        json_data = json.dumps(firestoreData, indent=4, ensure_ascii=False)

        with open(f'videos/{video_id}/firestore.json', 'w') as f:
            f.write(json_data)

    except HttpError as e:
        print('An error occurred')

def translate(word):
    name = 'basssu'
    api_key = '7dc698ce55ecc3e27486e89377dba6f0064350f3b'
    api_secret = '30191cfdcd26ac1df6bbf82ea3492aa1'
    url = 'https://mt-auto-minhon-mlt.ucri.jgn-x.jp/api/mt/generalNT_ko_ja/'    
    data = {
        'key': api_key,
        'name': name,
        'type': 'json',
        'text': word,
        'split' : '1',
        'history' : '0',
        }       

    response = requests.post(url, data=data, auth=OAuth1(api_key, api_secret)).json()
    pprint.pprint(response)
    associate = response['resultset']['result']['text']
    # print(associate)
    return associate

# 翻訳したいテキストを入力
def generateArray(text):
    splitedText = text.split(" ")
    associates = []
    for word in splitedText:
        associates.append(translate(word))
    japanese = ' '.join(associates)
    return japanese

# 韓国語字幕をダウンロードする関数
def download_korean_subtitle(video_id):
    try:
        transcript_list = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            if transcript.language_code == 'ko':
                return transcript.fetch()
        return None
    except:
        return None

# 日本語字幕をダウンロードする関数
def download_japanese_subtitle(video_id):
    try:
        transcript_list = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            if transcript.language_code == 'ja':
                return transcript.fetch()
        return None
    except:
        return None

# srtファイルに書き込む関数
def write_srt_file(korean_subtitle_list, japanese_subtitle_list, file_name, type): #typeの中には"onlyKa", "onlyJa" のどっちかが入る
    with open(file_name, mode='w', encoding='utf-8') as file:
        for i, korean_subtitle in enumerate(korean_subtitle_list):
            start_time = korean_subtitle['start']
            duration = korean_subtitle['duration']
            korean_subtitle_text = korean_subtitle['text']

            end_time = start_time + duration
            start_time_obj = datetime.timedelta(seconds=start_time) + datetime.datetime(1900,1,1)
            end_time_obj = datetime.timedelta(seconds=end_time) + datetime.datetime(1900,1,1)
            start_time_str = start_time_obj.strftime('%H:%M:%S,%f')[:-3]
            end_time_str = end_time_obj.strftime('%H:%M:%S,%f')[:-3]

            # meaning = generateArray(korean_subtitle_text)
            meaning = ""

            
            file.write(str(i + 1) + '\n')
            file.write(start_time_str + ' --> ' + end_time_str + '\n')
            if(type != "onlyJa"):
                file.write(korean_subtitle_text.replace("\n", " ") + '\n')
            # file.write(meaning + '\n')
            if(type != "onlyKa"):
                japanese_subtitle_text = japanese_subtitle_list[i]['text']
                file.write(japanese_subtitle_text.replace("\n", " ") + '\n')
            file.write('\n')

            # print(str(i + 1))
            # print(start_time_str + ' --> ' + end_time_str + '\n')
            # print(korean_subtitle_text)
            # # print(meaning)
            # print(japanese_subtitle_text)
            # print('\n')


# YouTube動画IDを指定

import sys

# コマンドライン引数からパラメータを受け取る
params = sys.argv[1:]

video_id = params[0]

# 韓国語字幕をダウンロード
korean_subtitle_list1 = download_korean_subtitle(video_id)

# 日本語字幕をダウンロード
japanese_subtitle_list1 = download_japanese_subtitle(video_id)
# 両方の配列を見て、"duration"と"start"の値が一致する要素を抽出
korean_subtitle_list = [item for item in korean_subtitle_list1 if any(item["duration"] == j_item["duration"] and item["start"] == j_item["start"] for j_item in japanese_subtitle_list1)]
japanese_subtitle_list = [item for item in japanese_subtitle_list1 if any(item["duration"] == k_item["duration"] and item["start"] == k_item["start"] for k_item in korean_subtitle_list1)]
# ファイルに書き込む
if korean_subtitle_list is None or japanese_subtitle_list is None or len(japanese_subtitle_list) != len(korean_subtitle_list):
    print('subtitle is not available for this video.:')
    print(video_id)
    exit

if not os.path.exists('videos'):
    os.mkdir('videos')

if not os.path.exists(f'videos/{video_id}'):
    os.mkdir(f'videos/{video_id}')

write_srt_file(korean_subtitle_list, japanese_subtitle_list, f'videos/{video_id}/subtitle_ka.srt', "onlyKa")
write_srt_file(korean_subtitle_list, japanese_subtitle_list, f'videos/{video_id}/subtitle_ja.srt', "onlyJa")

outputFirestoreJson(video_id)


