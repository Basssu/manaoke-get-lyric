import csv
import ConvenientFunctions as cf
import ToFireStore
from datetime import datetime
import os

def main():
    videoDocList = ToFireStore.fetchJasracCodeList()
    current_time = datetime.now()
    
    directory = 'csv'
    if not os.path.exists(directory):
        os.makedirs(directory)

    formatted_time = current_time.strftime("%Y%m%d%H%M%S")
    csv_filename = f"csv/videos_with_jasracCode_{formatted_time}.txt"
    with open(csv_filename, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile, delimiter='\t')
        # csv_writer.writerow([
        #     "インターフェイスキーコード", 
        #     "コンテンツ区分", 
        #     "コンテンツ枝番", 
        #     "メドレー区分", 
        #     "メドレー枝番", 
        #     "コレクトコード", 
        #     "ＪＡＳＲＡＣ作品コード", 
        #     "原題名", 
        #     "副題・邦題", 
        #     "作詞者名", 
        #     "補作詞・訳詞者名", 
        #     "作曲者名", 
        #     "編曲者名", 
        #     "アーティスト名", 
        #     "情報料（税抜）", 
        #     "ＩＶＴ区分", 
        #     "原詞訳詞区分", 
        #     "IL区分", 
        #     "リクエスト回数"
        #     ])
        jasracCodeList = []
        recordsCount = 0
        for doc in videoDocList:
            data = doc.to_dict()
            if jasracCodeList.count(data.get("jasracCode")) > 0 or data.get("jasracCode") == None:
                continue
            jasracCodeList.append(data.get("jasracCode"))
            recordsCount += 1
            csv_writer.writerow([
                data.get("jasracCode").replace("-",""), #インターフェイスキーコード
                "", #コンテンツ区分
                "000", #コンテンツ枝番
                "", #メドレー区分
                "0", #メドレー枝番
                "", #コレクトコード
                data.get("jasracCode").replace("-",""), #ＪＡＳＲＡＣ作品コード
                data.get("title"), #原題名
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
    
if __name__ == '__main__':
    main()