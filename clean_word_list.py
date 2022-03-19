word_list = 'scrabble_words.txt'
out_file = 'scrabble_words_clean.txt'

ltr_counts = {
    'a': 9,
    'b': 2,
    'c': 2,
    'd': 4,
    'e': 12,
    'f': 2,
    'g': 3,
    'h': 2,
    'i': 9,
    'j': 1,
    'k': 1,
    'l': 4,
    'm': 2,
    'n': 6,
    'o': 8,
    'p': 2,
    'q': 1,
    'r': 6,
    's': 4,
    't': 6,
    'u': 4,
    'v': 2,
    'w': 2,
    'x': 1,
    'y': 2,
    'z': 1
}

with open(word_list) as file_in:
    with open(out_file, 'a') as file_out:
        bad = False

        for word in file_in.readlines():

            word = word.strip().lower()

            if len(word) > 15:
                bad = True

            if not bad:
                for ltr in ltr_counts:
                    if word.count(ltr) > ltr_counts[ltr]:
                        bad = True
                        break
            if bad:
                print('bad word: ' + word)
                bad = False
            else:
                file_out.write(word+'\n')