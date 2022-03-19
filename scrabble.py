import re
import numpy as np
from itertools import permutations, combinations
from time import perf_counter

BOARD_FILE = 'res/small_board.txt'
REF_BOARD_FILE = 'res/small_ref_board.txt'
SDICT_FILE = 'res/CSW22.txt'
SDICT = None
BOARD = None
REF_BOARD = None


def main():
    # TODO: handle vertical words: literally just rotate the board 90 deg. CCW and run again
    #       use numpy arrays to hopefully gain some performance
    #       (will also make rotating a lot easier, there's a function for that)
    #
    #       account for limited number of tiles - don't have as many as we want
    #
    #       make sure multiple blank tiles in one word can be handled
    global SDICT, BOARD, REF_BOARD

    start_run_time = perf_counter()

    # use '*' for blank tile
    letters_in_hand = list('tes*')
    min_word_sz = 1
    max_word_sz = 7 # should be <= len(BOARD[0]) (row length)

    bingo_size = 7
    bingo_bonus = 50

    # load Scrabble dictionary
    load_dictionary(SDICT_FILE)
    if SDICT is None:
        print('Scrabble dictionary failed to load: exiting')
        return

    # load board
    BOARD = read_board_from_file(BOARD_FILE)
    if BOARD is None:
        print('board failed to load: exiting')
        return

    # load reference board
    REF_BOARD = read_board_from_file(REF_BOARD_FILE)
    if REF_BOARD is None:
        print('ref_board failed to load: exiting')
        return

    # remove bonuses from REF_BOARD if a word is already played there
    for row in range(len(BOARD)):
        for col in range(len(BOARD[0])):
            if BOARD[row][col] != ' ':
                REF_BOARD[row][col] = '.'
                print(f'replacing {REF_BOARD[row][col]} with "." - {BOARD[row][col]} at {[row,col]}')

    
    # generate a list of all valid horizontal spaces on the board
    spaces = generate_spaces_h(letters_in_hand, min_word_sz, max_word_sz, len(letters_in_hand))
    #[print(s) for s in spaces]
    #print()

    # fill each horizontal space with a list of valid Scrabble words we can play with out letters
    filled_spaces = fill_all_spaces(min_word_sz, letters_in_hand, spaces)

    # make sure horizontal words are also valid in any vertical words created
    # TODO: filter out spaces with 'valid_words_final' == {}
    for space in filled_spaces:
        space['valid_words_final'] = check_valid_words_in_v_spaces(space)

    # calculate highest scoring horizontal word in each space
    filled_spaces = find_highest_scoring_word_in_each_space(filled_spaces)
    #print_spaces_line_by_line(filled_spaces)



    # print high scoring space(s)
    
    high_scoring_spaces = []
    for space in filled_spaces:
        if space['num_blank'] == bingo_size and space['valid_words_final'] != {}:
            space['high_score'] = space['high_score'] + bingo_bonus
            
        if len(high_scoring_spaces) > 0:
            if space['high_score'] > high_scoring_spaces[0]['high_score']:
                high_scoring_spaces = [space]
            elif space['high_score'] == high_scoring_spaces[0]['high_score']:
                high_scoring_spaces.append(space)
        else:
            high_scoring_spaces.append(space)
    

    print()
    print('-------- high scoring space(s) --------')
    print()

    if len(high_scoring_spaces) < 1:
        print('no high scoring space found')
    else:
        print_spaces_line_by_line(high_scoring_spaces)


    print()
    print(f'total run time: {perf_counter() - start_run_time}')
    print()


