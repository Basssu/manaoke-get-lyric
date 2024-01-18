import firebase_admin
from firebase_admin import firestore
from googleapiclient.discovery import build
import ConvenientFunctions as cf
import ToFireStore
import Notification

def makeFirebaseClient(flavor: str):
    creds = cf.firebaseCreds(flavor)
    domain = cf.firebaseDomain(flavor)
    firebase_admin.initialize_app(creds,{'storageBucket': f'gs://{domain}'})
    return firestore.client(), creds, domain

def videoIdLoop(flavor: str):
    while True:
        documentId = cf.inputText('ビデオのdocumentIdを入力してください(例: ko_ja_-L7eMf6Yf84)')
        setJson(documentId, flavor)
        if not cf.answeredYes(f'引き続き別の動画の承認作業を続けますか？'):
            break

def setJson(documentId: str, flavor: str):
    videoDoc = ToFireStore.fetchDocbyCollectionNameAndDocumentId('videos', documentId)
    videoDocDict = videoDoc.to_dict()
    isUncompletedVideo = videoDocDict.get('isUncompletedVideo')
    isWaitingForReview = videoDocDict.get('isWaitingForReview')
    captionSubmitterUid = videoDocDict.get('captionSubmitterUid')
    # category = videoDocDict.get('category')
    # celebrityIds = videoDocDict.get('celebrityIds')
    # playlistIds = videoDocDict.get('playlistIds')
    # title = videoDocDict.get('title')
    if isUncompletedVideo != True or isWaitingForReview != True or captionSubmitterUid == None:
        print('この動画は承認作業ができません')
        print('isUncompletedVideo: ' + str(isUncompletedVideo))
        print('isWaitingForReview: ' + str(isWaitingForReview))
        print('captionSubmitterUid: ' + str(captionSubmitterUid))
        return
    ToFireStore.afterReview(
        {
            'isUncompletedVideo': False,
            'isVerified': True,
            'isWaitingForReview': False,
        },
        documentId,
    )
    deviceTokens = Notification.uidsToDeviceTokens([captionSubmitterUid])
    Notification.sendNotificationByDeviceToken(
        deviceTokens = deviceTokens,
        title = 'あなたが送信した歌詞・字幕の承認が完了しました',
        body = 'ありがとうございます！これで他のオタクたちもこの動画を楽しめます！',
        data = {
            'route': 'reviewed_video_list_by_user',
        }
    )
    hasTranslationAfterSubtitles = videoDocDict.get('hasTranslationAfterSubtitles')
    if hasTranslationAfterSubtitles != True:
        print('翻訳後字幕がデフォルトで存在しないため、お気に入り登録している人に通知を送信しませんでした。')
        return
    Notification.sendCelebrityLikersByVideoDocs([videoDoc])
    # sendNotificationToUsers(category, celebrityIds, playlistIds, title, documentId)

# def se elebrityId})をお気に入り登録している人に通知を送信しました')
    # if category == 'music' and celebrityIds != None:
    #     for celebrity in celebrityIds:
    #         Notification.sendNotificationToCelebrityLikers(celebrity, f'「{title}」を韓国語で歌おう！' if title != None else None)
    #         print(f'アーティスト(id: {celebrity})をお気に入り登録している人に通知を送信しました')
    # if category == 'video' and playlistIds != None:
    #     for playlist in playlistIds:
    #         Notification.sendToSeriesLiker(playlist)
    #         print(f'シリーズ(id: {playlist})をお気に入り登録している人に通知を送信しました')
    
def main():
    flavor = cf.getFlavor()
    firebaseList = makeFirebaseClient(flavor)
    videoIdLoop(flavor)

if __name__ == '__main__':
    main()


