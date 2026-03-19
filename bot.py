import os
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

DATA_FILE = Path("checkins.json")


# =========================
# ДАНІ
# =========================
BODY_DICTIONARY = {
    "Дихання": [
        "глибоке",
        "поверхневе",
        "швидке",
        "повільне",
        "рівне",
        "переривчасте",
    ],
    "Температура": [
        "тепло",
        "холод",
        "жар",
        "прохолода",
        "печіння",
    ],
    "Тиск і форма": [
        "напруга",
        "стиснення",
        "здавлювання",
        "тиск",
        "тяжкість",
        "легкість",
        "розширення",
        "розпирання",
        "скручування",
        "спазм",
        "скутість",
        "натяг",
        "розкриття",
    ],
    "Сенсорні відчуття": [
        "пульсація",
        "вібрація",
        "поколювання",
        "оніміння",
        "мурашки",
        "щипання",
        "свербіж",
        "біль",
        "нудота",
    ],
    "Стан наповнення": [
        "переповнення",
        "спустошення",
        "порожнеча",
        "голод",
        "жага",
        "насичення",
    ],
    "Тонус і енергія": [
        "активація",
        "завмирання",
        "оживлення",
        "розслаблення",
    ],
}

EMOTION_DICTIONARY = {
    "Тривога": (
        "Стан внутрішнього напруження, настороженості або очікування чогось невизначеного.\n\n"
        "У тілі:\n"
        "— стиснення в грудях\n"
        "— поверхневе або швидке дихання\n"
        "— напруга в животі або плечах\n\n"
        "Про що це може бути:\n"
        "— невизначеність\n"
        "— втрата контролю\n"
        "— очікування загрози"
    ),

    "Страх": (
        "Реакція на реальну або уявну небезпеку.\n\n"
        "У тілі:\n"
        "— холод або тремтіння\n"
        "— завмирання або різка активація\n"
        "— прискорене серцебиття\n\n"
        "Про що це може бути:\n"
        "— потреба в безпеці\n"
        "— сигнал про межі або ризик"
    ),

    "Злість": (
        "Емоція, яка виникає, коли порушуються межі або щось є несправедливим.\n\n"
        "У тілі:\n"
        "— жар, печіння\n"
        "— напруга в руках, щелепі\n"
        "— бажання руху або дії\n\n"
        "Про що це може бути:\n"
        "— порушені межі\n"
        "— потреба в захисті\n"
        "— накопичена напруга"
    ),

    "Сум": (
        "Стан втрати, м’якості або внутрішнього зниження енергії.\n\n"
        "У тілі:\n"
        "— тяжкість у грудях або тілі\n"
        "— сльози або бажання плакати\n"
        "— сповільнення\n\n"
        "Про що це може бути:\n"
        "— проживання втрати\n"
        "— потреба в підтримці\n"
        "— відпускання"
    ),

    "Сором": (
        "Відчуття вразливості та бажання сховатися або зменшитися.\n\n"
        "У тілі:\n"
        "— стискання\n"
        "— тепло в обличчі\n"
        "— опускання погляду\n\n"
        "Про що це може бути:\n"
        "— страх осуду\n"
        "— втрата контакту з собою\n"
        "— бажання бути прийнятим"
    ),

    "Провина": (
        "Емоція, що виникає, коли здається, що ми зробили щось не так.\n\n"
        "У тілі:\n"
        "— тиск у грудях\n"
        "— внутрішнє стискання\n"
        "— важкість\n\n"
        "Про що це може бути:\n"
        "— порушення власних цінностей\n"
        "— потреба виправити або відновити"
    ),

    "Безсилля": (
        "Стан, коли немає відчуття впливу або ресурсу діяти.\n\n"
        "У тілі:\n"
        "— важкість\n"
        "— спустошення\n"
        "— млявість\n\n"
        "Про що це може бути:\n"
        "— перевантаження\n"
        "— виснаження\n"
        "— потреба у відновленні"
    ),

    "Радість": (
        "Стан живості, відкритості та контакту.\n\n"
        "У тілі:\n"
        "— тепло\n"
        "— легкість\n"
        "— розширення\n\n"
        "Про що це може бути:\n"
        "— задоволення\n"
        "— контакт із життям\n"
        "— ресурс"
    ),

    "Полегшення": (
        "Відчуття спаду напруги після складності.\n\n"
        "У тілі:\n"
        "— видих\n"
        "— розслаблення\n"
        "— м’якість\n\n"
        "Про що це може бути:\n"
        "— завершення напруги\n"
        "— повернення в баланс"
    ),

    "Ніжність": (
        "М’який, теплий стан відкритості та турботи.\n\n"
        "У тілі:\n"
        "— тепло в грудях\n"
        "— розслаблення\n"
        "— м’якість\n\n"
        "Про що це може бути:\n"
        "— близькість\n"
        "— контакт\n"
        "— довіра"
    ),

    "Самотність": (
        "Відчуття відсутності контакту або зв’язку з іншими.\n\n"
        "У тілі:\n"
        "— порожнеча\n"
        "— холод\n"
        "— тяжкість\n\n"
        "Про що це може бути:\n"
        "— потреба в зв’язку\n"
        "— відсутність підтримки"
    ),

    "Перевантаження": (
        "Стан, коли занадто багато всього одночасно.\n\n"
        "У тілі:\n"
        "— напруга\n"
        "— тиск у голові\n"
        "— хаос у відчуттях\n\n"
        "Про що це може бути:\n"
        "— надлишок стимулів\n"
        "— потреба в паузі"
    ),

    "Інтерес": (
        "Стан цікавості, залученості та відкритості до нового.\n\n"
        "У тілі:\n"
        "— легка активація\n"
        "— фокус\n"
        "— оживлення\n\n"
        "Про що це може бути:\n"
        "— рух до чогось нового\n"
        "— навчання\n"
        "— дослідження"
    ),

    "Спокій": (
        "Стан рівноваги та стабільності.\n\n"
        "У тілі:\n"
        "— рівне дихання\n"
        "— розслаблення\n"
        "— відсутність напруги\n\n"
        "Про що це може бути:\n"
        "— безпека\n"
        "— баланс\n"
        "— стабільність"
    ),
}


