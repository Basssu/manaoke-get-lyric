import MeCab
import mecab_ko_dic
from konlpy.tag import Okt
from konlpy.utils import pprint
import ConvenientFunctions as cf
from typing import Optional

def captionsToJson(koreanCaptions: list[str, dict], japaneseCaptions: Optional[list[str, dict]]) -> list[dict]:
    jsonData = []
    for i in range(len(koreanCaptions)):
        jsonData.append({
            "time": convertTimeToSrtFormat(koreanCaptions[i]['start'],koreanCaptions[i]['duration']),
            "fullMeaning": japaneseCaptions[i]['text'] if japaneseCaptions != None else None,
            "detail": makeDetailList(koreanCaptions[i]['text'])
        })
    return jsonData

def makeDetailList(KoreanCaptionText: str) -> list[list]:
    # <table>
    # word    features
    # Get     SL,*,*,*,*,*,*,* ←oneWordLine
    # lost    SL,*,*,*,*,*,*,*
    # 여긴     NP+JX,*,T,여긴,Inflect,NP,JX,여기/NP/*+ᆫ/JX/*
    # 우리     NP,*,F,우리,*,*,*,*
    # 구역     NNG,*,T,구역,*,*,*,*
    # get     SL,*,*,*,*,*,*,*
    # outta   SL,*,*,*,*,*,*,*
    # here    SL,*,*,*,*,*,*,*
    # EOS
    tagger = MeCab.Tagger(mecab_ko_dic.MECAB_ARGS)
    table = tagger.parse(KoreanCaptionText)
    analysisList = []
    for oneWordLine in table.split("\n"):
        word = oneWordLine.split("\t")[0]
        if word == ' ' or word == u'\xa0':
            continue
        if word == "EOS":
            break
        features = oneWordLine.split("\t")[1].split(",")
        analysisList.append(wordAnalysis(word, features))
    
    KoreanCaptionTextDivided = KoreanCaptionText.strip().split()
    detail = []
    for j in range(len(KoreanCaptionTextDivided)):
        analysis = []
        for k in range(len(analysisList)):
            if analysisList[k][0] in KoreanCaptionTextDivided[j]:
                analysis.append(analysisList[k])
        detail.append({'actualLyric': KoreanCaptionTextDivided[j], 'analysis': analysis})
    return detail

def wordAnalysis(word: str, features: list[str]) -> list:
    okt = Okt()
    return [
        word,
        {
            "pos": features[0],
            "start_pos": features[5],
            "end_pos": features[6],
            "expression": features[7] if len(features) > 7 else None,
            "stem": okt.pos(word, norm=False, stem=True)[0][0],
            "stem_pos": okt.pos(word, norm=False, stem=True)[0][1]
        }]

def convertTimeToSrtFormat(start: float, duration: float) -> str:
    end = start + duration
    time = f'{cf.formatTime(start)} --> {cf.formatTime(end)}'
    return time