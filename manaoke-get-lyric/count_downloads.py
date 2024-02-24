from datetime import datetime, timedelta
from . import to_firestore as to_firestore
from . import convenient_functions as cf
import pytz

def calculate_age(birthdate: datetime):
    current_date = datetime.now()
    age = current_date.year - birthdate.year - ((current_date.month, current_date.day) < (birthdate.month, birthdate.day))
    return age

def is_monday(date: datetime) -> bool:
    return date.weekday() == 0

def show_downloads_by_age(users: dict):
    age_scale_map: dict[int] = {
        60: 0, #60歳以上
        55: 0, #55~59歳
        50: 0,
        45: 0,
        40: 0,
        35: 0,
        30: 0,
        25: 0,
        20: 0,
        15: 0,
        10: 0,
        5: 0,
        0: 0,
    }
    for user in users:
        age = calculate_age(user['birthday'])
        for age_scale in age_scale_map:
            if age >= age_scale:
                age_scale_map[age_scale] += 1
                break
    print('年齢別ダウンロード数')
    for age_scale in age_scale_map:
        print(f'{age_scale}-: {age_scale_map[age_scale]}')
    for age_scale in age_scale_map:
        print(age_scale_map[age_scale])

def weekly_downloads(year: int, month: int, day: int):
    date = datetime(year, month, day, tzinfo=pytz.timezone('Asia/Tokyo'))
    if not is_monday(date):
        print('月曜日の日付を入力してください')
        return None
    next_week_date = date + timedelta(days=7)
    users = to_firestore.fetch_ranged_users(date, next_week_date)
    show_downloads_by_age(users)
    print(f'{date.strftime("%Y%m%d")}~{next_week_date.strftime("%Y%m%d")}')
    print(f'ユーザ数: {len(users)}')

def main():
    is_weekly_count = cf.answered_yes('y = 週ごとのユーザ数を集計, n = uidから年齢')
    if is_weekly_count:
        print('どの週のユーザを集計しますか？(月曜日の日付を入力してください)')
        year = int(input('year: '))
        month = int(input('month: '))
        day = int(input('day: '))
        weekly_downloads(year, month, day)
    else:
        print('年齢を取得したいuidは？')
        uid = input('uid: ')
        birthday = to_firestore.fetch_user_birthday_by_uids(uid)
        if birthday == None:
            print('誕生日が取得できませんでした')
            return
        age = calculate_age(birthday)
        print(f'{age}歳')