# =========================
# ДОПОМІЖНІ ФУНКЦІЇ
# =========================
def load_data() -> list:
    if not DATA_FILE.exists():
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_entry(entry: dict) -> None:
    data = load_data()
    data.append(entry)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user_entries(user_id: int) -> list:
    data = load_data()
    return [item for item in data if item.get("user_id") == user_id]


def build_reflection(data: dict) -> str:
    place = data.get("place", "тілі").lower()
    place_detail = data.get("place_detail")
    feeling = data.get("feeling", "відчуття").lower()
    breathing = data.get("breathing", "не помічаю").lower()
    movement = data.get("movement", "не зрозуміло").lower()
    intensity = data.get("intensity", "?")
    emotion = data.get("emotion", "не розумію").lower()

    place_text = f"{place} ({place_detail.lower()})" if place_detail else place

    lines = [
        "Ти помічаєш:",
        f"— {feeling} в зоні: {place_text}",
        f"— дихання зараз: {breathing}",
        f"— відчуття: {movement}",
        f"— інтенсивність: {intensity}/10",
        f"— емоційно це найбільше схоже на: {emotion}",
        "",
        "Це не діагноз, а лише м’яке віддзеркалення.",
    ]

    if emotion in ["тривога", "страх"] or feeling in ["стиснення", "напруга"] or breathing == "поверхневе":
        lines.append("Схоже, тіло зараз може бути в стані напруги та настороженості.")
    elif emotion in ["сум", "безсилля"] or feeling in ["тяжкість", "спустошення", "порожнеча"]:
        lines.append("Схоже, тіло зараз може нести втому, смуток або потребу в опорі.")
    elif emotion == "злість" or feeling in ["печіння", "напруга"]:
        lines.append("Схоже, в тілі зараз багато енергії, якій, можливо, хочеться виходу.")
    elif emotion in ["радість", "полегшення", "ніжність"]:
        lines.append("Схоже, тіло зараз переживає більше м’якості, тепла або розширення.")
    else:
        lines.append("Спробуй просто побути з цим відчуттям ще кілька секунд без потреби все пояснювати.")

    return "\n".join(lines)


