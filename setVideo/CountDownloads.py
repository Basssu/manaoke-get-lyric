from datetime import datetime, timedelta
from typing import Optional
import ToFireStore
import ConvenientFunctions as cf
import pytz

def calculateAge(birthdate: datetime):
    current_date = datetime.now()
    age = current_date.year - birthdate.year - ((current_date.month, current_date.day) < (birthdate.month, birthdate.day))
    return age

def isMonday(date: datetime) -> bool:
    return date.weekday() == 0

def showDownloadsByAge(users: dict):
    ageScaleMap: dict[int] = {
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
        age = calculateAge(user['birthday'])
        for ageScale in ageScaleMap:
            if age >= ageScale:
                ageScaleMap[ageScale] += 1
                break
    print('年齢別ダウンロード数')
    for ageScale in ageScaleMap:
        print(f'{ageScale}-: {ageScaleMap[ageScale]}')
    for ageScale in ageScaleMap:
        print(ageScaleMap[ageScale])

def weeklyDownloads(year: int, month: int, day: int):
    date = datetime(year, month, day, tzinfo=pytz.timezone('Asia/Tokyo'))
    if not isMonday(date):
        print('月曜日の日付を入力してください')
        return None
    nextWeekDate = date + timedelta(days=7)
    users = ToFireStore.fetchRangedUsers(date, nextWeekDate)
    showDownloadsByAge(users)
    print(f'{date.strftime("%Y%m%d")}~{nextWeekDate.strftime("%Y%m%d")}')
    print(f'ユーザ数: {len(users)}')

def main():
    isWeeklyCount = cf.answeredYes('y = 週ごとのユーザ数を集計, n = uidから年齢')
    if isWeeklyCount:
        print('どの週のユーザを集計しますか？(月曜日の日付を入力してください)')
        year = int(input('year: '))
        month = int(input('month: '))
        day = int(input('day: '))
        weeklyDownloads(year, month, day)
    else:
        print('年齢を取得したいuidは？')
        uid = input('uid: ')
        birthday = ToFireStore.fetchUserBirthdayByUids(uid)
        if birthday == None:
            print('誕生日が取得できませんでした')
            return
        age = calculateAge(birthday)
        print(f'{age}歳')

if __name__ == '__main__':
    main()