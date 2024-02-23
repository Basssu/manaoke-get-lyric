from googleapiclient.discovery import build
import youtube_transcript_api
import ConvenientFunctions as cf
import GetYoutubeData

def video_ids_from_playlist_id(playlistId: str):
    videoIds = []
    playlistItems = GetYoutubeData.getItemResponseFromPlaylist(playlistId)
    for i in range(len(playlistItems)):
        videoIds.append(playlistItems[i]['snippet']['resourceId']['videoId'])
    return videoIds

def caption_language_from_video_id(videoId: str) -> list[str]:
    languages = []
    if has_this_language_caption('ja', videoId):
        languages.append('ja')
    if has_this_language_caption('ko', videoId):
        languages.append('ko')

    languages.sort()
    return languages

def has_this_language_caption(languageCode: str, videoId: str):
    try:
        transcriptList = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(videoId)
        for transcript in transcriptList:
            if transcript.language_code == languageCode and not transcript.is_generated:
                return True
    except:
        print('error: ' + videoId + ' has no caption')
    return False

def show_video_ids_with_caption(videoIds: list[str]):
    videosWithoutCaption = []
    videosWithOnlyJapaneseCaption = []
    videosWithOnlyKoreanCaption = []
    videosWithBothJapaneseAndKoreanCaption = []
    for videoId in videoIds:
        print(f'{videoIds.index(videoId)} / {len(videoIds)}')
        languages = caption_language_from_video_id(videoId)
        if not languages:
            videosWithoutCaption.append(videoId)
            continue
        if languages == ['ja']:
            videosWithOnlyJapaneseCaption.append(videoId)
            continue
        if languages == ['ko']:
            videosWithOnlyKoreanCaption.append(videoId)
            continue
        if languages == sorted(['ja', 'ko']):
            videosWithBothJapaneseAndKoreanCaption.append(videoId)
            continue

    print('字幕がない動画の数: ' + str(len(videosWithoutCaption)))
    print(','.join(videosWithoutCaption) + '\n')
    print('日本語字幕のみの動画の数: ' + str(len(videosWithOnlyJapaneseCaption)))
    print(','.join(videosWithOnlyJapaneseCaption) + '\n')
    print('韓国語字幕のみの動画の数: ' + str(len(videosWithOnlyKoreanCaption)))
    print(','.join(videosWithOnlyKoreanCaption) + '\n')
    print('日本語字幕と韓国語字幕の両方がある動画の数: ' + str(len(videosWithBothJapaneseAndKoreanCaption)))
    print(','.join(videosWithBothJapaneseAndKoreanCaption) + '\n')
    print('全ての動画の数: ' + str(len(videoIds)))
    print(','.join(videoIds) + '\n')

def main():
    playlistId = cf.input_text('playlistIdを入力')
    videoIds = video_ids_from_playlist_id(playlistId)
    show_video_ids_with_caption(videoIds)

if __name__ == '__main__':
    main()