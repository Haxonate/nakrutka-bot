import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, CallbackQuery, ContentType
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from SimpleQIWI import *
import sqlite3
import requests
from config import *

qiwi = QApi(phone=phone, token=qiwi_token)

bot = Bot(telegram_token, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

con = sqlite3.connect('db.db')
c = con.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS users (
    user        INTEGER,
    balance     REAL DEFAULT (0),
    orders      INTEGER,
    is_banned   BOOL DEFAULT (FALSE)
    );
""")

users_data = {}
ban_user = []

s = requests.Session()
s.headers['Content-Type'] = 'application/json'
global_service_data = s.post('https://easyliker.ru/api',
                             json={"api_token": easyliker_token, "method": "getServices",
                                   "version": 1.0}).json()

global_service_data: dict
a = list(global_service_data['response']['telegram'])
a.insert(2, ' ')

temp = {}
for _ in a:
    try:
        temp[_] = global_service_data['response']['telegram'][_]
    except:
        temp[_] = ' '

global_service_data['response']['telegram'] = temp
global_service_data['response']['vk'].pop('interviews', None)
global_service_data['response']['telegram']['views_post'][0]['description'] = 'Офферы, среднее качество'


c.execute('SELECT * FROM users')
_ = c.fetchall()

for user in _:
    if user[-1]:
        ban_user.append(user[0])


def split_arr(arr, size):
    arrs = []
    while len(arr) > size:
        pice = arr[:size]
        arrs.append(pice)
        arr = arr[size:]
    arrs.append(arr)
    return arrs

def raw(text, m: [types.Message, CallbackQuery], *args):
    _ = ['first_name', 'last_name', 'username', 'id']
    for __ in _:
        try:
            text = text.replace(__, str(m['from'][__]))
        except:
            text = text.replace(__, '')

    for x in args:
        for _ in x:
            try:
                text = text.replace(_, str(x[_]))
            except:
                text = text.replace(_, '')

    return text

async def delete_msg(msg):
    try:
        await msg.delete()
    except:
        pass

async def on_start(_):
    me = await bot.me
    q = qiwi.balance
    print(f'Бот запустился под ником {me.username}. Баланс qiwi - {int(q[0])}₽.')


"""Клавиатуры"""
def keyboard_menu(id):
    """

    :param id:
    :return: menu keyboard
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    c.execute(f'SELECT balance FROM users WHERE user = {id}')
    bl = c.fetchone()[0]
    services = {'Заказать накрутку🛒': 'nakrutka', '': ' ', f'💸Баланс | {int(bl)}₽': 'balance',
                'Мои заказы🗂': 'orders', 'Тех. поддержка☎️': 'tp'}

    for _ in services:
        keyboard.insert(InlineKeyboardButton(_, callback_data=services[_]))

    if id in admins:
        services = {'': '-', 'Выдать баланс': 'give_balance', 'Забрать баланс': 'take_balance', 'Забанить': 'ban',
                    'Разбанить': 'unban'}
        keyboard.add(InlineKeyboardButton('➖➖➖➖Админ панель➖➖➖➖', callback_data='_'))
        for _ in services:
            keyboard.insert(InlineKeyboardButton(_, callback_data=services[_]))

    return keyboard

def keyboard_website():
    """
    :return: keyboard with website
    """
    keyboard = InlineKeyboardMarkup()
    services = {'Instagram': 'instagram', 'Vk': 'vk', 'YouTube': 'youtube', 'TikTok': 'tiktok', 'Telegram': 'telegram'}

    for _ in services:
        keyboard.insert(InlineKeyboardButton(_, callback_data=services[_]))
    keyboard.add(InlineKeyboardButton('◀️Назад', callback_data='menu'))
    return keyboard

def keyboard_type(id):
    """
    :return: keyboard with type of wrapping
    """
    keyboard = InlineKeyboardMarkup()

    for _ in global_service_data['response'][users_data[id]['website']]:
        if _ == ' ':
            keyboard.row()
            continue
        keyboard.insert(InlineKeyboardButton(dict_types[_], callback_data=_))
    keyboard.row(InlineKeyboardButton('◀️Назад', callback_data='nakrutka'))
    return keyboard




"""Хендлер на сообщения"""
@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='*', commands=['start'])
async def start(msg: types.Message):
    c.execute('SELECT user FROM users')
    u = c.fetchall()

    if not str(msg.from_user.id) in str(u):
        print(f'новый чел {msg.from_user.first_name} | {msg.from_user.username}')
        con.execute(f'INSERT INTO users(user) VALUES ({msg.from_user.id})')
        con.commit()

    users_data[msg.from_user.id] = {}

    await bot.send_message(msg.from_user.id,
                           raw(start_msg, msg),
                           reply_markup=keyboard_menu(msg.from_user.id))

