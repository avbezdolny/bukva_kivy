#!python3
# -*- coding: utf-8 -*-

import kivy
kivy.require('1.11.1')

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.utils import get_color_from_hex, platform
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import ObjectProperty, ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.modalview import ModalView
from kivy.core.audio import SoundLoader
from kivy.storage.dictstore import DictStore
from os.path import join, dirname
from combi import COMBI
import sqlite3 as DB
import random
import sys


# Returns path containing content - either locally or in pyinstaller tmp file
def resourcePath():
    if hasattr(sys, '_MEIPASS'):
        return join(sys._MEIPASS)
    return join(dirname(__file__))


# Строка соединения с БД
DATABASE_URI = join(resourcePath(), 'dictionary.db')


class DatabaseError(Exception):
    """Пользовательский класс исключения для базы данных!"""
    pass


class UseDatabase:
    """Класс диспетчера контекста для соединения с базой данных!"""

    def __init__(self, config: str) -> None:
        self.configuration = config

    def __enter__(self) -> 'cursor':
        try:
            self.conn = DB.connect(self.configuration)  # соединение с базой данных
            self.cursor = self.conn.cursor()
            return self.cursor
        except Exception as err:
            raise DatabaseError(err)

    def __exit__(self, exc_type, exc_value, exc_trace) -> None:
        self.conn.commit()
        self.cursor.close()
        self.conn.close()
        if exc_type:
            raise DatabaseError(exc_value)  # если ошибка в SQL-запросе


class GameBoard(Widget):
    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y) and not App.get_running_app().is_block:
            App.get_running_app().clear_game_board()
            App.get_running_app().selection_mode = True

    def on_touch_up(self, touch):
        if App.get_running_app().selection_mode:
            App.get_running_app().selection_mode = False
            App.get_running_app().is_block = True
            App.get_running_app().player_selection()


class Tile(Widget):
    letter = StringProperty('*')
    selection = BooleanProperty(False)
    tile_index = 0

    def on_touch_move(self, touch):
        if self.collide_point(touch.x, touch.y) and App.get_running_app().selection_mode:
            self.selection = True
            if self.tile_index not in App.get_running_app().matrix_selection:
                App.get_running_app().matrix_selection.append(self.tile_index)
                if App.get_running_app().is_sound and App.get_running_app().sound_move: App.get_running_app().sound_move.play()


class HistoryLabel(Label):
    pass


class Btn(ButtonBehavior, Widget):
    text = StringProperty('btn')
    color = ListProperty(get_color_from_hex('#26a69a40'))
    text_color = ListProperty(get_color_from_hex('#26a69a'))

    def __init__(self, **kwargs):
        super(Btn, self).__init__(**kwargs)


class ToggleBtn(ButtonBehavior, Widget):
    text = StringProperty('K')
    is_select = BooleanProperty(False)
    color = ListProperty(get_color_from_hex('#26a69a40'))
    text_color = ListProperty(get_color_from_hex('#26a69a'))

    def __init__(self, **kwargs):
        super(ToggleBtn, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            for tbtn in App.get_running_app().key_board.children[2].children:
                if tbtn.text != self.text:
                    tbtn.is_select = False
            self.is_select = True if not self.is_select else False
            if App.get_running_app().is_sound and App.get_running_app().sound_move: App.get_running_app().sound_move.play()
            App.get_running_app().apply_btn.disabled = False if self.is_select else True


class HistoryBoard(ScrollView):
    font_size = NumericProperty(24)
    text = StringProperty('')
    player_text = ListProperty(['', ''])


class KeyBoard(Widget):
    padding = NumericProperty(2)
    button_height = NumericProperty(24)


class ScrollableLabel(ScrollView):
    text = StringProperty('Long text ...')


class ViewInfo(Widget):
    text = StringProperty('Long text ...')


class ViewInfoSmall(Widget):
    text = StringProperty('...')


class ViewChoice(Widget):
    text = StringProperty('...')
    text_yes = StringProperty('Да')
    text_no = StringProperty('Нет')


class SelectBox(ButtonBehavior, Widget):
    text = StringProperty('mode')
    select = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SelectBox, self).__init__(**kwargs)


