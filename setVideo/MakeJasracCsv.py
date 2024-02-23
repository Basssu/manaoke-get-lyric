import csv
import ToFireStore
from datetime import datetime
import os

def main():
    videoDocList = ToFireStore.fetch_jasrac_code_list()
    current_time = datetime.now()
    
    directory = 'csv'
    if not os.path.exists(directory):
        os.makedirs(directory)

    formatted_time = current_time.strftime("%Y%m%d%H%M%S")
    csv_filename = f"csv/videos_with_jasracCode_{formatted_time}.txt"
    with open(csv_filename, "w", newline="", encoding='shift_jis') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter='\t')
        jasracCodeList = []
        recordsCount = 0
        for doc in videoDocList:
            data = doc.to_dict()
            if jasracCodeList.count(data.get("jasracCode")) > 0 or data.get("jasracCode") == None:
                continue
            jasracCodeList.append(data.get("jasracCode"))
            recordsCount += 1
            title = data.get("title")
            if not is_shift_jis_encodable(title):
                title = '変換不可'
            csv_writer.writerow([
                data.get("jasracCode").replace("-",""), #インターフェイスキーコード
                "", #コンテンツ区分
                "000", #コンテンツ枝番
                "", #メドレー区分
                "0", #メドレー枝番
                "", #コレクトコード
                data.get("jasracCode").replace("-",""), #ＪＡＳＲＡＣ作品コード
                title, #原題名
                "", #副題・邦題
                "未取得", #作詞者名
                "", #補作詞・訳詞者名
                "", #作曲者名
                "", #編曲者名
                "", #アーティスト名
                "0", #情報料（税抜）
                "T", #ＩＶＴ区分
                "3", #原詞訳詞区分
                "", #IL区分
                "0", #リクエスト回数
                ])
    print("報告レコード数")
    print(recordsCount)
    
def is_shift_jis_encodable(text):
    try:
        text.encode('shift_jis')
        return True
    except UnicodeEncodeError:
        return False
    
if __name__ == '__main__':
    main()