@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='*', commands=['help'])
async def start(msg: types.Message):
    c.execute('SELECT user FROM users')
    u = c.fetchall()

    if not str(msg.from_user.id) in str(u):
        print(f'новый чел {msg.from_user.first_name} | {msg.from_user.username}')
        con.execute(f'INSERT INTO users(user) VALUES ({msg.from_user.id})')
        con.commit()

    users_data[msg.from_user.id] = {}

    await bot.send_message(msg.from_user.id,
                           raw(help_msg, msg),
                           reply_markup=keyboard_menu(msg.from_user.id))


@dp.message_handler(lambda x: x.from_user.id not in ban_user, content_types=ContentType.TEXT)
async def on_text(msg: types.Message):
    if msg.from_user.id not in users_data:
        users_data[msg.from_user.id] = {}

    await bot.send_message(msg.from_user.id, raw(msg_menu, msg),
                           reply_markup=keyboard_menu(msg.from_user.id))

@dp.message_handler(lambda x: x.from_user.id not in ban_user, content_types=ContentType.ANY)
async def on_text(msg: types.Message):
    if msg.from_user.id not in users_data:
        users_data[msg.from_user.id] = {}
    await bot.send_message(msg.from_user.id, raw(other_type, msg),
                           reply_markup=keyboard_menu(msg.from_user.id))



"""Админские методы"""
@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='give_balance', content_types=ContentType.TEXT)
async def on_text(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)

    if 'give_balance' in users_data[msg.from_user.id]:
        if msg.text.isdigit():
            try:
                c.execute(f'SELECT balance FROM users WHERE user = {users_data[msg.from_user.id]["give_balance"]}')
                bl = c.fetchone()[0]
                c.execute('UPDATE users SET balance = (?) WHERE user = (?)', (bl + float(msg.text), users_data[msg.from_user.id]["give_balance"]))
                con.commit()
                await msg.answer(
                    f'Баланс успешно выдан.\nТекущий баланс человека <code>{int(bl + int(msg.text))}</code>₽',
                    reply_markup=keyboard_menu(msg.from_user.id))
                await bot.send_message(users_data[msg.from_user.id]["give_balance"], f'Вам выдан баланс в размере  <code>{msg.text}</code>₽')

                u = await bot.get_chat(users_data[msg.from_user.id]["give_balance"])
                print(f'{msg.from_user.first_name} | {msg.from_user.id} | {msg.from_user.username} выдал {msg.text}Руб {u.first_name} | {u.id} | {u.username}')
            except Exception as e:
                print(e)
                await bot.send_message(msg.from_user.id, 'Не нашел юзера в базе. Попросите человека прописать /start')
            await state.set_state()
            users_data[msg.from_user.id].pop('give_balance', None)

        else:
            await msg.answer('Введите целое число')
        return

    if msg.forward_from:
        id = msg.forward_from.id
        users_data[msg.from_user.id]['give_balance'] = id
        await msg.answer('Сколько выдать рублей на баланс?')

    elif msg.text.isdigit():
        users_data[msg.from_user.id]['give_balance'] = int(msg.text)
        await msg.answer('Сколько выдать рублей на баланс?')

    else:
        await msg.answer('Введите целое число или перешлите сообщение.')

