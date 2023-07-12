
import ConvenientFunctions as cf

def deleteVideoFromFirebase(videoId: str):
    print('delete')

def main():
    flavor = cf.getFlavor

    videoIds = cf.inputText('削除したい動画のvideoId(例: ko_ja_0rtV5esQT6I)を入力(複数の場合、","で区切る)').split(',')

if __name__ == '__main__':
    main()