# takes in a 'space', returns a list of the 'valid_words' of 'space' that also make valid
#   words in each 'v_space'
def check_valid_words_in_v_spaces(space):
    # don't need to check v_space if there are none
    if len(space['v_spaces']) < 1:
        return dict.fromkeys(space['valid_words'])

    valid_words_final = {}
    for h_word_to_try in space['valid_words']:
        valid_words_v = []
        v_spaces = space['v_spaces']

        # 'v_space' start column - 'space' start col. gives index of letter in 'word_to_try'
        #   that is at the intersection of both spaces
        # (doesn't account for '*' character, remove that temporarily for math)
        blank_index = None
        if h_word_to_try.count('*') > 0:
            blank_index = h_word_to_try.index('*')

        h_word_to_try_temp = h_word_to_try.replace('*', '')

        for v_space in v_spaces:
            # put 'valid_word' in each 'v_space'
            # if invalid for any 'v_space', then 'valid_word' is invalid for 'space'

            index = abs(v_space['start'][1] - space['start'][1])
            letter_to_put_in_v_blank = h_word_to_try_temp[index]
            v_blank_index = v_space['ltrs'].index(' ')

            v_word_to_try = ''.join(v_space['ltrs']).replace(' ', letter_to_put_in_v_blank)
            if is_valid_word(v_word_to_try):
                if blank_index == index + 1:
                    # TODO: check for multiple blank tiles
                    # need to add back '*' blank tile indicator
                    v_word_to_try = list(v_word_to_try)

                    if v_blank_index + 1 == len(v_word_to_try):
                        v_word_to_try.append('*')
                    else:
                        v_word_to_try.insert(v_blank_index+1, '*')

                    v_word_to_try = ''.join(v_word_to_try)

                valid_words_v.append(v_word_to_try)

        if len(valid_words_v) == len(v_spaces):
            valid_words_final[h_word_to_try] = valid_words_v

    return valid_words_final



# takes in a list of spaces, return a new list of spaces, each with the highest scoring
#   word added
def find_highest_scoring_word_in_each_space(spaces):
    global REF_BOARD

    new_spaces = []

    for space in spaces:
        high_score = 0
        high_scoring_word = ''
        high_scoring_words = []
        valid_words_final = space['valid_words_final']

        # grab the section of the reference board corresponding to 'space'
        start_row = space['start'][0]
        start_col = space['start'][1]
        ref_board_space = REF_BOARD[start_row][start_col:start_col+space['size']]

        point_vals = {}

        for valid_word_h in list(valid_words_final.keys()):
            # score the horizontal word, using ref_board_space to find letter/word bonuses
            points = calculate_points(valid_word_h, ref_board_space)
            point_val_list = {valid_word_h: points}

            # don't need to score v_words if there are none
            if valid_words_final[valid_word_h] is not None:
                # score each vertical word made from horizontal word
                cur_v_space_index = 0
                for valid_word_v in valid_words_final[valid_word_h]:
                    cur_v_space = space['v_spaces'][cur_v_space_index]
                    v_start_row = cur_v_space['start'][0]
                    v_start_col = cur_v_space['start'][1]
                    v_ref_board_space = [REF_BOARD[v_start_row+i][v_start_col] for i in range(cur_v_space['size'])]
                    cur_v_space_index += 1

                    point_res = calculate_points(valid_word_v, v_ref_board_space)

                    points += point_res
                    point_val_list[valid_word_v] = point_res

            point_vals[valid_word_h] = point_val_list

            if points >= high_score:
                if points == high_score:
                    high_scoring_words.append(valid_word_h)
                else:
                    high_score = points
                    high_scoring_word = valid_word_h
                    high_scoring_words = [high_scoring_word]


        space['ref_board_space'] = ref_board_space
        space['high_scoring_word'] = high_scoring_words
        space['high_score'] = high_score
        space['point_vals'] = point_vals
        new_spaces.append(space)

    return new_spaces


# takes in a string of letters, returns the number of scrabble points these letters add up to
# '*' counts as a blank tile and is worth 0 points
def calculate_points(letters, ref_board_space):
    rev_word_letters = letters[::-1]
    rev_ref_space = ref_board_space[::-1]

    # don't count points for blank tiles, they're worth nothing
    # reverse the word then add up points - that way if a '*' is detected just skip next letter
    # ('*' always comes directly after a letter)
    points = 0
    word_bonus = 0
    skip_next = False
    for c in range(len(rev_word_letters)):
        if rev_word_letters[c] == '*':
            # skip next iteration if it's a blank space, counts for 0 points
            # still need to check for word bonuses, however
            rev_ref_space.insert(c, '*')
            if rev_ref_space[c+1] == 'T':
                word_bonus += 2
            elif rev_ref_space[c+1] == 'D':
                word_bonus += 1
            skip_next = True
        else:
            if not skip_next:
                letter_points = get_point_value(rev_word_letters[c])

                # check for bonuses
                ref_letter = rev_ref_space[c]
                if ref_letter == 'T':
                    word_bonus += 2
                elif ref_letter == 'D':
                    word_bonus += 1
                elif ref_letter == 't':
                    letter_points *= 3
                elif ref_letter == 'd':
                    letter_points *= 2

                points += letter_points
            else:
                skip_next = False

    points += points * word_bonus

    return points