class ViewMode(Widget):
    text = StringProperty('Начать новую игру?')
    text_yes = StringProperty('Да')
    text_no = StringProperty('Нет')
    text_single_mode = 'Одиночная'
    text_hotseat = 'Хотсит'
    text_balda = 'Быстрый бот'
    text_AI = 'Умный бот'


class BukvaApp(App):
    Window.clearcolor = get_color_from_hex('#000000')
    if platform in ['win', 'linux', 'mac']:
        icon = 'data/icon.png'
        title = 'БУКВА'
        Window.size = (480, 850)
        Window.left = 100
        Window.top = 100

    game_board = ObjectProperty(None)
    info_btn = ObjectProperty(None)
    sound_btn = ObjectProperty(None)
    pass_btn = ObjectProperty(None)
    new_btn = ObjectProperty(None)
    apply_btn = ObjectProperty(None)
    cancel_btn = ObjectProperty(None)
    key_board = ObjectProperty(None)
    history_board = ObjectProperty(None)
    player_label = StringProperty('Игрок ')  # для передачи русских букв в *.kv файл
    player_turn = NumericProperty(0)
    matrix = ListProperty([' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '])
    matrix_selection = ListProperty([])
    selection_mode = BooleanProperty(False)
    is_block = BooleanProperty(True)
    score = ListProperty([0, 0])
    info_label = StringProperty('Конец игры!')
    show_keyboard = BooleanProperty(False)
    history = ListProperty([])
    word_selection = StringProperty('')
    playerAI = BooleanProperty(True)
    temp_playerAI = BooleanProperty(True)
    balda = BooleanProperty(True)  # признак быстрого бота
    temp_balda = BooleanProperty(True)
    black_list = ListProperty([])  # список исключенных из поиска вариантов для ИИ
    is_game_over = BooleanProperty(False)
    store = ObjectProperty()
    border_width = NumericProperty(2)

    # звуки
    is_sound = BooleanProperty(True)
    sound_click = None
    sound_popup = None
    sound_move = None

    # Диалоги
    view_exit = ObjectProperty(None)
    view_info = ObjectProperty(None)
    view_info_small = ObjectProperty(None)
    view_pass = ObjectProperty(None)
    view_mode = ObjectProperty(None)

    def on_start(self):
        self.game_board = self.root.ids.game_board
        self.info_btn = self.root.ids.info_btn
        self.info_btn.text = 'инфо'
        self.sound_btn = self.root.ids.sound_btn
        self.sound_btn.text = 'звук'
        self.pass_btn = self.root.ids.pass_btn
        self.pass_btn.text = 'пас'
        self.new_btn = self.root.ids.new_btn
        self.new_btn.text = 'игра'
        self.apply_btn = self.root.ids.key_board.apply_btn
        self.apply_btn.text = 'Принять'
        self.cancel_btn = self.root.ids.key_board.cancel_btn
        self.cancel_btn.text = 'Отмена'
        self.key_board = self.root.ids.key_board
        self.history_board = self.root.ids.history_board
        self.border_width = min(self.root.width, self.root.height)/480

        self.apply_btn.bind(on_release=self.press_apply_btn)
        self.cancel_btn.bind(on_release=self.press_cancel_btn)

        alphabet = ('А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я')
        for i, item in enumerate(self.key_board.children[2].children):
            item.text = alphabet[-(i + 1)]

        # sounds
        self.sound_click = SoundLoader.load('click.wav')
        self.sound_popup = SoundLoader.load('popup.wav')
        self.sound_move  = SoundLoader.load('move.wav')

        # info dialog
        self.view_info = ModalView(size_hint=(None, None), size=[min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75], auto_dismiss=False, background = 'data/background.png')
        self.view_info.add_widget(ViewInfo())
        self.view_info_small = ModalView(size_hint=(None, None), size=[min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75], auto_dismiss=False, background = 'data/background.png')
        self.view_info_small.add_widget(ViewInfoSmall())

        # exit dialog
        self.view_exit = ModalView(size_hint=(None, None), size=[min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75], auto_dismiss=False, background = 'data/background.png')
        self.view_exit.add_widget(ViewChoice(text='Выйти из игры?'))
        self.view_exit.children[0].ids.yes_btn.bind(on_release=self.stop)

        # pass dialog
        self.view_pass = ModalView(size_hint=(None, None), size=[min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75], auto_dismiss=False, background = 'data/background.png')
        self.view_pass.add_widget(ViewChoice(text='Пропустить ход?'))
        self.view_pass.children[0].ids.yes_btn.bind(on_release=self.pass_turn)

        # mode dialog
        self.view_mode = ModalView(size_hint=(None, None), size=[min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75], auto_dismiss=False, background = 'data/background.png')
        self.view_mode.add_widget(ViewMode())
        self.view_mode.children[0].ids.yes_btn.bind(on_release=self.new_game)

        Window.bind(on_key_down=self.on_key_down)
        if platform in ['win', 'linux', 'mac']: Window.bind(on_request_close=self.on_request_close)
        self.game_board.bind(size=Clock.schedule_once(self.resize, 0.150))
        self.history_board.children[0].children[1].bind(on_ref_press=self.print_it)
        self.history_board.children[0].children[0].children[1].children[0].bind(on_ref_press=self.print_it)
        self.history_board.children[0].children[0].children[0].children[0].bind(on_ref_press=self.print_it)

        # load data settings
        if platform in ['win', 'linux', 'mac']:  # desktop
            self.store = DictStore(join(self.user_data_dir, 'store.dat'))
        else:  # if platform in ['android', 'ios']
            self.store = DictStore('store.dat')  # android API 26+ без запроса разрешений доступа

        if self.store.exists('matrix'):
            self.matrix = self.store.get('matrix')['value'].split('#')
            self.history = self.store.get('history')['value'].split('#')
            self.score = [int(x) for x in self.store.get('score')['value'].split('#')]
            self.playerAI = self.store.get('playerAI')['value']
            self.balda = self.store.get('balda')['value']
            self.player_turn = self.store.get('player_turn')['value']
            self.is_game_over = self.store.get('is_game_over')['value']
            self.history_board.text = self.store.get('board_history')['value']
            self.history_board.player_text = self.store.get('board_player')['value'].split('#')
            self.is_sound = self.store.get('is_sound')['value']
            self.sound_btn.text = '[s]звук[/s]' if not self.is_sound else 'звук'

            if not self.is_game_over:  # продолжаем игру
                self.resume_game()
        else:
            self.begin_game()

    def press_apply_btn(self, *args):
        self.show_keyboard = False
        self.search_word()

    def press_cancel_btn(self, *args):
        self.show_keyboard = False
        self.cancel_player_selection()

    def set_sound(self):
        self.is_sound = True if not self.is_sound else False
        self.sound_btn.text = '[s]звук[/s]' if not self.is_sound else 'звук'

    def show_about(self):
        about = "[size=" + str(int(min(self.view_info.width, self.view_info.height)/14)) + "]БУКВА[/size]\n\n" \
                "Лингвистическая настольная игра для 2 игроков, в которой необходимо составлять слова с " \
                "помощью букв, добавляемых определённым образом на квадратное игровое поле.\n\nСлова составляются " \
                "посредством переходов от буквы к букве под прямым углом. Игровое поле представляет собой " \
                "25-клеточную квадратную таблицу, клетки центральной строки которой содержат по одной букве, " \
                "а строка целиком — произвольное 5-буквенное нарицательное имя существительное в именительном падеже " \
                "и единственном числе (множественном числе, если слово не имеет единственного числа).\n\nВо время " \
                "своего хода игрок может добавить букву в клетку, примыкающую по вертикали или горизонтали к " \
                "заполненной клетке таким образом, чтобы получалась неразрывная и несамопересекающаяся прямоугольная " \
                "ломаная («змейка») из клетки с добавленной буквой и других заполненных клеток, представляющая собой " \
                "слово (соответствующее описанным выше требованиям), или пропустить ход.\n\nВ течение игры должны " \
                "соблюдаться также следующие правила:\n- Игроки ходят по очереди.\n- Каждая клетка содержит только " \
                "одну букву, каждая буква в составленном слове приносит игроку одно очко.\n- Слово должно содержаться " \
                "хотя бы в одном толковом или энциклопедическом словаре (или энциклопедии), при этом запрещаются " \
                "аббревиатуры, слова с уменьшительно-ласкательными (банька, дочурка, ножик) и размерно-оценочными " \
                "суффиксами (домина, зверюга, ножища), если такие слова не имеют специального значения, " \
                "а также слова, не входящие в состав русского литературного языка, то есть вульгаризмы, диалектизмы и " \
                "жаргонизмы (имеющие словарные пометки вульг., диал., жарг. и аналогичные, например, сокращённые " \
                "названия соответствующих регионов).\n- Слова в одной игре повторяться не могут, даже если это " \
                "омонимы.\n\nИгра заканчивается тогда, когда либо заполнены все клетки, либо невозможно составить " \
                "очередное слово согласно указанным выше правилам. Выигрывает тот игрок, который наберёт большее " \
                "количество очков.[size=" + str(int(min(self.view_info.width, self.view_info.height)/30)) + "]\n\n" \
                "* * *\n(c) Антон Бездольный, 2020\n/ вер. 2.0 /[/size]"
        self.view_info.children[0].text = about
        self.view_info.open()

    def pass_turn(self, *args):
        self.is_block = True
        self.info_label = 'Пропуск хода'
        self.next_turn()

    def print_it(self, instance, value):
        if self.is_sound and self.sound_popup: self.sound_popup.play()
        _SQL = "select COMMENT from DICT where WORD = '{s_word}'".format(s_word=value.lower())
        data = None

        try:
            with UseDatabase(DATABASE_URI) as cursor:
                cursor.execute(_SQL)
                data = cursor.fetchall()
        except DatabaseError as err:
            self.info_label = str(err)

        if data:  # найдено в словаре
            self.view_info.children[0].text = data[0][0]
            self.view_info.open()
        else:  # не найдено
            self.view_info_small.children[0].text = value
            self.view_info_small.open()

    def clear_game_board(self):
        for tile in self.game_board.children[0].children:
            tile.selection = False

    def clear_key_board(self):
        for item in self.key_board.children[2].children:
            item.is_select = False

    def resume_game(self):
        if self.playerAI:
            self.black_list = [(10, 11, 12, 13, 14), ]

        # информационное сообщение
        self.info_label = 'Ход игрока ' + str(self.player_turn + 1) + (' >> Выделите слово!' if self.player_turn == 0 or (self.player_turn == 1 and not self.playerAI) else ' ...')

        if not self.playerAI or (self.playerAI and self.player_turn == 0):  # ход человека
            self.is_block = False
        elif self.playerAI and self.player_turn == 1:  # ход ИИ
            Clock.schedule_once(self.searchAI, 0.5)  # таймаут

    def new_game(self, *args):
        self.playerAI = self.temp_playerAI
        self.balda = self.temp_balda

        # очищаем результаты прошлой игры
        self.clear_game_board()
        self.clear_key_board()
        self.show_keyboard = False
        self.is_game_over = False
        self.is_block = True

        self.history = []
        self.score = [0, 0]
        self.history_board.text = ''
        self.history_board.player_text[0] = ''
        self.history_board.player_text[1] = ''
        self.word_selection = ''
        self.matrix_selection = []
        self.matrix = [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']

        self.begin_game()

    def begin_game(self):
        _SQL = 'select WORD from DICT where LEN = {len_word}'.format(len_word=5)
        data = None

        try:
            with UseDatabase(DATABASE_URI) as cursor:
                cursor.execute(_SQL)
                data = cursor.fetchall()
        except DatabaseError as err:
            self.info_label = str(err)

        if data:
            # определяем первое случайное слово
            random_word = random.choice(data)[0].upper()
            self.history.append(random_word)
            self.history_board.text = '[ref=' + random_word + ']' + random_word + '[/ref]'

            self.matrix[10] = random_word[0]
            self.matrix[11] = random_word[1]
            self.matrix[12] = random_word[2]
            self.matrix[13] = random_word[3]
            self.matrix[14] = random_word[4]

            if self.playerAI:
                self.black_list = [(10, 11, 12, 13, 14), ]

            # определяем право первого хода
            self.player_turn = 0 if random.randint(1, 100) <= 50 else 1
            self.info_label = 'Ход игрока ' + str(self.player_turn + 1) + (
                ' >> Выделите слово!' if self.player_turn == 0 or (
                            self.player_turn == 1 and not self.playerAI) else ' ...')

            if not self.playerAI or (self.playerAI and self.player_turn == 0):  # ход человека
                self.is_block = False
            elif self.playerAI and self.player_turn == 1:  # ход ИИ
                Clock.schedule_once(self.searchAI, 0.5)  # таймаут

        else:  # словарь пустой !!!
            self.view_info_small.children[0].text = 'Пустой словарь!'
            if self.is_sound and self.sound_popup: self.sound_popup.play()
            self.view_info_small.open()

    def is_correct_select(self):
        if len(self.word_selection) < 2:  # берем только варианты из как минимум двух элементов
            return False

        count_space = 0
        for ltr in self.word_selection:
            if ltr == ' ':
                count_space += 1
        if count_space != 1:  # берем только варианты содержащие один пробел
            return False

        # исключаем варианты в которых разница между соседними элементами нас не устраивает (не +-1 и не +-5)
        for i in range(1, len(self.matrix_selection)):
            i1 = self.matrix_selection[i]
            i2 = self.matrix_selection[i - 1]
            sub_i1_i2 = i1 - i2
            if sub_i1_i2 != 1 and sub_i1_i2 != -1 and sub_i1_i2 != 5 and sub_i1_i2 != -5:
                return False
            if (i1 == 4 and i2 == 5) or (i1 == 5 and i2 == 4) or (i1 == 9 and i2 == 10) or (i1 == 10 and i2 == 9) or (
                    i1 == 14 and i2 == 15) or (i1 == 15 and i2 == 14) or (i1 == 19 and i2 == 20) or (
                    i1 == 20 and i2 == 19):
                return False

        return True

    def player_selection(self):
        for i in self.matrix_selection:
            self.word_selection += self.matrix[i]

        # если выделение верно
        if self.is_correct_select():
            self.clear_key_board()
            self.show_keyboard = True
            self.apply_btn.disabled = True
            self.info_label = 'Выберите букву!'
        else:
            self.cancel_player_selection('Выделите слово корректно!')

    def cancel_player_selection(self, phraze='Выделите слово!'):
        self.info_label = phraze
        self.matrix_selection = []
        self.word_selection = ''
        self.clear_game_board()
        self.is_block = False

    def search_word(self):
        select_key = ''
        for item in self.key_board.children[2].children:
            if item.is_select:
                select_key = item.text
        s_word = self.word_selection.replace(' ', select_key)

        # проверка на повтор в истории
        if s_word in self.history:
            self.cancel_player_selection(s_word + ' >> Слово уже было!')

        # поиск в базе
        else:
            _SQL = "select WORD from DICT where WORD = '{s_word}'".format(s_word=s_word.lower())
            data = None

            try:
                with UseDatabase(DATABASE_URI) as cursor:
                    cursor.execute(_SQL)
                    data = cursor.fetchall()
            except DatabaseError as err:
                self.info_label = str(err)

            if data:  # найдено в словаре
                self.history.append(s_word)
                self.history_board.player_text[self.player_turn] += '[ref=' + s_word + ']' + s_word + '(' + str(len(s_word)) + ')[/ref]\n'
                self.history_board.scroll_y = 0  # прокрутка в конец списка
                self.info_label = s_word

                for i, item in enumerate(self.matrix_selection):
                    self.matrix[item] = s_word[i]

                if self.playerAI:
                    self.black_list.append(tuple(self.matrix_selection))

                self.score[self.player_turn] += len(s_word)
                self.next_turn()
            else:  # нет такого слова
                self.cancel_player_selection(s_word + ' >> Нет такого слова!')

    def searchAI(self, *args):
        if platform in ['win', 'linux', 'mac']:
            Window.set_system_cursor('wait')

        variantsAI = []  # варианты ИИ

        for elem in COMBI:
            if elem not in self.black_list and self.matrix[elem[0]] not in ['Ь', 'Ъ', 'Ы']:
                count_space = 0

                for i in elem:
                    if self.matrix[i] == ' ':
                        count_space += 1

                if count_space == 1:
                    variantsAI.append(elem)

        data = None
        result = False
        is_over = False

        try:
            with UseDatabase(DATABASE_URI) as cursor:
                while not result:
                    if self.balda:  # быстрый бот
                        self.matrix_selection = list(random.choice(variantsAI))
                    else:  # умный бот
                        len_max = max([len(x) for x in variantsAI])  # max длина варианта
                        var_max = [v for v in variantsAI if len(v) == len_max]  # список вариантов с max длиной
                        self.matrix_selection = list(random.choice(var_max))

                    self.word_selection = ''

                    for index in self.matrix_selection:
                        self.word_selection += self.matrix[index]

                    s_word = self.word_selection.replace(' ', '_')

                    _SQL = "select WORD from DICT where WORD like '{s_word}' and LEN = {s_len}".format(s_word=s_word.lower(), s_len=len(s_word))
                    cursor.execute(_SQL)
                    data = cursor.fetchall()

                    if data:  # найдено в словаре
                        # перебор возможных слов в выбранной комбинации
                        words = [word[0].upper() for word in data]

                        is_word = False  # признак найденного подходящего слова
                        while not is_word:
                            select_word = random.choice(words)
                            if select_word not in self.history:
                                self.history.append(select_word)
                                self.history_board.player_text[
                                    self.player_turn] += '[ref=' + select_word + ']' + select_word + '(' + str(len(select_word)) + ')[/ref]\n'
                                self.history_board.scroll_y = 0  # прокрутка в конец списка
                                self.info_label = select_word
                                for i, item in enumerate(self.matrix_selection):
                                    self.matrix[item] = select_word[i]
                                for tile in self.game_board.children[0].children:  # выделение на игровом поле
                                    tile.selection = False  # убираем сначала предыдущее выделение игроком-человеком
                                    if tile.tile_index in self.matrix_selection:
                                        tile.selection = True
                                self.black_list.append(tuple(self.matrix_selection))
                                self.score[self.player_turn] += len(select_word)
                                is_word = True
                                result = True
                            else:  # слово уже было
                                words.remove(select_word)
                                if len(words) == 0:
                                    is_word = True  # закончились возможные слова в выбранной комбинации, но результата нет ...

                        if not result:  # нет результата в переборке выбранных слов
                            variantsAI.remove(tuple(self.matrix_selection))
                            self.black_list.append(tuple(self.matrix_selection))

                    else:  # не найдено в словаре
                        variantsAI.remove(tuple(self.matrix_selection))
                        self.black_list.append(tuple(self.matrix_selection))

                    if len(variantsAI) == 0:  # закончились возможные варианты, но результата нет ...
                        result = True
                        is_over = True

        except DatabaseError as err:
            self.info_label = str(err)

        if platform in ['win', 'linux', 'mac']:
            Window.set_system_cursor('arrow')

        # итог
        if is_over:  # конец игры !!!
            self.info_label = 'Возможных вариантов нет!'
            Clock.schedule_once(self.game_over, 0.5)  # таймаут
        else:  # продолжаем игру
            self.next_turn()

    def next_turn(self):
        self.matrix_selection = []
        self.word_selection = ''

        # проверка на конец игры !!!
        count_space = 0
        for item in self.matrix:
            if item == ' ':
                count_space += 1
        if count_space == 0:  # конец игры !!!
            self.info_label = 'Конец игры!'
            Clock.schedule_once(self.game_over, 0.5)  # таймаут
        else:  # игра продолжается
            self.player_turn = 0 if self.player_turn == 1 else 1
            self.info_label += ' >> Ход игрока ' + str(self.player_turn + 1)

            if not self.playerAI or (self.playerAI and self.player_turn == 0):  # ход человека
                self.is_block = False
            elif self.playerAI and self.player_turn == 1:  # ход ИИ
                Clock.schedule_once(self.searchAI, 0.5)  # таймаут

    def game_over(self, *args):
        self.is_game_over = True

        # определение победителя
        winner = 0 if self.score[0] == self.score[1] else 1 if self.score[0] > self.score[1] else 2
        string_win = 'Ничья!\n\n' if winner == 0 else 'Победил Игрок ' + str(winner) + '!\n\n'

        # подсветка победителя (если ничья, то не трогаем)
        if winner == 1: self.player_turn = 0
        if winner == 2: self.player_turn = 1

        self.view_info_small.children[0].text = string_win + str(self.score[0]) + ' : ' + str(self.score[1])
        if self.is_sound and self.sound_popup: self.sound_popup.play()
        self.view_info_small.open()

    def resize(self, *args):
        self.border_width = min(self.root.width, self.root.height)/480
        
        self.view_info.size = [min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75]
        self.view_info_small.size = [min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75]
        self.view_exit.size = [min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75]
        self.view_pass.size = [min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75]
        self.view_mode.size = [min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48, (min(self.root.width, self.root.height) - 2*min(self.root.width, self.root.height)/48) * 0.75]

        if self.view_info.children[0].text[1:5] == 'size':
            about = "[size=" + str(int(min(self.view_info.width, self.view_info.height)/14)) + "]БУКВА[/size]\n\n" \
                    "Лингвистическая настольная игра для 2 игроков, в которой необходимо составлять слова с " \
                    "помощью букв, добавляемых определённым образом на квадратное игровое поле.\n\nСлова составляются " \
                    "посредством переходов от буквы к букве под прямым углом. Игровое поле представляет собой " \
                    "25-клеточную квадратную таблицу, клетки центральной строки которой содержат по одной букве, " \
                    "а строка целиком — произвольное 5-буквенное нарицательное имя существительное в именительном падеже " \
                    "и единственном числе (множественном числе, если слово не имеет единственного числа).\n\nВо время " \
                    "своего хода игрок может добавить букву в клетку, примыкающую по вертикали или горизонтали к " \
                    "заполненной клетке таким образом, чтобы получалась неразрывная и несамопересекающаяся прямоугольная " \
                    "ломаная («змейка») из клетки с добавленной буквой и других заполненных клеток, представляющая собой " \
                    "слово (соответствующее описанным выше требованиям), или пропустить ход.\n\nВ течение игры должны " \
                    "соблюдаться также следующие правила:\n- Игроки ходят по очереди.\n- Каждая клетка содержит только " \
                    "одну букву, каждая буква в составленном слове приносит игроку одно очко.\n- Слово должно содержаться " \
                    "хотя бы в одном толковом или энциклопедическом словаре (или энциклопедии), при этом запрещаются " \
                    "аббревиатуры, слова с уменьшительно-ласкательными (банька, дочурка, ножик) и размерно-оценочными " \
                    "суффиксами (домина, зверюга, ножища), если такие слова не имеют специального значения, " \
                    "а также слова, не входящие в состав русского литературного языка, то есть вульгаризмы, диалектизмы и " \
                    "жаргонизмы (имеющие словарные пометки вульг., диал., жарг. и аналогичные, например, сокращённые " \
                    "названия соответствующих регионов).\n- Слова в одной игре повторяться не могут, даже если это " \
                    "омонимы.\n\nИгра заканчивается тогда, когда либо заполнены все клетки, либо невозможно составить " \
                    "очередное слово согласно указанным выше правилам. Выигрывает тот игрок, который наберёт большее " \
                    "количество очков.[size=" + str(int(min(self.view_info.width, self.view_info.height)/30)) + "]\n\n" \
                    "* * *\n(c) Антон Бездольный, 2020\n/ вер. 2.0 /[/size]"
            self.view_info.children[0].text = about
            self.view_info.children[0].scroll_label.scroll_y = 1

    def on_key_down(self, window, key, *args):
        if key in [27, 4]:  # ESC and BACK_BUTTON
            if self.is_sound and self.sound_popup: self.sound_popup.play()
            self.view_exit.open()
            return True

    def on_request_close(self, *args):
        if self.is_sound and self.sound_popup: self.sound_popup.play()
        self.view_exit.open()
        return True

    def save_data(self):
        self.store.put('matrix', value="#".join(self.matrix))
        self.store.put('history', value="#".join(self.history))
        self.store.put('score', value="#".join([str(x) for x in self.score]))
        self.store.put('playerAI', value=self.playerAI)
        self.store.put('balda', value=self.balda)
        self.store.put('player_turn', value=self.player_turn)
        self.store.put('is_game_over', value=self.is_game_over)
        self.store.put('board_history', value=self.history_board.text)
        self.store.put('board_player', value="#".join(self.history_board.player_text))
        self.store.put('is_sound', value=self.is_sound)

    def on_pause(self):
        self.save_data()
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        self.save_data()
        sys.exit(0)  # for Android and other OS


if __name__ == '__main__':
    if platform in ['win', 'linux', 'mac']:  # desktop
        kivy.resources.resource_add_path(resourcePath())
    BukvaApp().run()
