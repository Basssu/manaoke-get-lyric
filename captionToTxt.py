import youtube_transcript_api
import datetime
import requests
import pprint
from requests_oauthlib import OAuth1
import os
import json
# from youtube_transcript_api import YouTubeTranscriptApi
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
import sys
sys.path.append('/opt/homebrew/lib/python3.10/site-packages')
from apiclient.discovery import build


def outputFirestoreJson(video_id):
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

        firestoreData = {
            "videoId": video_id,
            "youtubeTitle": title,
            "title": None,
            "channelId": channelId,
            "publishedAt": publishedAt,
            "publishedIn": int(publishedAt.split("-")[0]),
            "channelTitle": channelTitle,
            "artist": None,
            "translatedFrom": "ko",
            "translatedTo": "ja",
            "jsonUrl": None,
            "category": "music"
        }

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
                file.write(korean_subtitle_text + '\n')
            # file.write(meaning + '\n')
            if(type != "onlyKa"):
                japanese_subtitle_text = japanese_subtitle_list[i]['text']
                file.write(japanese_subtitle_text + '\n')
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
korean_subtitle_list = download_korean_subtitle(video_id)

# 日本語字幕をダウンロード
japanese_subtitle_list = download_japanese_subtitle(video_id)

# ファイルに書き込む
if korean_subtitle_list is None or japanese_subtitle_list is None or len(japanese_subtitle_list) != len(korean_subtitle_list):
    print('subtitle is not available for this video.')
    exit

if not os.path.exists('videos'):
    os.mkdir('videos')

if not os.path.exists(f'videos/{video_id}'):
    os.mkdir(f'videos/{video_id}')

write_srt_file(korean_subtitle_list, japanese_subtitle_list, f'videos/{video_id}/subtitle_ka.srt', "onlyKa")
write_srt_file(korean_subtitle_list, japanese_subtitle_list, f'videos/{video_id}/subtitle_ja.srt', "onlyJa")

outputFirestoreJson(video_id)


