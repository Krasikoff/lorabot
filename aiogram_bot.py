import os
from dotenv import load_dotenv
from aiogram import Router, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    BufferedInputFile
)
from lorabot import LoraBot
from state import MenuOrder

load_dotenv()

token = os.getenv('TG_TOKEN')
bot = Bot(token=token)
#storage = MemoryStorage()
dp = Dispatcher(bot = bot, storage = MemoryStorage())
lora_bot = LoraBot('TG_BOT_NAME')
router = Router()


possible_rating = ['1', '2', '3', '4', '5']
"""Меню пользователя."""
menu = [
    [KeyboardButton(text='Menu a'), KeyboardButton(text='Menu b')],
    [KeyboardButton(text='Make order'),
     KeyboardButton(text='Leave review')],
    [KeyboardButton(text='Leave rating')],
]
user_markup = ReplyKeyboardMarkup(
    keyboard=menu,
    resize_keyboard=True,
    one_time_keyboard=True
)

"""Меню пользователя."""
menu_buy = [
    [KeyboardButton(text='Return')], [KeyboardButton(text='Buy')],
]
buy_markup = ReplyKeyboardMarkup(
    keyboard=menu_buy, resize_keyboard=True, one_time_keyboard=True
)

"""Меню аналитики."""
menu_analytics = [
    [KeyboardButton(text='Total'), KeyboardButton(text='Users')],
    [KeyboardButton(text='Messages'),
     KeyboardButton(text='Events')],
    [KeyboardButton(text='Rating'), KeyboardButton(text='SQL')],
]
analytics_markup = ReplyKeyboardMarkup(
    keyboard=menu_analytics, resize_keyboard=True, one_time_keyboard=True
)
menu_analytics = ['Total', 'Users', 'Messages', 'Events', 'Rating', 'SQL']

"""Меню NO."""
menu_no = [
   [KeyboardButton(text='No'),],
]
no_markup = ReplyKeyboardMarkup(
    keyboard=menu_no, resize_keyboard=True, one_time_keyboard=True
)


user_analytics = {}


@router.message(MenuOrder.password_check)
async def message_password(
    message: Message,
    state: FSMContext):
    if lora_bot.check_password(message.text):
        await bot.send_message(
            message.chat.id, "Choose what you want to analyze",
            reply_markup=analytics_markup
        )
        await state.set_state(MenuOrder.analitics_menu)
    else:
        await bot.send_message(
            message.chat.id, "Error pass", reply_markup=user_markup
        )


@router.message(MenuOrder.analitics_menu)
async def analytics(
    message: Message,
    state: FSMContext):    
    if message.text == 'SQL':
        await bot.send_message(
            message.chat.id, "Write your SQL", reply_markup=no_markup
        )
        user_analytics[message.from_user.id] = {}
        user_analytics[message.from_user.id]['analytics_type'] = message.text
        await state.set_state(MenuOrder.analytics_date)
    elif message.text in menu_analytics:
        await bot.send_message(
            message.chat.id,
            "Set date if you need(start and end date "
            "splitting by space in format 'YYYY-MM-DD')"
            " or select no on menu", reply_markup=no_markup
        )
        user_analytics[message.from_user.id] = {}
        user_analytics[message.from_user.id]['analytics_type'] = message.text
        await state.set_state(MenuOrder.analytics_date)
    else:
        await bot.send_message(
            message.chat.id, "Error_analitics", reply_markup=user_markup
        )

@router.message(MenuOrder.analytics_date)
async def analytics_date(
    message: Message,
    state: FSMContext):
    if user_analytics[message.from_user.id]['analytics_type'] == 'SQL':
        info = lora_bot.sql_query(message.text)
        await bot.send_message(message.chat.id, info, reply_markup=user_markup)
        user_analytics[message.from_user.id] = {}
        await bot.send_message(
            message.chat.id, "End analytics", reply_markup=user_markup
        )
    elif message.text == 'No':
        user_analytics[message.from_user.id]['start_date'] = None
        user_analytics[message.from_user.id]['end_date'] = None
        await bot.send_message(
            message.chat.id,
            "Set message or event type (only this one has types) "
            "or select no on menu",
            reply_markup=no_markup
        )
        await state.set_state(MenuOrder.analytics_type)
    elif len(message.text.split(' ')) == 2:
        date = message.text.split(' ')
        user_analytics[message.from_user.id]['start_date'] = date[0]
        user_analytics[message.from_user.id]['end_date'] = date[1]
        await bot.send_message(
            message.chat.id,
            "Set message or event type (only this one has types) or select "
            "no on menu",
            reply_markup=no_markup
        )
        await state.set_state(MenuOrder.analytics_type)
    else:
        await bot.send_message(message.chat.id, "Error_date", reply_markup=user_markup)