def suggest_practice(data: dict) -> str:
    emotion = data.get("emotion", "").lower()
    feeling = data.get("feeling", "").lower()
    breathing = data.get("breathing", "").lower()

    if emotion in ["тривога", "страх"] or feeling in ["стиснення", "напруга"] or breathing == "поверхневе":
        return (
            "Спробуй зараз:\n"
            "1. Зробити повільний видих довшим за вдих.\n"
            "2. Спертися спиною на опору.\n"
            "3. Назвати 3 предмети навколо себе."
        )

    if emotion in ["сум", "безсилля"] or feeling in ["тяжкість", "спустошення", "порожнеча"]:
        return (
            "Спробуй зараз:\n"
            "1. Покласти руку на груди або живіт.\n"
            "2. Відчути вагу тіла на стільці або підлозі.\n"
            "3. Запитати себе: «Чого мені зараз не вистачає?»"
        )

    if emotion == "злість" or feeling in ["печіння", "напруга"]:
        return (
            "Спробуй зараз:\n"
            "1. Сильно стиснути й розтиснути кулаки.\n"
            "2. Натиснути стопами в підлогу.\n"
            "3. Зробити 3 активні видихи."
        )

    return (
        "Спробуй коротке заземлення:\n"
        "1. Подивись навколо й знайди 3 предмети.\n"
        "2. Відчуй опору під ногами.\n"
        "3. Повільно видихни.\n"
        "4. Скажи собі подумки: «Я тут, зараз, у контакті з собою»."
    )


def stats_text(entries: list) -> str:
    if not entries:
        return "Поки що записів немає. Зроби перший check-in, і тут з’явиться твоя динаміка."

    last_7 = entries[-7:]
    place_count = {}
    feeling_count = {}
    emotion_count = {}

    for item in last_7:
        place = item.get("place", "—")
        feeling = item.get("feeling", "—")
        emotion = item.get("emotion", "—")

        place_count[place] = place_count.get(place, 0) + 1
        feeling_count[feeling] = feeling_count.get(feeling, 0) + 1
        emotion_count[emotion] = emotion_count.get(emotion, 0) + 1

    def top_items(d: dict, limit: int = 3) -> str:
        sorted_items = sorted(d.items(), key=lambda x: x[1], reverse=True)[:limit]
        return "\n".join([f"— {k}: {v}" for k, v in sorted_items]) if sorted_items else "— Поки що мало даних"

    return (
        "Твоя динаміка за останні записи:\n\n"
        "Найчастіше ти відмічала зони:\n"
        f"{top_items(place_count)}\n\n"
        "Найчастіші відчуття:\n"
        f"{top_items(feeling_count)}\n\n"
        "Найчастіші емоції:\n"
        f"{top_items(emotion_count)}"
    )


# =========================
# КЛАВІАТУРИ
# =========================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Почати check-in")],
            [KeyboardButton(text="⚡ Швидкий запис"), KeyboardButton(text="📚 Тілесний словник")],
            [KeyboardButton(text="💛 Словник емоцій"), KeyboardButton(text="📊 Моя динаміка")],
            [KeyboardButton(text="🌿 Практика на 1 хвилину"), KeyboardButton(text="⚙️ Налаштування")],
        ],
        resize_keyboard=True
    )


def start_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Так, почати")],
            [KeyboardButton(text="Спочатку подивитись, як це працює")],
            [KeyboardButton(text="У головне меню")],
        ],
        resize_keyboard=True
    )


def pause_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Далі")]],
        resize_keyboard=True
    )


def place_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Голова"), KeyboardButton(text="🫁 Груди")],
            [KeyboardButton(text="🗣 Горло"), KeyboardButton(text="☀️ Живіт")],
            [KeyboardButton(text="🫀 Сонячне сплетіння"), KeyboardButton(text="🧍 Спина")],
            [KeyboardButton(text="💪 Руки"), KeyboardButton(text="🦵 Ноги")],
            [KeyboardButton(text="🧍 Все тіло"), KeyboardButton(text="✍️ Інше місце")],
        ],
        resize_keyboard=True
    )


def place_detail_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ліворуч"), KeyboardButton(text="Праворуч")],
            [KeyboardButton(text="Спереду"), KeyboardButton(text="Ззаду")],
            [KeyboardButton(text="Вгорі"), KeyboardButton(text="Внизу")],
            [KeyboardButton(text="Пропустити")],
        ],
        resize_keyboard=True
    )