# takes in a list of board spaces and returns a list of spaces, each with a new entry containing all
#   valid Scrabble words that can be played in the space
#
# returns:
# [ {'start': [0,0], 'size': 2, 'num_blank': 1, 'valid_words': ['as', 'is'], ... },
#   { ... },
#   { ... } ]
def fill_all_spaces(min_word_sz, letters_in_hand, spaces):
    global BOARD

    filled_spaces = []

    # pre-load all permutations of 'letters_in_hand'
    perms = {}
    for sz in range(1, len(letters_in_hand)+1):
        perms[sz] = permute_letters(letters_in_hand, sz)
    letter_list = np.array(list(perms.values()))

    total_spaces = len(spaces)
    cur_space = 1
    for space in spaces:
        print(f"filling space #: {cur_space} / {total_spaces}  (size {space['size']})")
        cur_space += 1

        num_blank = space['num_blank']
        words = fill_space(space, letter_list[num_blank-1])#perms[num_blank])

        if words is not None and len(words) > 0:
            # add new 'valid_words' entry to 'space'
            space['valid_words'] = list(words)
            filled_spaces.append(space)

    return filled_spaces


# fills a given section of the board with all permutations of 'letters'
# returns a list containing all such permutations that are also valid Scrabble words
# 'space' can be blank or contain existing characters
# returns None if number of blank spaces in 'space' is not equal to number of letters
def fill_space(space, letter_list):
    filled = []
    filled_a = np.array([], dtype='str')

    start_time = perf_counter()

    # fill 'space' with 'letter_list'
    # return a list of these filled spaces that are valid Scrabble words
    for letters_to_try in letter_list:

        # horizontal word is good
        word = letters_valid_in_space(letters_to_try, space)
        if word is not None:
            #filled.append(word)
            filled_a = np.append(filled_a, word)

    print(f'for loop took: {perf_counter()-start_time} for {len(letter_list)} iterations')

    return filled_a #filled


# returns the word formed by putting 'letters' in 'space' if it's valid, otherwise None
def letters_valid_in_space(letters, space):
    BLANK_SPACE_CHAR = ' '
    new_space = []
    space_ltrs = space['ltrs']

    ltr_index = 0
    for ltr in space_ltrs:
        if ltr == BLANK_SPACE_CHAR:
            new_space += letters[ltr_index]
            ltr_index += 1
        else:
            new_space += ltr

    word = ''.join(new_space)

    # temporarily remove '*' blank space indicator for word validation
    if word.count('*') > 0:
        temp = word.replace('*', '')
    else:
        temp = word

    if (is_valid_word(temp)):
        return word
    else:
        return None


# most of this is redundant with the parts of generate_spaces_h() that detect
#   if the space is touching a letter vertically
def get_v_spaces(space, v_word_start_list):
    global BOARD

    v_spaces = []
    row = space['start'][0]

    for v_start_col in v_word_start_list:

        # get starting row of vertical word (looking "up")
        v_start_row = row
        done = False

        while not done:
            if v_start_row > 0:
                v_start_row -= 1
                cur_ltr = BOARD[v_start_row][v_start_col]
                if cur_ltr == ' ':
                    done = True
                    v_start_row += 1
            else:
                done = True

        # get ending row of vertical word (looking "down")
        v_end_row = row
        done = False

        while not done:
            if v_end_row < len(BOARD)-1:
                v_end_row += 1
                cur_ltr = BOARD[v_end_row][v_start_col]
                if cur_ltr == ' ':
                    done = True
                    v_end_row -= 1
            else:
                done = True


        v_size = v_end_row - v_start_row + 1# v_end_row - v_start_row
        v_space = {
            'start': [v_start_row, v_start_col],
            'size': v_size,
            'ltrs': [BOARD[i][v_start_col] for i in range(v_start_row, v_end_row+1)]
        }
        v_spaces.append(v_space)

    return v_spaces

# generate a List of spaces on the board where a word can be played