@router.message(MenuOrder.analytics_type)
async def analytics_type(
    message: Message,
    state: FSMContext
    ):
    print('--analytics_type message =', message.text)
    current_state = await state.get_state()
    print('--analytics_type =', current_state)
    print(user_analytics[message.from_user.id])
    if message.text == 'No':
        user_analytics[message.from_user.id]['type'] = None
    else:
        user_analytics[message.from_user.id]['type'] = message.text
    if user_analytics[message.from_user.id]['analytics_type'] == 'Total':
        info = lora_bot.analyze_total(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        await state.set_state(default_state)
    elif user_analytics[message.from_user.id]['analytics_type'] == 'Users':
        photo, info = lora_bot.analyze_new_user(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date'])
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo, info = lora_bot.analyze_user_number_accumulation(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo = lora_bot.analyze_hour_activity(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo, info = lora_bot.analyze_dau(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo, info = lora_bot.analyze_wau(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo, info = lora_bot.analyze_mau(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo, info = lora_bot.analyze_yau(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo, info = lora_bot.analyze_language(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        await state.set_state(default_state)
    elif user_analytics[message.from_user.id]['analytics_type'] == 'Messages':
        photo, info = lora_bot.analyze_messages_number(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date'],
            user_analytics[message.from_user.id]['type']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        info = lora_bot.analyze_messages(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date'],
            user_analytics[message.from_user.id]['type']
        )
        await bot.send_message(message.chat.id, info)
        photo, info = lora_bot.analyze_messages_type(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo, info = lora_bot.analyze_messages_funnel(
            ['Menu c', 'Menu b', 'Menu a'],
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        await state.set_state(default_state)
    elif user_analytics[message.from_user.id]['analytics_type'] == 'Events':
        photo, info = lora_bot.analyze_events_number(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date'],
            user_analytics[message.from_user.id]['type']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        info = lora_bot.analyze_events(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date'],
            user_analytics[message.from_user.id]['type']
        )
        await bot.send_message(message.chat.id, info)
        photo, info = lora_bot.analyze_events_type(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        photo, info = lora_bot.analyze_events_funnel(
            ['Menu received', 'Make order', 'Buy'],
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        await state.set_state(default_state)
    elif user_analytics[message.from_user.id]['analytics_type'] == 'Rating':
        photo, info = lora_bot.analyze_assessment(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
        b_photo = BufferedInputFile(photo,'photo')
        await bot.send_photo(message.chat.id, b_photo)
        info = lora_bot.analyze_review(
            user_analytics[message.from_user.id]['start_date'],
            user_analytics[message.from_user.id]['end_date']
        )
        await bot.send_message(message.chat.id, info)
    user_analytics[message.from_user.id] = {}
    await bot.send_message(
        message.chat.id, "End analytics", reply_markup=user_markup
    )
    await state.set_state(default_state)

@router.message(MenuOrder.rating)
async def rating(
    message: Message,
    state: FSMContext
):  
    if message.text in ('1', '2', '3', '4', '5'):
        rating = int(message.text)
        lora_bot.assessment(rating, message.from_user.id)
        await bot.send_message(
            message.chat.id, "Thank you!", reply_markup=user_markup
        )
        await state.set_state(default_state)
    else:
        await bot.send_message(
            message.chat.id, "Error_type", reply_markup=user_markup
        )

@router.message(MenuOrder.review)
async def review(
    message: Message,
    state: FSMContext
):
#    print(message.text)
    lora_bot.review(message.text, message.from_user.id)
    await bot.send_message(message.chat.id, "Thank you!", reply_markup=user_markup)
    await state.set_state(default_state)

@router.message(default_state, CommandStart())
async def handle_text(message):
    """/start bot."""

    lora_bot.user(message.from_user.id, message.from_user.language_code)
    lora_bot.event('Menu received', 'Order', message.from_user.id)
    await bot.send_message(
        message.chat.id,
        "Hi! Choose commands or write message",
        reply_markup=user_markup
    )


@router.message(F.text.in_(['Menu a', 'Menu b']))
async def handle_text_comand(message):
    print('===', message.text) 
    lora_bot.message(message.text, 'command', message.from_user.id)
    if message.text == 'Menu b':
        lora_bot.event(
            'Event for command that do something',
            'Event simple command',
            message.from_user.id
        )
    await bot.send_message(message.chat.id, f'You use the command {message.text}')


@router.message(F.text == 'secret')
async def handle_text_secret(message):
    lora_bot.message(message.text, 'command', message.from_user.id)
    lora_bot.event('Event for secret command', 'Secret', message.from_user.id)
    await bot.send_message(message.chat.id, f'You use the command {message.text}')

@router.message(F.text)
async def handle_text_analitics(message: Message, state: FSMContext):
    """Колбэк любого текста. Обычное меню."""
    if message.text == "analytics":
        # make message chains for analytics
        await bot.send_message(message.from_user.id, 'Enter password')
        await state.set_state(MenuOrder.password_check)
    else:
        if message.text == 'Make order':
            text = 'Press Buy or Return'
            lora_bot.message(message.text, 'menu', message.from_user.id)
            lora_bot.event('Make order', 'Order',  message.from_user.id)
            await bot.send_message(message.chat.id, text, reply_markup=buy_markup)
        elif message.text == 'Buy':
            text = f'You use the menu command {message.text}'
            lora_bot.message(message.text, 'menu', message.from_user.id)
            lora_bot.event('Buy', 'Order',  message.from_user.id)
            await bot.send_message(message.chat.id, text, reply_markup=user_markup)
        elif message.text == 'Leave rating':
            await bot.send_message(
                message.from_user.id, 'Write the mark to bot(1-5):'
            )
            await state.set_state(MenuOrder.rating)
#            current_state = await state.get_state()
#            print('---Колбэк leave rating--', current_state)
        elif message.text == 'Leave review':
            await bot.send_message(message.from_user.id, 'Write your review')
            await state.set_state(MenuOrder.review)
        elif message.text in menu:
            text = f'You use the menu command {message.text}'
            lora_bot.message(message.text, 'menu', message.from_user.id)
            await bot.send_message(message.chat.id, text, reply_markup=user_markup)
        else:
            text = f'You write {message.text}'
            lora_bot.message(message.text, 'text', message.from_user.id)
            await bot.send_message(message.chat.id, text, reply_markup=user_markup)


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
