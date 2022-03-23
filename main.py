import sys
import telebot
from telebot import types
from random import randrange
from collections import Counter
import config
TOKEN = config.TOKEN

bot = telebot.TeleBot(TOKEN)

grid = [['#'] * 3 for _ in range(3)]
user_char = None
computer_char = None
maps = None
checker = None
level = 0
USER_TURN = False
AI_TURN = True

EMPTY_CHAR = '#'
scores = {
    user_char: -100,
    computer_char: 100,
    'draw': 0
}


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Type command /level')


@bot.message_handler(commands=['level'])
def level(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    easy = types.KeyboardButton('Easy')
    hard = types.KeyboardButton('Hard')
    markup.add(easy, hard)
    bot.send_message(message.chat.id, 'Choose level and type command /dice', reply_markup=markup)


@bot.message_handler(func=lambda x: x.text == 'Easy' or x.text == 'Hard')
def handle_level(message):
    global level
    if message.text == 'Easy':
        level = 0
    else:
        level = 1
    bot.delete_message(message.chat.id, message.id)


@bot.message_handler(commands=['dice'])
def preparation(message):
    sent = bot.send_message(message.chat.id, 'Guess one number from 1 to 6')
    bot.register_next_step_handler(sent, dice)


def dice(message):
    global user_char, computer_char, grid, scores
    bot_number = randrange(1, 6)
    user_num = int(message.text)
    while int(message.text) == bot_number:
        bot_number = randrange(1, 6)
    bot_num = bot_number
    bot.send_message(message.chat.id,
                     f"Bot guessed number {bot_number}. Whose guess will turn out correct or close to answer will "
                     f"begin first "
                     )
    sent = bot.send_dice(message.chat.id, '🎲')
    markup = types.ReplyKeyboardMarkup()
    start_btn = types.KeyboardButton("Start the game!")
    markup.add(start_btn)
    if abs(bot_num - sent.dice.value) < abs(user_num - sent.dice.value):
        bot.send_message(message.chat.id, 'Bot begins first', reply_markup=markup)
        user_char = 'O'
        computer_char = 'X'
    else:
        bot.send_message(message.chat.id, 'You begin first!', reply_markup=markup)
        user_char = 'X'
        computer_char = 'O'
    grid = [['#'] * 3 for _ in range(3)]
    scores = {
        user_char: -100,
        computer_char: 100,
        'draw': 0
    }


@bot.message_handler(func=lambda x: x.text == "Start the game!" or (x.text[0] == '(' and x.text[-1] == ')'))
def play_game(message):
    global user_char, grid, maps, level
    if message.text == "Start the game!":
        if user_char == 'X':
            maps = bot.send_message(message.chat.id, array_to_string(grid))
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            buttons = []
            for i in range(len(grid)):
                for j in range(len(grid[0])):
                    btn = types.KeyboardButton(f"({i},{j})")
                    buttons.append(btn)
            markup.add(*buttons)
            bot.send_message(message.chat.id, "Choose position of your object", reply_markup=markup)
        else:
            bot_move(level)
            maps = bot.send_message(message.chat.id, array_to_string(grid))
            buttons = []
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            for i in range(len(grid)):
                for j in range(len(grid[0])):
                    btn = types.KeyboardButton(f"({i},{j})")
                    buttons.append(btn)
            markup.add(*buttons)
            bot.send_message(message.chat.id, "Choose position of your object", reply_markup=markup)
    else:
        user_move(message)
        if check_win(message, grid):
            bot.delete_message(chat_id=message.chat.id, message_id=message.id)
            bot.edit_message_text(text=array_to_string(grid), chat_id=maps.chat.id, message_id=maps.id)
            return
        bot.delete_message(chat_id=message.chat.id, message_id=message.id)
        bot_move(level)
        bot.edit_message_text(text=array_to_string(grid), chat_id=maps.chat.id, message_id=maps.id)
        if check_win(message, grid):
            return


def user_move(message):
    global grid, user_char
    x, y = map(int, message.text[1:-1].split(','))
    if grid[x][y] == '#':
        grid[x][y] = user_char


def bot_move(level):
    global grid, computer_char, user_char
    if level == 0:
        x, y = randrange(0, 3), randrange(0, 3)
        while grid[x][y] == user_char or grid[x][y] == computer_char:
            x, y = randrange(0, 3), randrange(0, 3)
        grid[x][y] = computer_char
    else:
        move = None
        best_score = -sys.maxsize
        board = [grid[y].copy() for y in range(3)]
        for y in range(3):
            for x in range(3):
                if board[y][x] == EMPTY_CHAR:
                    board[y][x] = computer_char
                    score = minimax(board, 0, USER_TURN)
                    board[y][x] = EMPTY_CHAR
                    if score > best_score:
                        best_score = score
                        move = (x, y)

        grid[move[1]][move[0]] = computer_char


def minimax(board, depth, is_ai_turn):
    global computer_char, user_char, scores, EMPTY_CHAR, USER_TURN, AI_TURN
    if is_win(computer_char, board):
        return scores[computer_char]
    if is_win(user_char, board):
        return scores[user_char]
    if is_draw(board):
        return scores['draw']

    if is_ai_turn:
        best_score = - sys.maxsize
        for y in range(3):
            for x in range(3):
                if board[y][x] == EMPTY_CHAR:
                    board[y][x] = computer_char
                    score = minimax(board, depth + 1, USER_TURN)
                    board[y][x] = EMPTY_CHAR
                    best_score = max(best_score, score)
    else:
        best_score = sys.maxsize
        for y in range(3):
            for x in range(3):
                if board[y][x] == EMPTY_CHAR:
                    board[y][x] = user_char
                    score = minimax(board, depth + 1, AI_TURN)
                    board[y][x] = EMPTY_CHAR
                    best_score = min(best_score, score)
    return best_score


def get_opponent_char(char):
    return 'O' if char == 'X' else 'X'


def is_win(char, field):
    global EMPTY_CHAR
    opponent_char = get_opponent_char(char)
    for y in range(3):
        if opponent_char not in field[y] and EMPTY_CHAR not in field[y]:
            return True
    for x in range(3):
        col = [field[0][x], field[1][x], field[2][x]]
        if opponent_char not in col and EMPTY_CHAR not in col:
            return True

    diagonal = [field[0][0], field[1][1], field[2][2]]
    if opponent_char not in diagonal and EMPTY_CHAR not in diagonal:
        return True
    diagonal = [field[0][2], field[1][1], field[2][0]]
    if opponent_char not in diagonal and EMPTY_CHAR not in diagonal:
        return True

    return False


def is_draw(field):
    global EMPTY_CHAR
    count = 0
    for y in range(3):
        count += 1 if EMPTY_CHAR in field[y] else 0
    return count == 0


def array_to_string(grid):
    ans = ''
    for i in range(len(grid)):
        ans += ' '.join(grid[i])
        ans += '\n'

    return ans


def check_win(message, grid):
    global user_char, computer_char
    markup = types.ReplyKeyboardMarkup()

    for i in range(len(grid)):
        line = Counter(grid[i])
        if 'X' in line and 'O' in line:
            continue
        if user_char in line and line[user_char] == 3:
            if message:
                bot.send_message(message.chat.id, "You are winner!", reply_markup=markup)
            user_char = None
            computer_char = None
            return True
        if computer_char in line and line[computer_char] == 3:
            if message:
                bot.send_message(message.chat.id, "Bot is winner!", reply_markup=markup)
            user_char = None
            computer_char = None
            return True

    for j in range(len(grid[0])):
        cnt_x = 0
        cnt_o = 0
        for i in range(len(grid)):
            if grid[i][j] == user_char:
                cnt_x += 1
            if grid[i][j] == computer_char:
                cnt_o += 1
        if cnt_x == 3:
            if message:
                bot.send_message(message.chat.id, "You are winner!", reply_markup=markup)
            user_char = None
            computer_char = None
            return True
        if cnt_o == 3:
            if message:
                bot.send_message(message.chat.id, "Bot is winner!", reply_markup=markup)
            user_char = None
            computer_char = None
            return True

    i = 0
    cnt_x = 0
    cnt_o = 0
    while i < len(grid):
        if grid[i][i] == user_char:
            cnt_x += 1
        if grid[i][i] == computer_char:
            cnt_o += 1
        i += 1

    if cnt_x == 3:
        if message:
            bot.send_message(message.chat.id, "You are winner!", reply_markup=markup)
        user_char = None
        computer_char = None
        return True
    if cnt_o == 3:
        if message:
            bot.send_message(message.chat.id, "Bot is winner!", reply_markup=markup)
        user_char = None
        computer_char = None
        return True
    i = 2
    j = 0
    cnt_x = 0
    cnt_o = 0
    while i > -1:
        if grid[i][j] == user_char:
            cnt_x += 1
        if grid[i][j] == computer_char:
            cnt_o += 1
        i -= 1
        j += 1

    if cnt_x == 3:
        if message:
            bot.send_message(message.chat.id, "You are winner!", reply_markup=markup)
        user_char = None
        computer_char = None
        return True
    if cnt_o == 3:
        if message:
            bot.send_message(message.chat.id, "Bot is winner!", reply_markup=markup)
        user_char = None
        computer_char = None
        return True
    if '#' not in Counter(grid[0]) and '#' not in Counter(grid[1]) and '#' not in Counter(grid[2]):
        if message:
            bot.send_message(message.chat.id, "Draw...", reply_markup=markup)
        user_char = None
        computer_char = None
        return True
    return False


bot.polling()