# must be horizontal or vertical
# must be touching at least one existing letter
#
# returns:
# {
#     row 0: [ {'start': [0,0], 'size': 2, 'num_blank': 1}, { ... } ]
#     row 1: [ { ... }, ... ]
#     ...
# }
def generate_spaces_h(letters_in_hand, min_word_sz, max_word_sz, max_blanks):
    global BOARD

    spaces = []

    # loop through every row in the board
    for r in range(0, len(BOARD)):
        row = BOARD[r]
        
        # loop through all possible word sizes
        for size in range(min_word_sz, max_word_sz+1): #len(row)+1):
            max_index = (len(row) - size) + 1
            if max_index < 0 or max_index > len(row):
                print(f'min_word_sz: {min_word_sz}')
                print(f'max_index: {max_index}')
                print(f'size: {size}')
                print(f'max_word_sz: {max_word_sz} - probably bigger than row length')
                return None

            # find all valid spaces of length 'size' in 'row'
            for c in range(0, max_index):
                space = row[c:c+size]
                num_blank = space.count(' ')

                # not valid if there are more blank spaces than 'max_blanks'
                # or if there are no blank spaces at all
                if num_blank > max_blanks or num_blank < 1:
                    continue


                # if there is an existing letter above one of the blank spots
                #   in the space, record its coordinates
                # that also means the space is valid even if it's empty
                v_word_start_list = []

                # above
                if r > 0: # bounds check
                    # now loop through the slots
                    for i in range(0, len(space)):
                        above = BOARD[r-1][c+i]
                        if above != ' ' and BOARD[r][c+i] == ' ':
                            v_word_start_list.append(c + i)
                # below
                if r < len(BOARD)-1: # bounds check
                    # now loop through the slots
                    for i in range(0, len(space)):
                        below = BOARD[r+1][c+i]
                        if below != ' ' and BOARD[r][c+i] == ' ':
                            if c + i not in v_word_start_list:  # accounts for already found above
                                v_word_start_list.append(c + i)

                
                if num_blank != len(space) or len(v_word_start_list) > 0:
                    # make sure there's not a letter to the left or right of 'space'
                    # (that particular space will be accounted for later)

                    # left
                    if c > 0: # bounds check
                        if row[c-1] != ' ':
                            continue
                    # right
                    if c + size < len(row): # bounds check
                        if row[c+size] != ' ':
                            continue

                    new_space = {
                            'start': [r,c],
                            'size': size,
                            'num_blank': num_blank,
                            'ltrs': space,
                    }
                    new_space['v_spaces'] = get_v_spaces(new_space, v_word_start_list)

                    spaces.append(new_space)


    return spaces


# returns a list of all permutations of 'letters' of size 'size'

# [ ('a', 'b', 'c'), ('a', 'c', 'b'), ... ]
def permute_letters(letters, size):
    if letters.count('*') > 0:
        # handle blank tile(s)
        # replace '*' with every letter a-z, find all perms
        perms = []
        for c in range(97, 123): # 'a' to 'z'
            # keeping the '*' so we know which letter is a blank tile for scoring purposes
            new_letters = [l.replace('*',f'{chr(c)}*') for l in letters]
            for p in list(permutations(new_letters, size)):
                perms.append(p)

        # stupid - remove duplicates
        perms = list(dict.fromkeys(perms))
        return perms

    else:
        return list(permutations(letters, size))


# returns 'True' if 'word' is a valid Scrabble word
def is_valid_word(word):
    global SDICT

    return word.lower() in SDICT


def load_dictionary(file):
    global SDICT

    with open(file, 'r') as file:
        words = file.readlines()
        SDICT = [word.strip().lower() for word in words]


def print_spaces_line_by_line(spaces):
    for space in spaces:
        print('{')
        for key in list(space.keys()):
            if key == 'high_scoring_word':
                print()
            print(f'\t{key}: {space[key]}')
        print('}\n')


# takes in a string with 1 or 2 characters
# letter = [a-z]\*?
# returns the point value of letter, or 0 if letter contains * (blank tile)
def get_point_value(letter):
    #if letter.count('*') > 0:
    #    return 0

    points = {
        'a':1, 'e':1, 'i':1, 'o':1, 'u':1, 'l':1, 'n':1, 's':1, 't':1, 'r':1,
        'd':2, 'g':2,
        'b':3, 'c':3, 'm':3, 'p':3,
        'f':4, 'h':4, 'v':4, 'w':4, 'y':4,
        'k':5,
        'j':8, 'x':8,
        'q':10, 'z':10
    }
    return points[letter]


# returns:
#
# [ ['r', 'o', 'w', '0'],
#   ['r', 'o', 'w', '1'],
#   ['r', 'o', 'w', '2'],
#   [       ...        ] ]
def read_board_from_file(board_file):
    with open(board_file) as file:
        rows = [row.strip().replace('.', ' ') for row in file.readlines()]
        for r in range(len(rows)):
            rows[r] = [space for space in rows[r]]
        return rows


if __name__ == '__main__':
    main()