@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='take_balance', content_types=ContentType.TEXT)
async def on_text(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if 'give_balance' in users_data[msg.from_user.id]:
        if msg.text.isdigit():
            try:
                c.execute(f'SELECT balance FROM users WHERE user = {users_data[msg.from_user.id]["give_balance"]}')
                bl = c.fetchone()[0]
                c.execute('UPDATE users SET balance = (?) WHERE user = (?)',
                          (bl - float(msg.text), users_data[msg.from_user.id]["give_balance"]))
                con.commit()
                await msg.answer(f'Баланс успешно забран.\nТекущий баланс человека {int(bl - int(msg.text))}', reply_markup=keyboard_menu(msg.from_user.id))
                u = await bot.get_chat(users_data[msg.from_user.id]["give_balance"])
                print(f'{msg.from_user.first_name} | {msg.from_user.id} | {msg.from_user.username} забрал {msg.text}Руб у {u.first_name} | {u.id} | {u.username} ')
            except:
                await bot.send_message(msg.from_user.id, 'Не нашел юзера в базе. Попросите человека прописать /start')
            await state.set_state()
            users_data[msg.from_user.id].pop('give_balance', None)
        else:
            await msg.answer('Введите целое число')
        return

    if msg.forward_from:
        id = msg.forward_from.id
        users_data[msg.from_user.id]['give_balance'] = id
        await msg.answer('Сколько забрать рублей с баланса?')

    elif msg.text.isdigit():
        users_data[msg.from_user.id]['give_balance'] = int(msg.text)
        await msg.answer('Сколько выдать рублей на баланс?')

    else:
        await msg.answer('Введите целое число или перешлите сообщение.')

@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='ban', content_types=ContentType.TEXT)
async def on_text(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)

    if msg.forward_from:
        ban_user.append(msg.forward_from.id)
        try:
            c.execute(f'UPDATE users SET is_banned = TRUE WHERE user = {msg.forward_from.id}')
            con.commit()

            await msg.answer('Юзер добавлен в игнор', reply_markup=keyboard_menu(msg.from_user.id))
            u = await bot.get_chat(msg.forward_from.id)
            print(f'{msg.from_user.first_name} | {msg.from_user.id} | {msg.from_user.username} добавил {u.first_name} | {u.id} | {u.username} в чс')
        except:
            await msg.answer('Юзер не найден в базе ')
        await state.set_state()

    elif msg.text.isdigit():
        ban_user.append(int(msg.text))
        try:
            c.execute(f'UPDATE users SET is_banned = TRUE WHERE user = {int(msg.text)}')
            con.commit()
            await msg.answer('Юзер добавлен в игнор', reply_markup=keyboard_menu(msg.from_user.id))
        except:
            await msg.answer('Юзер не найден в базе ')
        await state.set_state()

    else:
        await msg.answer('Введите целое число или перешлите сообщение.')

@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='unban', content_types=ContentType.TEXT)
async def on_text(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)

    if msg.forward_from:
        ban_user.remove(msg.forward_from.id)
        try:
            c.execute(f'UPDATE users SET is_banned = FALSE WHERE user = {msg.forward_from.id}')
            con.commit()
            await msg.answer('Юзер убран из черного списка', reply_markup=keyboard_menu(msg.from_user.id))
            u = await bot.get_chat(msg.forward_from.id)
            print(f'{msg.from_user.first_name} | {msg.from_user.id} | {msg.from_user.username} убрал {u.first_name} | {u.id} | {u.username} из чс')
        except:
            await msg.answer('Юзер не найден в базе ')
        await state.set_state()

    elif msg.text.isdigit():
        ban_user.remove(int(msg.text))
        try:
            c.execute(f'UPDATE users SET is_banned = FALSE WHERE user = {int(msg.text)}')
            con.commit()
            await msg.answer('Юзер убран из черного списка', reply_markup=keyboard_menu(msg.from_user.id))
        except:
            await msg.answer('Юзер не найден в базе ')
        await state.set_state()

    else:
        await msg.answer('Введите целое число или перешлите сообщение.')