def feeling_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Напруга"), KeyboardButton(text="Стиснення")],
            [KeyboardButton(text="Тяжкість"), KeyboardButton(text="Порожнеча")],
            [KeyboardButton(text="Тепло"), KeyboardButton(text="Холод")],
            [KeyboardButton(text="Пульсація"), KeyboardButton(text="Вібрація")],
            [KeyboardButton(text="Поколювання"), KeyboardButton(text="Біль")],
            [KeyboardButton(text="Нудота"), KeyboardButton(text="Оніміння")],
            [KeyboardButton(text="Розширення"), KeyboardButton(text="Розпирання")],
            [KeyboardButton(text="Свербіж"), KeyboardButton(text="Печіння")],
            [KeyboardButton(text="Показати більше"), KeyboardButton(text="Інше")],
        ],
        resize_keyboard=True
    )


def feeling_more_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Тремтіння"), KeyboardButton(text="Скутість")],
            [KeyboardButton(text="Спазм"), KeyboardButton(text="Натяг")],
            [KeyboardButton(text="Мурашки"), KeyboardButton(text="Щипання")],
            [KeyboardButton(text="Тиск"), KeyboardButton(text="Здавлювання")],
            [KeyboardButton(text="Розслаблення"), KeyboardButton(text="Легкість")],
            [KeyboardButton(text="Переповнення"), KeyboardButton(text="Спустошення")],
            [KeyboardButton(text="Голод"), KeyboardButton(text="Жага")],
            [KeyboardButton(text="Насичення"), KeyboardButton(text="Активація")],
            [KeyboardButton(text="Завмирання"), KeyboardButton(text="Оживлення")],
            [KeyboardButton(text="Скручування"), KeyboardButton(text="Розкриття")],
            [KeyboardButton(text="Назад до основних")],
        ],
        resize_keyboard=True
    )


def breathing_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Глибоке"), KeyboardButton(text="Поверхневе")],
            [KeyboardButton(text="Швидке"), KeyboardButton(text="Повільне")],
            [KeyboardButton(text="Рівне"), KeyboardButton(text="Переривчасте")],
            [KeyboardButton(text="Не помічаю"), KeyboardButton(text="Пропустити")],
        ],
        resize_keyboard=True
    )


def movement_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Статичне"), KeyboardButton(text="Пульсує")],
            [KeyboardButton(text="Хвилями"), KeyboardButton(text="Розтікається")],
            [KeyboardButton(text="Наростає"), KeyboardButton(text="Слабшає")],
            [KeyboardButton(text="Не розумію")],
        ],
        resize_keyboard=True
    )


def direction_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Вгору"), KeyboardButton(text="Вниз")],
            [KeyboardButton(text="Вліво"), KeyboardButton(text="Вправо")],
            [KeyboardButton(text="Назовні"), KeyboardButton(text="Всередину")],
            [KeyboardButton(text="Без напрямку"), KeyboardButton(text="Пропустити")],
        ],
        resize_keyboard=True
    )


def intensity_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=str(i)) for i in range(0, 6)],
            [KeyboardButton(text=str(i)) for i in range(6, 11)],
        ],
        resize_keyboard=True
    )


def emotion_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Тривога"), KeyboardButton(text="Страх")],
            [KeyboardButton(text="Злість"), KeyboardButton(text="Сум")],
            [KeyboardButton(text="Сором"), KeyboardButton(text="Провина")],
            [KeyboardButton(text="Безсилля"), KeyboardButton(text="Радість")],
            [KeyboardButton(text="Полегшення"), KeyboardButton(text="Ніжність")],
            [KeyboardButton(text="Не розумію"), KeyboardButton(text="Інше")],
        ],
        resize_keyboard=True
    )


def summary_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Що можна зробити зараз")],
            [KeyboardButton(text="Зберегти запис"), KeyboardButton(text="Додати нотатку")],
            [KeyboardButton(text="У головне меню")],
        ],
        resize_keyboard=True
    )


def after_save_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ще один check-in")],
            [KeyboardButton(text="Подивитись історію"), KeyboardButton(text="У головне меню")],
        ],
        resize_keyboard=True
    )


def practice_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заземлення"), KeyboardButton(text="Коли тривожно")],
            [KeyboardButton(text="Коли важко"), KeyboardButton(text="Коли злість")],
            [KeyboardButton(text="Коли не відчуваю себе"), KeyboardButton(text="Перед сном")],
            [KeyboardButton(text="У головне меню")],
        ],
        resize_keyboard=True
    )


