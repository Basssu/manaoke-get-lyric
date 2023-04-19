korea = [{'duration': 5.429,
  'start': 5.348,
  'text': '[구찌와 함께하는 이곳은 하니의 마리끌레르 화보 촬영 현장]'},
 {'duration': 2.202, 'start': 13.38, 'text': '[♥하니 등장♥]'},
 {'duration': 1.426, 'start': 15.591, 'text': '안녕하세요~\n[첫 번째 착장 촬영 준비를 마친 하니]'},
 {'duration': 1.066, 'start': 17.026, 'text': '안녕하세요'},
 {'duration': 1.385, 'start': 18.101, 'text': '-이쪽으로...\n-네'}]
このような配列と

japan = [{'duration': 1.302, 'start': 4.037, 'text': '[HANNI GUCCI LOOK(1)]'},
 {'duration': 5.429,
  'start': 5.348,
  'text': '[GUCCIと共に行うHANNIの\n『marie claire』雑誌撮影の現場]'},
 {'duration': 2.202, 'start': 13.38, 'text': '[♥HANNI登場♥]'},
 {'duration': 1.426,
  'start': 15.591,
  'text': 'こんにちは～\n[1着目の衣装を着て\n撮影準備を終えたHANNI]'},
 {'duration': 1.066, 'start': 17.026, 'text': 'こんにちは'},
 {'duration': 1.385, 'start': 18.101, 'text': '- こちらへ…\n- はい'},
 {'duration': 1.559, 'start': 19.495, 'text': 'おお GUCCIの枕'},
 ]
このような配列がある

このとき、両方の配列を見て、配列内辞書型のキー"duration"と"start"の値が両方ともお互いに一致する要素があった場合のみ、配列に残すように処理したい。
例えば上記の場合は処理をした後

korea = [{'duration': 5.429,
  'start': 5.348,
  'text': '[구찌와 함께하는 이곳은 하니의 마리끌레르 화보 촬영 현장]'},
 {'duration': 2.202, 'start': 13.38, 'text': '[♥하니 등장♥]'},
 {'duration': 1.426, 'start': 15.591, 'text': '안녕하세요~\n[첫 번째 착장 촬영 준비를 마친 하니]'},
 {'duration': 1.066, 'start': 17.026, 'text': '안녕하세요'},
 {'duration': 1.385, 'start': 18.101, 'text': '-이쪽으로...\n-네'}]

japan = [
 {'duration': 5.429,
  'start': 5.348,
  'text': '[GUCCIと共に行うHANNIの\n『marie claire』雑誌撮影の現場]'},
 {'duration': 2.202, 'start': 13.38, 'text': '[♥HANNI登場♥]'},
 {'duration': 1.426,
  'start': 15.591,
  'text': 'こんにちは～\n[1着目の衣装を着て\n撮影準備を終えたHANNI]'},
 {'duration': 1.066, 'start': 17.026, 'text': 'こんにちは'},
 {'duration': 1.385, 'start': 18.101, 'text': '- こちらへ…\n- はい'},
 ]
このようになる。なぜなら、最初に示したjapan配列の1つ目の要素
{'duration': 1.302, 'start': 4.037, 'text': '[HANNI GUCCI LOOK(1)]'}
の"duration"の1.302と、"start"の4.037を持つ辞書型がkorea配列にはなかったからだ。

これを実現するコードを書け