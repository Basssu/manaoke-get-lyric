from googleapiclient.discovery import build
import youtube_transcript_api
import ConvenientFunctions as cf
import GetYoutubeData

def videoIdsFromPlaylistId(playlistId: str):
    next_page_token = None
    video_ids = []
    while 1: 
        playlist_items_response = GetYoutubeData.getVideosInPlaylist(
            youtubePlaylistId = playlistId,
            nextPageToken = next_page_token,
            maxResults = 50,
        )
        for playlist_item in playlist_items_response["items"]:
            video_ids.append(playlist_item["snippet"]["resourceId"]["videoId"])
        next_page_token = playlist_items_response.get('nextPageToken')
        if not next_page_token:
            break
    return video_ids

def captionLanguageFromVideoId(videoId: str) -> list[str]:
    languages = []
    if hasThisLanguageCaption('ja', videoId):
        languages.append('ja')
    if hasThisLanguageCaption('ko', videoId):
        languages.append('ko')

    languages.sort()
    return languages

def hasThisLanguageCaption(languageCode: str, videoId: str):
    try:
        transcriptList = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(videoId)
        for transcript in transcriptList:
            if transcript.language_code == languageCode and not transcript.is_generated:
                return True
    except:
        print('error: ' + videoId + ' has no caption')
    return False

def showVideoIdsWithCaption(videoIds: list[str]):
    videosWithoutCaption = []
    videosWithOnlyJapaneseCaption = []
    videosWithOnlyKoreanCaption = []
    videosWithBothJapaneseAndKoreanCaption = []
    for videoId in videoIds:
        print(f'{videoIds.index(videoId)} / {len(videoIds)}')
        languages = captionLanguageFromVideoId(videoId)
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
    playlistId = cf.inputText('playlistIdを入力')
    videoIds = videoIdsFromPlaylistId(playlistId)
    showVideoIdsWithCaption(videoIds)

if __name__ == '__main__':
    main()