def settings_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Нагадування"), KeyboardButton(text="Час check-in")],
            [KeyboardButton(text="Частота звітів"), KeyboardButton(text="Видалити всі записи")],
            [KeyboardButton(text="У головне меню")],
        ],
        resize_keyboard=True
    )


def dictionary_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Відчуття за категоріями"), KeyboardButton(text="Відчуття → можлива емоція")],
            [KeyboardButton(text="Типи чутливості"), KeyboardButton(text="У головне меню")],
        ],
        resize_keyboard=True
    )


def emotion_dictionary_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Тривога"), KeyboardButton(text="Страх")],
            [KeyboardButton(text="Злість"), KeyboardButton(text="Сум")],
            [KeyboardButton(text="Сором"), KeyboardButton(text="Провина")],
            [KeyboardButton(text="Безсилля"), KeyboardButton(text="Радість")],
            [KeyboardButton(text="Полегшення"), KeyboardButton(text="Ніжність")],
            [KeyboardButton(text="У головне меню")],
        ],
        resize_keyboard=True
    )


# =========================
# FSM
# =========================
class CheckInStates(StatesGroup):
    waiting_for_start_choice = State()
    waiting_for_pause = State()
    waiting_for_place = State()
    waiting_for_custom_place = State()
    waiting_for_place_detail = State()
    waiting_for_feeling = State()
    waiting_for_custom_feeling = State()
    waiting_for_breathing = State()
    waiting_for_movement = State()
    waiting_for_direction = State()
    waiting_for_intensity = State()
    waiting_for_emotion = State()
    waiting_for_note = State()
    waiting_after_summary = State()


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(CommandStart())
    async def start_handler(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            "Привіт. Я допоможу тобі краще помічати, що відбувається в тілі.\n\n"
            "Іноді тіло говорить раніше, ніж думки.\n\n"
            "Тут ти зможеш:\n"
            "— швидко фіксувати тілесні відчуття\n"
            "— бачити повторювані патерни\n"
            "— м’якше розуміти свої емоції\n"
            "— повертати контакт із собою\n\n"
            "Це не медичний сервіс і не діагностика. Це інструмент самоспостереження.\n\n"
            "Готова почати перший check-in?",
            reply_markup=start_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_start_choice)

    @dp.message(CheckInStates.waiting_for_start_choice, F.text == "Так, почати")
    @dp.message(F.text == "🧠 Почати check-in")
    async def begin_checkin(message: Message, state: FSMContext):
        await message.answer(
            "Зроби паузу на 10 секунд.\n"
            "Не треба нічого вигадувати. Просто поміть, де в тілі зараз найбільше відчувається життя або напруга.",
            reply_markup=pause_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_pause)

    @dp.message(CheckInStates.waiting_for_start_choice, F.text == "Спочатку подивитись, як це працює")
    async def how_it_works(message: Message):
        await message.answer(
            "Один запис займає приблизно 30–60 секунд.\n\n"
            "Ти просто відповідаєш на кілька питань:\n"
            "— де в тілі відчуття\n"
            "— яке воно\n"
            "— чи воно рухається\n"
            "— наскільки воно сильне\n"
            "— на яку емоцію це найбільше схоже\n\n"
            "У кінці ти отримаєш м’яке віддзеркалення і зможеш зберегти запис."
        )

    @dp.message(F.text == "У головне меню")
    async def back_to_main_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Ти в головному меню.", reply_markup=main_menu())

    @dp.message(CheckInStates.waiting_for_pause, F.text == "Далі")
    async def ask_place(message: Message, state: FSMContext):
        await message.answer("Де саме в тілі відчуття найсильніше?", reply_markup=place_menu())
        await state.set_state(CheckInStates.waiting_for_place)

    @dp.message(CheckInStates.waiting_for_place, F.text == "✍️ Інше місце")
    async def custom_place(message: Message, state: FSMContext):
        await message.answer("Напиши, де саме ти це відчуваєш.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(CheckInStates.waiting_for_custom_place)

    @dp.message(CheckInStates.waiting_for_custom_place)
    async def save_custom_place(message: Message, state: FSMContext):
        await state.update_data(place=message.text)
        await message.answer("Хочеш уточнити локалізацію?", reply_markup=place_detail_menu())
        await state.set_state(CheckInStates.waiting_for_place_detail)

    @dp.message(CheckInStates.waiting_for_place, F.text.in_([
        "🧠 Голова", "🫁 Груди", "🗣 Горло", "☀️ Живіт", "🫀 Сонячне сплетіння",
        "🧍 Спина", "💪 Руки", "🦵 Ноги", "🧍 Все тіло"
    ]))
    async def save_place(message: Message, state: FSMContext):
        place = message.text.split(" ", 1)[1]
        await state.update_data(place=place)
        await message.answer("Хочеш уточнити локалізацію?", reply_markup=place_detail_menu())
        await state.set_state(CheckInStates.waiting_for_place_detail)

    @dp.message(CheckInStates.waiting_for_place_detail)
    async def save_place_detail(message: Message, state: FSMContext):
        text = "" if message.text == "Пропустити" else message.text
        await state.update_data(place_detail=text)
        await message.answer("Яке це відчуття?", reply_markup=feeling_menu())
        await state.set_state(CheckInStates.waiting_for_feeling)

    @dp.message(CheckInStates.waiting_for_feeling, F.text == "Показати більше")
    async def show_more_feelings(message: Message):
        await message.answer("Ось розширений список відчуттів:", reply_markup=feeling_more_menu())

    @dp.message(CheckInStates.waiting_for_feeling, F.text == "Назад до основних")
    async def back_to_basic_feelings(message: Message):
        await message.answer("Повертаю основний список:", reply_markup=feeling_menu())

    @dp.message(CheckInStates.waiting_for_feeling, F.text == "Інше")
    async def custom_feeling(message: Message, state: FSMContext):
        await message.answer("Напиши своїм словом, яке це відчуття.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(CheckInStates.waiting_for_custom_feeling)

    @dp.message(CheckInStates.waiting_for_custom_feeling)
    async def save_custom_feeling(message: Message, state: FSMContext):
        await state.update_data(feeling=message.text)
        await message.answer("Яке зараз дихання?", reply_markup=breathing_menu())
        await state.set_state(CheckInStates.waiting_for_breathing)

    @dp.message(CheckInStates.waiting_for_feeling)
    async def save_feeling(message: Message, state: FSMContext):
        if message.text in ["Показати більше", "Назад до основних", "Інше"]:
            return
        await state.update_data(feeling=message.text)
        await message.answer("Яке зараз дихання?", reply_markup=breathing_menu())
        await state.set_state(CheckInStates.waiting_for_breathing)

    @dp.message(CheckInStates.waiting_for_breathing)
    async def save_breathing(message: Message, state: FSMContext):
        breathing = "" if message.text == "Пропустити" else message.text
        await state.update_data(breathing=breathing)
        await message.answer("Це відчуття рухається чи стоїть на місці?", reply_markup=movement_menu())
        await state.set_state(CheckInStates.waiting_for_movement)

    @dp.message(CheckInStates.waiting_for_movement)
    async def save_movement(message: Message, state: FSMContext):
        await state.update_data(movement=message.text)
        await message.answer("Якщо рухається — куди?", reply_markup=direction_menu())
        await state.set_state(CheckInStates.waiting_for_direction)

    @dp.message(CheckInStates.waiting_for_direction)
    async def save_direction(message: Message, state: FSMContext):
        direction = "" if message.text == "Пропустити" else message.text
        await state.update_data(direction=direction)
        await message.answer("Наскільки це сильно зараз? Оціни від 0 до 10.", reply_markup=intensity_menu())
        await state.set_state(CheckInStates.waiting_for_intensity)

    @dp.message(CheckInStates.waiting_for_intensity)
    async def save_intensity(message: Message, state: FSMContext):
        if not message.text.isdigit() or not 0 <= int(message.text) <= 10:
            await message.answer("Будь ласка, обери число від 0 до 10.")
            return
        await state.update_data(intensity=int(message.text))
        await message.answer(
            "На що це схоже емоційно?\n"
            "Тут не треба вгадати «правильно» — просто обери найближче.",
            reply_markup=emotion_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_emotion)

    @dp.message(CheckInStates.waiting_for_emotion, F.text == "Інше")
    async def custom_emotion(message: Message, state: FSMContext):
        await state.update_data(emotion="інша емоція")
        data = await state.get_data()
        reflection = build_reflection(data)
        await message.answer(reflection, reply_markup=summary_menu())
        await state.set_state(CheckInStates.waiting_after_summary)

    @dp.message(CheckInStates.waiting_for_emotion)
    async def save_emotion(message: Message, state: FSMContext):
        await state.update_data(emotion=message.text)
        data = await state.get_data()
        reflection = build_reflection(data)
        await message.answer(reflection, reply_markup=summary_menu())
        await state.set_state(CheckInStates.waiting_after_summary)

    @dp.message(CheckInStates.waiting_after_summary, F.text == "Що можна зробити зараз")
    async def show_practice_after_summary(message: Message, state: FSMContext):
        data = await state.get_data()
        await message.answer(suggest_practice(data), reply_markup=summary_menu())

    @dp.message(CheckInStates.waiting_after_summary, F.text == "Додати нотатку")
    async def ask_note(message: Message, state: FSMContext):
        await message.answer("Можна одним реченням. Напиши думку або контекст до цього запису.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(CheckInStates.waiting_for_note)

    @dp.message(CheckInStates.waiting_for_note)
    async def save_note(message: Message, state: FSMContext):
        await state.update_data(note=message.text)
        await message.answer("Нотатку додано.", reply_markup=summary_menu())
        await state.set_state(CheckInStates.waiting_after_summary)

    @dp.message(CheckInStates.waiting_after_summary, F.text == "Зберегти запис")
    async def save_final_entry(message: Message, state: FSMContext):
        data = await state.get_data()
        entry = {
            "user_id": message.from_user.id,
            "timestamp": datetime.now().isoformat(),
            "place": data.get("place", ""),
            "place_detail": data.get("place_detail", ""),
            "feeling": data.get("feeling", ""),
            "breathing": data.get("breathing", ""),
            "movement": data.get("movement", ""),
            "direction": data.get("direction", ""),
            "intensity": data.get("intensity", ""),
            "emotion": data.get("emotion", ""),
            "note": data.get("note", ""),
        }
        save_entry(entry)
        await message.answer(
            "Запис збережено.\n\n"
            "Сьогодні ти помітила:\n"
            "— де в тілі з’явилось відчуття\n"
            "— як воно проявляється\n"
            "— наскільки воно сильне\n"
            "— з чим емоційно це може бути пов’язано\n\n"
            "Так формується контакт із собою — не через аналіз, а через помічання.",
            reply_markup=after_save_menu(),
        )
        await state.clear()

    @dp.message(F.text == "Ще один check-in")
    async def another_checkin(message: Message, state: FSMContext):
        await begin_checkin(message, state)

    @dp.message(F.text == "Подивитись історію")
    @dp.message(F.text == "📊 Моя динаміка")
    async def show_stats(message: Message):
        entries = get_user_entries(message.from_user.id)
        await message.answer(stats_text(entries), reply_markup=main_menu())

    @dp.message(F.text == "🌿 Практика на 1 хвилину")
    async def practice_menu_handler(message: Message):
        await message.answer("Обери практику:", reply_markup=practice_menu())

    @dp.message(F.text == "Заземлення")
    async def grounding(message: Message):
        await message.answer(
            "Заземлення:\n"
            "1. Подивись навколо й знайди 3 предмети.\n"
            "2. Відчуй опору під ногами.\n"
            "3. Видихни повільніше, ніж вдихаєш.\n"
            "4. Назви подумки: «Я тут, зараз, у безпеці».",
            reply_markup=practice_menu()
        )

    @dp.message(F.text == "Коли тривожно")
    async def anxious_practice(message: Message):
        await message.answer(
            "Коли тривожно:\n"
            "1. Повільний видих довший за вдих.\n"
            "2. Спиною відчуй опору.\n"
            "3. Назви 3 звуки або 3 предмети поруч.",
            reply_markup=practice_menu()
        )

    @dp.message(F.text == "Коли важко")
    async def hard_practice(message: Message):
        await message.answer(
            "Коли важко:\n"
            "1. Поклади руку на груди або живіт.\n"
            "2. Відчуй вагу тіла.\n"
            "3. Спитай себе: «Що зараз було б для мене підтримкою?»",
            reply_markup=practice_menu()
        )

    @dp.message(F.text == "Коли злість")
    async def anger_practice(message: Message):
        await message.answer(
            "Коли є злість:\n"
            "1. Стисни і розтисни кулаки.\n"
            "2. Натисни стопами в підлогу.\n"
            "3. Зроби 3 сильні видихи.",
            reply_markup=practice_menu()
        )

    @dp.message(F.text == "Коли не відчуваю себе")
    async def disconnected_practice(message: Message):
        await message.answer(
            "Коли складно себе відчути:\n"
            "1. Доторкнись до рук або обличчя.\n"
            "2. Зверни увагу на температуру тіла.\n"
            "3. Запитай: «Що я відчуваю хоча б на 1%?»",
            reply_markup=practice_menu()
        )

    @dp.message(F.text == "Перед сном")
    async def sleep_practice(message: Message):
        await message.answer(
            "Перед сном:\n"
            "1. Повільно видихни 5 разів.\n"
            "2. Розслаб плечі та щелепу.\n"
            "3. Відчуй, як тіло торкається ліжка або стільця.",
            reply_markup=practice_menu()
        )

    @dp.message(F.text == "📚 Тілесний словник")
    async def body_dictionary_handler(message: Message):
        await message.answer("Обереш, що хочеш подивитись:", reply_markup=dictionary_menu())

    @dp.message(F.text == "Відчуття за категоріями")
    async def body_dictionary_categories(message: Message):
        text_parts = ["Тілесний словник:\n"]
        for category, items in BODY_DICTIONARY.items():
            text_parts.append(f"{category}:")
            text_parts.append("— " + "\n— ".join(items))
            text_parts.append("")
        await message.answer("\n".join(text_parts), reply_markup=dictionary_menu())

    @dp.message(F.text == "Відчуття → можлива емоція")
    async def body_to_emotion(message: Message):
        await message.answer(
            "Декілька м’яких прикладів:\n\n"
            "Стиснення в грудях\n"
            "— може бути пов’язане з тривогою, страхом або напругою\n\n"
            "Тяжкість у тілі\n"
            "— може бути пов’язана з втомою, сумом або перевантаженням\n\n"
            "Порожнеча в животі\n"
            "— іноді схожа на самотність, виснаження або безсилля\n\n"
            "Тепло і розширення\n"
            "— може бути пов’язане з полегшенням, радістю, ніжністю",
            reply_markup=dictionary_menu()
        )

    @dp.message(F.text == "Типи чутливості")
    async def sensitivity_types(message: Message):
        await message.answer(
            "Типи чутливості:\n\n"
            "Екстероцептивні\n"
            "— зовнішні відчуття: зір, слух, смак, нюх, дотик\n\n"
            "Пропріоцептивні\n"
            "— положення тіла, рух, баланс\n\n"
            "Інтероцептивні\n"
            "— внутрішні сигнали тіла: дихання, голод, напруга, серцебиття",
            reply_markup=dictionary_menu()
        )

    @dp.message(F.text == "💛 Словник емоцій")
    async def emotion_dictionary_handler(message: Message):
        await message.answer("Обереш емоцію:", reply_markup=emotion_dictionary_menu())

    @dp.message(F.text.in_(list(EMOTION_DICTIONARY.keys())))
    async def show_emotion_description(message: Message):
        description = EMOTION_DICTIONARY.get(message.text)
        if description:
            await message.answer(f"{message.text}\n\n{description}", reply_markup=emotion_dictionary_menu())

    @dp.message(F.text == "⚡ Швидкий запис")
    async def quick_record(message: Message):
        await message.answer(
            "Швидкий запис за 15 секунд.\n\n"
            "Напиши у формулі:\n"
            "де → яке відчуття → сила 0–10\n\n"
            "Приклад:\n"
            "груди, стиснення, 6",
            reply_markup=main_menu()
        )

    @dp.message(F.text == "⚙️ Налаштування")
    async def settings(message: Message):
        await message.answer(
            "Налаштування поки в базовій версії.\n"
            "Пізніше тут можна буде додати нагадування, час check-in і частоту звітів.",
            reply_markup=settings_menu()
        )

    @dp.message(F.text == "Видалити всі записи")
    async def delete_records(message: Message):
        all_data = load_data()
        filtered = [item for item in all_data if item.get("user_id") != message.from_user.id]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        await message.answer("Усі твої записи видалені.", reply_markup=settings_menu())

    @dp.message()
    async def fallback(message: Message):
        await message.answer(
            "Я не зовсім зрозумів це повідомлення.\n"
            "Спробуй обрати кнопку в меню або напиши /start.",
            reply_markup=main_menu()
        )

await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())