"""Заполнение данных"""
@dp.callback_query_handler(lambda x: x.from_user.id not in ban_user, state='Type')
async def inline_keyboard(callback_query: CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    if callback_query.data == 'nakrutka':
        await state.set_state()

        await callback_query.message.edit_text(raw(choice_website, callback_query),
                                               reply_markup=keyboard_website())
        return

    users_data[callback_query.from_user.id]["type"] = callback_query.data
    keyboard = InlineKeyboardMarkup(row_width=1)
    for _ in global_service_data['response'][users_data[callback_query.from_user.id]['website']][callback_query.data]:
        price = _['price']
        keyboard.insert(InlineKeyboardButton(f"{_['description'].capitalize()} | {str(price/100*extra_charge)[:5]}₽", callback_data=_['quality']))
    keyboard.row(InlineKeyboardButton('◀️Назад', callback_data='return'))
    services = {'Instagram': 'instagram', 'Vk': 'vk', 'YouTube': 'youtube', 'TikTok': 'tiktok',
                'Telegram': 'telegram'}
    services = {v: k for k, v in services.items()}
    await callback_query.message.edit_text(raw(choice_quality, callback_query, {'TYPE': genitive_dict[users_data[callback_query.from_user.id]['type']], 'WEBSITE': services[users_data[callback_query.from_user.id]['website']]}), reply_markup=keyboard)
    await state.set_state('quality')

@dp.callback_query_handler(lambda x: x.from_user.id not in ban_user, state='quality')
async def inline_keyboard(callback_query: CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)

    if callback_query.data == 'return':
        keyboard = InlineKeyboardMarkup()
        for _ in global_service_data['response'][users_data[callback_query.from_user.id]['website']]:

            if _ == ' ':
                keyboard.row()
                continue
            keyboard.insert(InlineKeyboardButton(dict_types[_].capitalize(), callback_data=_))

        keyboard.row(InlineKeyboardButton('◀️Назад', callback_data='nakrutka'))
        services = {'Instagram': 'instagram', 'Vk': 'vk', 'YouTube': 'youtube', 'TikTok': 'tiktok',
                    'Telegram': 'telegram'}
        services = {v: k for k, v in services.items()}
        await callback_query.message.edit_text(raw(choice_type, callback_query, {'WEBSITE': services[users_data[callback_query.from_user.id]['website']]}), reply_markup=keyboard_type(callback_query.from_user.id))
        await state.set_state('Type')
        return

    users_data[callback_query.from_user.id]["quality"] = callback_query.data
    users_data[callback_query.from_user.id]["msg_link"] = await bot.send_message(callback_query.from_user.id,
                                                                                 raw(input_link_, callback_query))
    await state.set_state('link')

@dp.callback_query_handler(lambda x: x.from_user.id not in ban_user, state='link')
async def inline_keyboard(callback_query: CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    asyncio.create_task(delete_msg(users_data[callback_query.from_user.id]["msg_link"]))

    services = {'Instagram': 'instagram', 'Vk': 'vk', 'YouTube': 'youtube', 'TikTok': 'tiktok',
                'Telegram': 'telegram'}
    services = {v: k for k, v in services.items()}
    await callback_query.message.edit_text(
        raw(choice_type, callback_query, {'WEBSITE': services[users_data[callback_query.from_user.id]['website']]}),
        reply_markup=keyboard_type(callback_query.from_user.id))

    await state.set_state('Type')

@dp.callback_query_handler(lambda x: x.from_user.id not in ban_user, state='count')
async def inline_keyboard(callback_query: CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    services = {'Instagram': 'instagram', 'Vk': 'vk', 'YouTube': 'youtube', 'TikTok': 'tiktok',
                'Telegram': 'telegram'}

    for _ in ["msg_count", "answer_link", "msg_link"]:
        asyncio.create_task(delete_msg(users_data[callback_query.from_user.id][_]))
    services = {v: k for k, v in services.items()}
    await callback_query.message.edit_text(
        raw(choice_type, callback_query, {'WEBSITE': services[users_data[callback_query.from_user.id]['website']]}),
        reply_markup=keyboard_type(callback_query.from_user.id))




    await state.set_state('Type')

@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='link')
async def input_link(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    min_ = 0
    users_data[msg.from_user.id]["link"] = msg.text
    users_data[msg.from_user.id]['answer_link'] = msg
    for _ in global_service_data['response'][users_data[msg.from_user.id]['website']][users_data[msg.from_user.id]['type']]:
        if users_data[msg.from_user.id]['quality'] in str(_):
            min_ = _['min_limit']
            break

    users_data[msg.from_user.id]["msg_count"] = await bot.send_message(msg.from_user.id, raw(input_count, msg, {'MIN': min_}))
    await state.set_state('count')

@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='count')
async def count(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    min_ = 0
    if not msg.text.isdigit():
        await msg.reply('Введите целое число.')
        return

    for _ in global_service_data['response'][users_data[msg.from_user.id]['website']][users_data[msg.from_user.id]['type']]:
        if users_data[msg.from_user.id]['quality'] in str(_):
            min_ = _['min_limit']
            break

    if int(msg.text) < min_:
        await bot.send_message(msg.from_user.id, f'Введите число, больше чем {min_}')
        return

    c.execute(f'SELECT balance FROM users WHERE user = {msg.from_user.id}')
    bl = c.fetchone()[0]

    users_data[msg.from_user.id]["count"] = int(msg.text)
    price = 0

    for _ in global_service_data['response'][users_data[msg.from_user.id]["website"]][users_data[msg.from_user.id]["type"]]:
        if _['quality'] == users_data[msg.from_user.id]['quality']:
            price = _['price']
            break

    sum_ = (int(msg.text) * price) / 100 * extra_charge

    if bl < sum_:
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton('Пополнить баланс', callback_data='up_balance'))
        kb.insert(InlineKeyboardButton('Меню', callback_data='menu'))
        await bot.send_message(msg.from_user.id, 'На счету не достаточно средств для заказа накрутки', reply_markup=kb)
        return
    try:
        p = {"api_token": easyliker_token,
             "method": "createTask",
             "version": 1.0,
             "website": users_data[msg.from_user.id]["website"],
             "type": users_data[msg.from_user.id]["type"],
             "quality": users_data[msg.from_user.id]["quality"],
             "link": users_data[msg.from_user.id]["link"],
             "count": users_data[msg.from_user.id]['count']
             }
        r = s.post('https://easyliker.ru/api', json=p)
    except:
        await bot.send_message(msg.from_user.id, 'Не известная ошибка при создании заказа. Давайте попробуем заново', reply_markup=keyboard_website())
        await state.set_state()
        return

    r_j = r.json()

    if 'error' in r.text:
        if 'BALANCE_TOO_LOW' in r.text:
            for adm in admins:
                try:
                    kb = InlineKeyboardMarkup().insert(InlineKeyboardButton('Пополнить баланс', url='https://easyliker.ru/profile/deposit'))
                    await bot.send_message(adm, 'На балансе сервиса недостаточно средств', reply_markup=kb)
                except:
                    pass

            await bot.send_message(msg.from_user.id, 'Не известная ошибка при создании заказа. Перевел вас в меню',
                                   reply_markup=keyboard_menu(msg.from_user.id))

        elif 'URL_INVALID' in r.text:
            await bot.send_message(msg.from_user.id,
                                   'Похоже, вы не правильно прислали мне ссылку.\nОтправьте мне новую ссылку')
            await state.set_state('link')

        else:
            if "RULES_ERROR" in r.text:
                await bot.send_message(msg.from_user.id, 'Ошибка. Контент задания нарушает правила. Перевел вас в меню',
                                       reply_markup=keyboard_menu(msg.from_user.id))
                await state.set_state()
            elif "ACCOUNT_BLOCKED" in r.text:
                await bot.send_message(msg.from_user.id,
                                       'Ошибка. Аккаунт заблокирован или является закрытым. Перевел вас в меню',
                                       reply_markup=keyboard_menu(msg.from_user.id))
                await state.set_state()
            elif "CREATE_ORDER_ERROR" in r.text:
                await bot.send_message(msg.from_user.id, 'Не известная ошибка при создании заказа. Перевел вас в меню',
                                       reply_markup=keyboard_menu(msg.from_user.id))
                await state.set_state()

    else:

        for adm in admins:
            if send_notify:
                try:
                    await bot.send_message(adm, f'Новая покупка на сумму {int(sum_)}Руб от {msg.from_user.first_name} (@{msg.from_user.username})', )
                except Exception as e:
                    print(e)

            if r_j['response']['balance'] < min_balance:
                try:
                    await bot.send_message(adm, f"На балансе сервиса осталось {r_j['response']['balance']}₽ рублей")
                except:
                    pass

        c.execute(f'SELECT orders FROM users WHERE user = {msg.from_user.id}')
        orders = c.fetchone()[0]

        orders = '' if orders is None else str(orders) + ', '
        orders = str(orders) + str(r_j['response']['id'])

        c.execute('UPDATE users SET orders = (?) WHERE user = (?)', (orders, msg.from_user.id))
        con.commit()

        c.execute('UPDATE users SET balance = (?) WHERE user = (?)', (bl - sum_, msg.from_user.id))
        con.commit()

        await bot.send_message(msg.from_user.id,
                               raw(success_purchase, msg),
                               reply_markup=keyboard_menu(msg.from_user.id))

        await state.set_state()



@dp.message_handler(lambda x: x.from_user.id not in ban_user, state='input balance')
async def amount(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)

    if not msg.text.isdigit():
        await bot.send_message(msg.from_user.id, 'Введите целое число')
        return

    if int(msg.text) < min_refill:
        await bot.send_message(msg.from_user.id, raw(if_min_refill, msg))
        return

    comment = qiwi.bill(int(msg.text), f'{msg.from_user.id}[{str(uuid4())[0:5]}]')
    users_data[msg.from_user.id]["amount"] = int(msg.text)
    users_data[msg.from_user.id]["comment"] = comment

    kb = InlineKeyboardMarkup(row_width=2)
    kb.insert(InlineKeyboardButton('Проверить оплату', callback_data='check_pay'))
    kb.insert(InlineKeyboardButton('Отменить оплату', callback_data='cancel_pay'))
    url = f"https://qiwi.com/payment/form/99?extra['account']={phone}&amountInteger={users_data[msg.from_user.id]['amount']}&amountFraction=0&currency=643&extra['comment']={comment}&blocked[0]=sum&blocked[1]=account&blocked[2]=comment"
    kb.insert(InlineKeyboardButton('Быстра оплата', url=url))
    await bot.send_message(msg.from_user.id,
                           raw(bill, msg, {'SUM': users_data[msg.from_user.id]["amount"], 'COMMENT': comment}),
                           reply_markup=kb)
    await state.set_state()



@dp.callback_query_handler(lambda x: x.from_user.id not in ban_user, state='*')
async def inline_keyboard(callback_query: CallbackQuery):
    state = dp.current_state(user=callback_query.from_user.id)
    a = {'Instagram': 'instagram', 'Vk': 'vk', 'YouTube': 'youtube', 'TikTok': 'tiktok', 'Telegram': 'telegram'}

    if callback_query.from_user.id not in users_data:
        users_data[callback_query.from_user.id] = {}
        pass

    if callback_query.data == 'menu':
        for _ in ['msg_up_balance', 'msg_tp']:
            if _ in users_data[callback_query.from_user.id]:
                asyncio.create_task(delete_msg(users_data[callback_query.from_user.id][_]))

        await callback_query.message.edit_text(raw(msg_menu, callback_query),reply_markup=keyboard_menu(callback_query.from_user.id))
        await state.set_state()
        return

    elif callback_query.data == 'tp':
        users_data[callback_query.from_user.id]['msg_tp'] = await bot.send_message(callback_query.from_user.id, msg_support, disable_web_page_preview=True)
        pass

    elif callback_query.data == 'return':
        users_data[callback_query.from_user.id] = {}
        await callback_query.message.edit_text(raw(msg_menu, callback_query), reply_markup=keyboard_website())
        return

    elif callback_query.data == 'balance':
        admin_info = ''
        kb = InlineKeyboardMarkup()
        kb.insert(InlineKeyboardButton('◀️Назад', callback_data='menu'))
        kb.insert(InlineKeyboardButton('Пополнить баланс', callback_data='up_balance'))
        c.execute(f'SELECT balance FROM users WHERE user = {callback_query.from_user.id}')
        bl = c.fetchone()[0]
        c.execute(f'SELECT orders FROM users WHERE user = {callback_query.from_user.id}')
        orders = str(c.fetchone()[0])
        orders = orders.split(', ') if not orders is None else []
        if callback_query.from_user.id in admins:
            kb.add(InlineKeyboardButton('Пополнить баланс EasyLiker', url='https://easyliker.ru/profile/deposit'))
            q = int(qiwi.balance[0])
            d = {
                "api_token": easyliker_token,
                "method": "getBalance",
                "version": 1.0
            }
            r = s.post('https://easyliker.ru/api', json=d)
            bl_s = int(r.json()['response'])
            admin_info += f'\n➖➖➖➖➖➖➖➖➖➖➖➖\nБаланс Qiwi: {q}₽\nБаланс EasyLiker: {bl_s}₽'

        await callback_query.message.edit_text(
            raw(balance_msg, callback_query, {'BALANCE': int(bl), 'COUNT_ORDERS': len(orders)}) + admin_info,
            reply_markup=kb)

        return

    elif callback_query.data == 'up_balance':
        await state.set_state('input balance')
        users_data[callback_query.from_user.id]['msg_up_balance'] = await bot.send_message(callback_query.from_user.id, raw(input_refill, callback_query))
        return

    elif callback_query.data == 'check_pay':
        qiwi._parse_payments()
        r = qiwi.check(users_data[callback_query.from_user.id]['comment'])
        if r:
            if send_notify:
                for adm in admins:
                    try:
                        await bot.send_message(adm,
                                               f'Новое пополнение на {int(users_data[callback_query.from_user.id]["amount"])}Руб от {callback_query.from_user.first_name} | @{callback_query.from_user.username}')
                    except:
                        pass

            await bot.answer_callback_query(callback_query.id, text='Успешное пополнение баланса.', show_alert=True)
            c.execute(f'SELECT balance FROM users WHERE user = {callback_query.from_user.id}')
            bl = c.fetchone()[0]
            c.execute('UPDATE users set balance = (?) WHERE user = (?)', (float(users_data[callback_query.from_user.id]['amount']+bl), callback_query.from_user.id))
            con.commit()

            await callback_query.message.edit_text(
                'Вы в главном меню. используй клавиатуру ниже для удобства.',
                reply_markup=keyboard_menu(callback_query.from_user.id))

        else:
            await bot.answer_callback_query(callback_query.id, text='Не нашел пополнения счета. Попробуй еще раз',
                                            show_alert=False)
            await asyncio.sleep(3)

    elif callback_query.data == 'cancel_pay':
        await callback_query.answer('Оплата отменена', show_alert=False)
        await callback_query.message.edit_text(raw(msg_menu, callback_query),
                                               reply_markup=keyboard_menu(callback_query.from_user.id))
        return

    elif callback_query.data == 'nakrutka':
        for _ in ['msg_up_balance', 'msg_tp']:
            if _ in users_data[callback_query.from_user.id]:
                asyncio.create_task(delete_msg(users_data[callback_query.from_user.id][_]))

        await callback_query.message.edit_text(raw(choice_website, callback_query),
                                               reply_markup=keyboard_website())
        return

    elif callback_query.data == 'orders':
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton('◀️Назад', callback_data='menu'))
        c.execute(f'SELECT orders FROM users WHERE user ={callback_query.from_user.id}', )
        orders = c.fetchone()[0]
        orders_data = []

        if orders is None:
            text_msg = raw(no_orders, callback_query)
            kb.add(InlineKeyboardButton('Заказать накрутку', callback_data='nakrutka'))

        else:

            for order in str(orders).split(', '):
                json = {
                    "api_token": easyliker_token,
                    "method": "getTasks",
                    "version": 1.0,
                    "id": int(order)
                }
                r = s.post('https://easyliker.ru/api', json=json)
                try:
                    orders_data.append(r.json()['response'][0])
                except:
                    pass

            text_msg = ''
            orders_data.reverse()
            for x, order in enumerate(orders_data):
                text_msg += f'<b>{order["name"]}</b>\nЦена заказа: {int(order["sum"]/100*extra_charge)}₽\nСсылка: {order["link"]}\nСтатус: <b>{order["status"]}</b>\n'
                if not x + 1 == len(orders_data):
                    text_msg += '➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n'

        await callback_query.message.edit_text(text_msg, disable_web_page_preview=True, reply_markup=kb)

    elif callback_query.data in ['give_balance', 'take_balance', 'ban', 'unban', '_'] and callback_query.from_user.id in admins:
        if callback_query.data != '_':
            kb = InlineKeyboardMarkup()
            kb.insert(InlineKeyboardButton('В меню', callback_data='menu'))
            await callback_query.message.edit_text('Перешлите сообщение человека или введите его ID', reply_markup=kb)
            await state.set_state(callback_query.data)

    elif callback_query.data in a.values():
        users_data[callback_query.from_user.id]["website"] = callback_query.data
        services = {'Instagram': 'instagram', 'Vk': 'vk', 'YouTube': 'youtube', 'TikTok': 'tiktok','Telegram': 'telegram'}
        services = {v: k for k, v in services.items()}

        await callback_query.message.edit_text(
            raw(choice_type, callback_query, {'WEBSITE': services[callback_query.data]}),
            reply_markup=keyboard_type(callback_query.from_user.id))
        await state.set_state('Type')

    else:
        for _ in ['msg_up_balance', 'msg_tp']:
            if _ in users_data[callback_query.from_user.id]:
                asyncio.create_task(delete_msg(users_data[callback_query.from_user.id][_]))

        await callback_query.message.edit_text(
            raw(msg_menu, callback_query),
            reply_markup=keyboard_menu(callback_query.from_user.id))
        await state.set_state()
        return

executor.start_polling(dp, on_startup=on_start)
