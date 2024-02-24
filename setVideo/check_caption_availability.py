from googleapiclient.discovery import build
import youtube_transcript_api
import convenient_functions as cf
import get_youtube_data as get_youtube_data

def video_ids_from_playlist_id(playlistId: str):
    video_ids = []
    playlist_items = get_youtube_data.get_item_response_from_playlist(playlistId)
    for i in range(len(playlist_items)):
        video_ids.append(playlist_items[i]['snippet']['resourceId']['videoId'])
    return video_ids

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
        transcript_list = youtube_transcript_api.YouTubeTranscriptApi.list_transcripts(videoId)
        for transcript in transcript_list:
            if transcript.language_code == languageCode and not transcript.is_generated:
                return True
    except:
        print('error: ' + videoId + ' has no caption')
    return False

def show_video_ids_with_caption(video_ids: list[str]):
    videos_without_caption = []
    videos_with_only_japanese_caption = []
    videos_with_only_korean_caption = []
    videos_with_both_japanese_and_korean_caption = []
    for videoId in video_ids:
        print(f'{video_ids.index(videoId)} / {len(video_ids)}')
        languages = caption_language_from_video_id(videoId)
        if not languages:
            videos_without_caption.append(videoId)
            continue
        if languages == ['ja']:
            videos_with_only_japanese_caption.append(videoId)
            continue
        if languages == ['ko']:
            videos_with_only_korean_caption.append(videoId)
            continue
        if languages == sorted(['ja', 'ko']):
            videos_with_both_japanese_and_korean_caption.append(videoId)
            continue

    print('字幕がない動画の数: ' + str(len(videos_without_caption)))
    print(','.join(videos_without_caption) + '\n')
    print('日本語字幕のみの動画の数: ' + str(len(videos_with_only_japanese_caption)))
    print(','.join(videos_with_only_japanese_caption) + '\n')
    print('韓国語字幕のみの動画の数: ' + str(len(videos_with_only_korean_caption)))
    print(','.join(videos_with_only_korean_caption) + '\n')
    print('日本語字幕と韓国語字幕の両方がある動画の数: ' + str(len(videos_with_both_japanese_and_korean_caption)))
    print(','.join(videos_with_both_japanese_and_korean_caption) + '\n')
    print('全ての動画の数: ' + str(len(video_ids)))
    print(','.join(video_ids) + '\n')

def main():
    playlist_id = cf.input_text('Playlist IDを入力')
    videoIds = video_ids_from_playlist_id(playlist_id)
    show_video_ids_with_caption(videoIds)

if __name__ == '__main__':
    main()