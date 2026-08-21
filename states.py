from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_code = State()
    waiting_comment = State()


class AdminStates(StatesGroup):
    # Kanal qo'shish
    waiting_channel_forward = State()

    # Kino/kod qo'shish
    waiting_movie_code = State()
    waiting_movie_content = State()

    # Kino o'chirish
    waiting_delete_code = State()

    # Narx sozlash
    waiting_price_amount = State()

    # Karta ma'lumotlarini sozlash
    waiting_card_number = State()

    # Xabar yuborish (broadcast)
    waiting_broadcast = State()
