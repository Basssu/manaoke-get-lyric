# videoId = 6ZUIwj3FgUY

# run:
# 	python captionToTxt.py $(videoId)
# 	node hangulToKatakana.js $(videoId)
# 	python txtToJson.py $(videoId)

# for文を使ったルール定義
# all:
#     for videoId in $(videoIds) ; do \
#         python captionToTxt.py $(videoId)
# 		node hangulToKatakana.js $(videoId)
# 		python txtToJson.py $(videoId)
#     done

# Makefile

# videoIds配列にビデオIDを追加する
videoIds = _ZAgIHmHLdc

.PHONY: all

# allターゲットはすべてのビデオIDに対して実行する
all: $(foreach id,$(videoIds),$(id))

# 各ビデオIDに対してスクリプトを実行するルールを定義する
$(videoIds):
	python captionToTxt.py $@
	node hangulToKatakana.js $@
	python txtToJson.py $@
	python toFirebase.py $@