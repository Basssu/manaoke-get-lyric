import csv
from . import convenient_functions as cf
from . import to_firestore
from . import notification

def extract_values_from_csv(file_path):
    values = []
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            if 'app_user_id' in row:
                values.append(row['app_user_id'])
    return values[1:] 

def main():
    revenue_cat_csv_path = input('revenueCatのCSVファイルのパスを入力してください(絶対パス): ')
    app_user_ids = extract_values_from_csv(revenue_cat_csv_path)
    if not app_user_ids:
        print('app_user_idが見つかりませんでした。')
        return
    print('app_user_idの数: ' + str(len(app_user_ids)))
    print('app_user_id[0]: ' + app_user_ids[0])
    if len(app_user_ids) > 1:
        print('app_user_id[1]: ' + app_user_ids[1])
        
    user_count = to_firestore.fetch_user_count()
    print('Firestoreのユーザ数: ' + str(user_count))
    if not cf.answered_yes('続行し、Firestoreの全ユーザのIDを取得しますか？'):
        return
    
    user_ids = to_firestore.fetch_all_user_ids()
    print('取得したユーザ数: ' + str(len(user_ids)))
    user_ids = list(filter(lambda x: x not in app_user_ids, user_ids))
    print('送信先のユーザ数: ' + str(len(user_ids)))
    
    title = input('通知タイトルを入力してください: ')
    body = input('通知本文を入力してください: ')
    
    if not cf.answered_yes('この通知を送信しますか？'):
        return
    
    device_tokens = notification.uids_to_device_tokens(user_ids)
    notification.send_notification_by_device_token(device_tokens, title, body, {'route': 'independent_purchase'})
    
    
    
    
    
    