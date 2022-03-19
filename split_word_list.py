import os, shutil

word_list_file = 'res/CSW22.txt'
# word_list_dir = 'res/words'

# # delete existing word_list_dir
# if os.path.exists(word_list_dir):
#     shutil.rmtree(word_list_dir)

# # create new word_list_dir
# os.mkdir(word_list_dir)

word_list = {}

cur_letter = None
with open(word_list_file, 'r') as file:
    words = file.readlines()
    cur_word_list = []

    for word in words:
        word = word.strip().lower()

        if cur_letter is None:
            cur_letter = word[0]

        if word[0] != cur_letter:
            # save current set of words
            word_list[cur_letter] = cur_word_list
            cur_word_list = []
            cur_letter = word[0]
        else:
            # add to current set of words
            cur_word_list.append(word)

    if len(cur_word_list) > 0:
        word_list[cur_letter] = cur_word_list


print(len(word_list))
for key in list(word_list):
    print(len(word_list[key]))
print(list(word_list))