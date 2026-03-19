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
        "глибоке — дихання відчувається об’ємним, повним, з більшим простором у грудях або животі",
        "поверхневе — дихання ніби коротше, дрібніше, може не вистачати відчуття повного вдиху",
        "вільне — дихання йде легко, без помітного опору",
        "стиснуте — ніби важко вдихнути або видихнути повністю, є відчуття обмеження",
        "швидке — вдихи й видихи частішають, інколи майже непомітно",
        "повільне — ритм дихання сповільнений, більш розмірений",
        "рівне — дихання відчувається стабільним і передбачуваним",
        "переривчасте — ритм дихання збивається, ніби є паузи або уривки",
    ],
    "Температура": [
        "тепло — приємне або нейтральне відчуття зігрівання",
        "холод — відчуття прохолоди, охолодження, іноді віддалення від контакту",
        "жар — більш інтенсивне тепло, яке може наростати",
        "прохолода — м’який варіант холоду",
        "печіння — тепло з гострішим, більш подразливим відтінком",
    ],
    "Тиск і форма": [
        "напруга — ніби тіло або частина тіла зібрана, утримується, не відпускає",
        "стиснення — відчуття, ніби щось зменшує простір усередині",
        "здавлювання — більш інтенсивний варіант стиснення",
        "тиск — ніби щось натискає зсередини або зовні",
        "тяжкість — відчуття ваги, щільності, обтяження",
        "легкість — відчуття меншої ваги, більшого простору або свободи",
        "розширення — ніби з’являється більше простору всередині",
        "розпирання — відчуття, ніби щось розсуває зсередини",
        "скручування — ніби всередині є поворот, спіраль, згортання",
        "спазм — коротке або хвилеподібне різке скорочення",
        "скутість — мало рухливості, мало м’якості, ніби все застигло",
        "натяг — ніби щось натягнуте всередині або по поверхні",
        "розкриття — відчуття більшої відкритості, м’якості, простору",
    ],
    "Сенсорні відчуття": [
        "пульсація — ритмічне биття, поштовхи або хвилі",
        "вібрація — дрібне внутрішнє тремтіння або дзижчання",
        "поколювання — ніби дрібні уколи або імпульси",
        "оніміння — менше чутливості, притупленість контакту",
        "мурашки — хвиля дрібних відчуттів по шкірі або в тілі",
        "щипання — локальне відчуття ніби щось ущипує",
        "свербіж — потреба почухати, внутрішнє подразнення",
        "біль — сигнал дискомфорту або перевантаження, який може бути різним за характером",
    ],
    "Стан наповнення": [
        "переповнення — ніби всередині вже занадто багато",
        "спустошення — ніби щось вичерпалось або стало порожнім",
        "порожнеча — відчуття відсутності наповнення, контакту або опори",
        "голод — тілесна потреба в їжі або енергії",
        "жага — потреба у воді, зволоженні, відновленні",
        "насичення — достатність, завершеність, більше не хочеться додавати",
    ],
    "Тонус і енергія": [
        "активація — більше мобілізації, зібраності, готовності діяти",
        "завмирання — ніби система зупинилась або дуже пригальмувала",
        "пожвавлення — повернення контакту, енергії, тепла, руху",
        "розслаблення — менше контролю і напруги, більше м’якості",
    ],
}

EMOTION_DICTIONARY_STAGE2 = {
    "Базові емоції і почуття": [
        "страх", "стурбованість", "занепокоєння", "настороженість", "напруженість",
        "хвилювання", "тривога", "переляк", "сум’яття", "паніка", "жах",
        "гнів", "роздратування", "гіркота", "злість", "обурення", "лють", "ненависть",
        "сум", "відраза", "радість", "інтерес", "смуток", "неприязнь", "задоволення",
        "цікавість", "хандра", "обридливість", "умиротворення", "жвавість", "туга",
        "гидування", "втіха", "захопленість", "пригніченість", "веселість",
        "збудження", "горе", "насолода", "ентузіазм", "скорбота", "щастя",
        "азарт", "відчай", "захват", "драйв", "тріумфування", "блаженство",
        "ейфорія", "шок", "остовпіння",
    ],
    "Соціальні емоції і почуття": [
        "сором", "соромливість", "боязкість", "ніяковість", "образа", "досада",
        "сердитість", "скривдженість", "провина", "заздрість", "нудьга", "прийняття",
        "жалкування", "ревнощі", "розпач", "суперництво", "апатія", "загальмованість",
        "ніжність", "симпатія", "каяття", "ворожість", "співчуття", "прив'язаність",
        "вдячність", "благоговіння", "повага",
    ],
    "Складні почуття": [
        "ніяковість: страх + прийняття",
        "презирство: гнів + гидливість",
        "розчарування: здивування + смуток",
        "жалість: співчуття + гордовитість",
        "кохання: радість + прийняття",
        "ентузіазм: радість + цікавість",
    ],
    "Стани, спричинені гамою почуттів": [
        "нервозність", "неповноцінність", "ніяковість", "невпевненість", "приниженість",
        "покірність", "збентеженість", "нетерпимість", "мстивість", "войовничість",
        "агресія", "бунтарство", "опір", "цинічність", "скепсис", "негативізм",
        "безвихідь", "засмучення", "розгубленість", "депресія", "пригніченість",
        "спустошеність", "меланхолія", "виснаження", "зневіра", "зневага",
        "вседозволеність", "зверхність", "зарозумілість", "холодність", "байдужість",
        "гордовитість", "підозрілість", "самовдоволеність", "самотність", "відкинутість",
        "ізольованість", "безпорадність", "слабкість", "вразливість", "покинутість",
        "відчуженість", "смирення", "впевненість", "довольство", "життєрадісність",
        "полегшення", "підбадьореність", "розслабленість", "безтурботність",
        "одухотвореність", "співпричетність", "натхнення", "наснага", "надія",
        "життєлюбність", "рішучість",
    ],
}

EMOTION_DETAILS = {
    "страх": {
        "what": "Страх з’являється, коли щось сприймається як небезпека або загроза. Він допомагає захиститися, відступити або зібратись.",
        "body": "У тілі це часто відчувається як холод, завмирання, напруга, прискорення серцебиття, бажання стиснутись або сховатись.",
        "about": "Часто це про безпеку, межі, вразливість або невідомість."
    },
    "тривога": {
        "what": "Тривога часто виникає не через явну небезпеку, а через невизначеність, очікування або перенавантаження.",
        "body": "У тілі це може бути поверхневе або стиснуте дихання, стиснення в грудях, напруга в животі, неспокій, неможливість розслабитись.",
        "about": "Часто це про контроль, невизначеність, внутрішню готовність до чогось складного."
    },
    "гнів": {
        "what": "Гнів виникає, коли щось здається несправедливим, коли порушуються межі або щось заважає важливому.",
        "body": "У тілі це може бути жар, тиск, напруга в щелепі, грудях, руках, бажання рухатись або діяти різкіше.",
        "about": "Часто це про межі, силу, фрустрацію, потребу захистити себе або щось важливе."
    },
    "сум": {
        "what": "Сум пов’язаний із втратою, виснаженням, розчаруванням або потребою сповільнитись і побути з тим, що болить.",
        "body": "У тілі це часто відчувається як тяжкість, м’якість, зниження енергії, повільність, клубок у горлі або сльози.",
        "about": "Часто це про втрату, нестачу, завершення чогось важливого або потребу в підтримці."
    },
    "радість": {
        "what": "Радість — це стан більшої живості, контакту, легкості або наповненості.",
        "body": "У тілі це може бути тепло, розширення, легкість, більше руху, бажання ділитися або бути в контакті.",
        "about": "Часто це про задоволення, близькість, сенс, безпеку або приємну новизну."
    },
    "сором": {
        "what": "Сором часто пов’язаний із відчуттям, що тебе можуть оцінити, відкинути або побачити надто вразливо.",
        "body": "У тілі це може бути жар в обличчі, бажання зменшитися, напруга, стискання, відведення погляду.",
        "about": "Часто це про вразливість, контакт, образ себе, соціальну чутливість."
    },
    "провина": {
        "what": "Провина виникає, коли здається, що було зроблено щось не так або завдано шкоди.",
        "body": "У тілі це може бути важкість, стискання, тиск у грудях або животі, бажання виправити, повернути або компенсувати.",
        "about": "Часто це про відповідальність, цінності, стосунки, межі."
    },
    "інтерес": {
        "what": "Інтерес — це стан уваги, допитливості й природного потягу до чогось нового або важливого.",
        "body": "У тілі це може бути оживлення, більша зібраність, легке розширення, більше ясності й присутності.",
        "about": "Часто це про дослідження, новизну, залученість, бажання зрозуміти або наблизитися."
    },
    "відраза": {
        "what": "Відраза виникає, коли щось сприймається як токсичне, огидне, надто чуже або неприйнятне.",
        "body": "У тілі це може бути напруження в обличчі, животі, горлі, бажання відсунутись або відвернутись.",
        "about": "Часто це про захист, неприйняття, межі, уникнення контакту."
    },
    "презирство": {
        "what": "Презирство часто з’являється, коли щось або хтось сприймається як нижче, негідне поваги або дуже чуже ціннісно.",
        "body": "У тілі це може бути холодність, відсторонення, напруга в обличчі, верхній частині тіла, дистанція.",
        "about": "Часто це про оцінку, дистанцію, захисне віддалення або жорсткість до себе чи інших."
    },
    "подив": {
        "what": "Подив виникає, коли реальність раптом відрізняється від того, що очікувалось.",
        "body": "У тілі це може бути завмирання, коротка пауза, розширення очей, затримка дихання, різке переключення уваги.",
        "about": "Часто це про новизну, несподіваність, зміну картини світу тут і зараз."
    },
    "вина": {
        "what": "Вина — це емоція, яка часто пов’язана з відчуттям, що було порушено щось важливе у стосунках або у власних цінностях.",
        "body": "У тілі це може бути стискання, важкість, внутрішній тиск, бажання сховатись або виправити ситуацію.",
        "about": "Часто це про відповідальність, стосунки, турботу, моральний конфлікт."
    },
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


def clear_choice(text: str) -> str:
    if not text:
        return ""
    if " " in text and text[0] in "🧠🫁🧍☀️💪🦵✋😁😲😔😤🤢🙄😨🫣🧐💔😱✍️":
        return text.split(" ", 1)[1]
    return text


def is_throat_choice(data: dict) -> bool:
    zone = data.get("body_zone", "").lower()
    subzone = data.get("body_subzone", "").lower()
    return zone == "шия" and subzone == "горло"


def build_location_text(data: dict) -> str:
    side = data.get("region_detail", "")
    zone = data.get("body_zone", "")
    subzone = data.get("body_subzone", "")

    parts = []
    if side:
        parts.append(side.lower())
    if zone:
        parts.append(zone.lower())
    if subzone:
        parts.append(subzone.lower())

    return ", ".join(parts) if parts else "не вказано"


def build_reflection(data: dict) -> str:
    now_text = datetime.now().strftime("%d.%m.%Y %H:%M")
    breathing = data.get("breathing", "не вказано")
    location = build_location_text(data)
    valence = data.get("valence", "не вказано")
    feeling = data.get("feeling", "не вказано")
    movement = data.get("movement_type", "не вказано")
    direction = data.get("direction", "")
    intensity = data.get("intensity", "не вказано")
    emotion = data.get("emotion", "не вказано")

    movement_text = movement.lower()
    if movement.lower() == "рухається" and direction:
        movement_text = f"рухається ({direction.lower()})"

    return (
        "Ось що зараз вдалося помітити:\n\n"
        f"🕒 Дата і час: {now_text}\n"
        f"🌬 Дихання: {breathing.lower() if isinstance(breathing, str) else breathing}\n"
        f"📍 Де в тілі: {location}\n"
        f"🧭 Оцінка відчуття: {valence.lower() if isinstance(valence, str) else valence}\n"
        f"🫧 Назва відчуття: {feeling.lower() if isinstance(feeling, str) else feeling}\n"
        f"🔄 Рух: {movement_text}\n"
        f"📈 Інтенсивність: {intensity}/10\n"
        f"💛 Емоційно це найбільше схоже на: {emotion.lower() if isinstance(emotion, str) else emotion}\n\n"
        "Це не діагноз і не оцінка. Це просто спосіб м’якше побути в контакті з собою."
    )


def suggest_practice(data: dict) -> str:
    emotion = str(data.get("emotion", "")).lower()
    feeling = str(data.get("feeling", "")).lower()
    breathing = str(data.get("breathing", "")).lower()
    valence = str(data.get("valence", "")).lower()

    if emotion in ["тривога", "страх"] or feeling in ["стиснення", "напруга"] or breathing in ["поверхневе", "стиснуте"]:
        return (
            "Спробуй зараз:\n"
            "1. Видихнути трохи повільніше, ніж вдихаєш.\n"
            "2. Відчути опору під ногами.\n"
            "3. Назвати 3 предмети навколо себе."
        )

    if emotion in ["печаль", "сум"] or feeling in ["тяжкість", "порожнеча"] or valence == "неприємне":
        return (
            "Спробуй зараз:\n"
            "1. Покласти руку на груди або живіт.\n"
            "2. Відчути вагу тіла на поверхні.\n"
            "3. Поставити собі питання: «Що зараз могло б мене трохи підтримати?»"
        )

    if emotion == "гнів" or feeling in ["печіння", "напруга"]:
        return (
            "Спробуй зараз:\n"
            "1. М’яко стиснути й розслабити кулаки.\n"
            "2. Натиснути стопами в підлогу.\n"
            "3. Зробити 3 активні видихи."
        )

    return (
        "Можна спробувати коротку мікропаузу:\n"
        "1. Подивись навколо.\n"
        "2. Відчуй тіло на опорі.\n"
        "3. Зроби один повільний видих.\n"
        "4. Просто залишся з собою ще на кілька секунд."
    )


def stats_text(entries: list) -> str:
    if not entries:
        return "Поки що тут порожньо. Зроби перший check-in — і тут з’явиться твоя динаміка."

    last_10 = entries[-10:]

    zones = {}
    feelings = {}
    emotions = {}

    for item in last_10:
        zone = item.get("body_zone", "—")
        feeling = item.get("feeling", "—")
        emotion = item.get("emotion", "—")

        zones[zone] = zones.get(zone, 0) + 1
        feelings[feeling] = feelings.get(feeling, 0) + 1
        emotions[emotion] = emotions.get(emotion, 0) + 1

    def top_items(d: dict, title: str) -> str:
        items = sorted(d.items(), key=lambda x: x[1], reverse=True)[:3]
        if not items:
            return f"{title}\n— Поки що мало даних"
        return title + "\n" + "\n".join([f"— {k}: {v}" for k, v in items])

    return (
        "Твоя динаміка за останні записи:\n\n"
        f"{top_items(zones, 'Найчастіші зони тіла:')}\n\n"
        f"{top_items(feelings, 'Найчастіші відчуття:')}\n\n"
        f"{top_items(emotions, 'Найчастіші емоції:')}"
    )


# =========================
# КЛАВІАТУРИ
# =========================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Почати check-in")],
            [KeyboardButton(text="⚡ Швидкий запис"), KeyboardButton(text="📚 Тілесний словник")],
            [KeyboardButton(text="💛 Словник емоцій і почуттів"), KeyboardButton(text="📊 Моя динаміка")],
            [KeyboardButton(text="🌿 Практика на 1 хвилину"), KeyboardButton(text="⚙️ Налаштування")],
        ],
        resize_keyboard=True
    )


def start_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Почати check-in")],
            [KeyboardButton(text="Головне меню")],
        ],
        resize_keyboard=True
    )


def pause_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Далі")]],
        resize_keyboard=True
    )


def breathing_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Глибоке"), KeyboardButton(text="Поверхневе")],
            [KeyboardButton(text="Вільне"), KeyboardButton(text="Стиснуте")],
            [KeyboardButton(text="Швидке"), KeyboardButton(text="Повільне")],
            [KeyboardButton(text="Рівне"), KeyboardButton(text="Переривчасте")],
            [KeyboardButton(text="Важко відповісти"), KeyboardButton(text="Пропустити")],
        ],
        resize_keyboard=True
    )


def region_detail_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ліворуч"), KeyboardButton(text="Праворуч")],
            [KeyboardButton(text="Спереду"), KeyboardButton(text="Ззаду")],
            [KeyboardButton(text="Вгорі"), KeyboardButton(text="Внизу")],
            [KeyboardButton(text="Пропустити")],
        ],
        resize_keyboard=True
    )


def body_zone_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Голова"), KeyboardButton(text="🫁 Груди")],
            [KeyboardButton(text="🧍 Шия"), KeyboardButton(text="☀️ Живіт")],
            [KeyboardButton(text="🧍 Спина"), KeyboardButton(text="💪 Руки")],
            [KeyboardButton(text="🦵 Ноги"), KeyboardButton(text="✋ Шкіра")],
            [KeyboardButton(text="🧍 Все тіло"), KeyboardButton(text="✍️ Інше місце")],
        ],
        resize_keyboard=True
    )


def subzone_menu(zone: str):
    zone_map = {
        "Голова": [
            "Скроні", "Лоб", "Маківка", "Потилиця", "Обличчя", "Щелепа", "Очі", "Вуха"
        ],
        "Груди": [
            "Центр грудей", "Ліворуч у грудях", "Праворуч у грудях", "Під ключицями", "Ребра"
        ],
        "Шия": [
            "Передня частина шиї", "Бокова частина шиї", "Задня частина шиї", "Горло"
        ],
        "Живіт": [
            "Верхня частина живота", "Центр живота", "Нижня частина живота", "Ліворуч", "Праворуч"
        ],
        "Спина": [
            "Верх спини", "Між лопатками", "Поперек", "Крижі"
        ],
        "Руки": [
            "Плечі", "Передпліччя", "Лікті", "Кисті", "Пальці"
        ],
        "Ноги": [
            "Стегна", "Коліна", "Гомілки", "Стопи", "Пальці ніг"
        ],
        "Шкіра": [
            "Обличчя", "Шия", "Руки", "Ноги", "Спина", "Живіт", "Все тіло"
        ],
        "Все тіло": [
            "Всередині тіла", "По поверхні тіла", "Хвилями по тілу", "Важко локалізувати"
        ],
    }

    items = zone_map.get(zone, [])
    rows = []

    for i in range(0, len(items), 2):
        row = [KeyboardButton(text=items[i])]
        if i + 1 < len(items):
            row.append(KeyboardButton(text=items[i + 1]))
        rows.append(row)

    rows.append([KeyboardButton(text="✍️ Свій варіант")])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def valence_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Приємне"), KeyboardButton(text="Нейтральне"), KeyboardButton(text="Неприємне")],
        ],
        resize_keyboard=True
    )


def feeling_menu(include_nausea: bool = False):
    rows = [
        [KeyboardButton(text="Напруга"), KeyboardButton(text="Стиснення")],
        [KeyboardButton(text="Тяжкість"), KeyboardButton(text="Порожнеча")],
        [KeyboardButton(text="Тепло"), KeyboardButton(text="Холод")],
        [KeyboardButton(text="Пульсація"), KeyboardButton(text="Вібрація")],
        [KeyboardButton(text="Поколювання"), KeyboardButton(text="Біль")],
    ]

    if include_nausea:
        rows.append([KeyboardButton(text="Нудота"), KeyboardButton(text="Оніміння")])
    else:
        rows.append([KeyboardButton(text="Оніміння"), KeyboardButton(text="Розширення")])

    rows.extend([
        [KeyboardButton(text="Розширення"), KeyboardButton(text="Розпирання")],
        [KeyboardButton(text="Свербіж"), KeyboardButton(text="Печіння")],
        [KeyboardButton(text="Показати більше"), KeyboardButton(text="Інше")],
    ])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


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
            [KeyboardButton(text="Завмирання"), KeyboardButton(text="Пожвавлення")],
            [KeyboardButton(text="Скручування"), KeyboardButton(text="Розкриття")],
            [KeyboardButton(text="Назад до основних")],
        ],
        resize_keyboard=True
    )


def movement_type_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Статичне"), KeyboardButton(text="Рухається")],
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
            [KeyboardButton(text="😁 Радість"), KeyboardButton(text="😲 Подив")],
            [KeyboardButton(text="😔 Печаль"), KeyboardButton(text="😤 Гнів")],
            [KeyboardButton(text="🤢 Відраза"), KeyboardButton(text="🙄 Презирство")],
            [KeyboardButton(text="😨 Страх"), KeyboardButton(text="🫣 Сором")],
            [KeyboardButton(text="🧐 Інтерес"), KeyboardButton(text="💔 Вина")],
            [KeyboardButton(text="😱 Тривога"), KeyboardButton(text="Не розумію")],
            [KeyboardButton(text="Інше")],
        ],
        resize_keyboard=True
    )


def summary_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Що можна зробити зараз")],
            [KeyboardButton(text="Зберегти запис"), KeyboardButton(text="Додати нотатку")],
            [KeyboardButton(text="Головне меню")],
        ],
        resize_keyboard=True
    )


def after_save_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ще один check-in")],
            [KeyboardButton(text="Подивитись історію"), KeyboardButton(text="Головне меню")],
        ],
        resize_keyboard=True
    )


def practice_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Заземлення"), KeyboardButton(text="Перед сном")],
            [KeyboardButton(text="Кордони"), KeyboardButton(text="Активація енергії")],
            [KeyboardButton(text="Зниження енергії"), KeyboardButton(text="Тілесний сканер")],
            [KeyboardButton(text="Дихальні вправи")],
            [KeyboardButton(text="Головне меню")],
        ],
        resize_keyboard=True
    )


def settings_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Видалити всі записи")],
            [KeyboardButton(text="Головне меню")],
        ],
        resize_keyboard=True
    )


def dictionary_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Відчуття за категоріями"), KeyboardButton(text="Відчуття → можлива емоція")],
            [KeyboardButton(text="Типи відчуттів")],
            [KeyboardButton(text="Головне меню")],
        ],
        resize_keyboard=True
    )


def emotion_dictionary_categories_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Базові емоції і почуття")],
            [KeyboardButton(text="Соціальні емоції і почуття")],
            [KeyboardButton(text="Складні почуття")],
            [KeyboardButton(text="Стани, спричинені гамою почуттів")],
            [KeyboardButton(text="Головне меню")],
        ],
        resize_keyboard=True
    )


def emotion_list_menu(items: list[str]):
    rows = []
    for i in range(0, len(items), 2):
        row = [KeyboardButton(text=items[i])]
        if i + 1 < len(items):
            row.append(KeyboardButton(text=items[i + 1]))
        rows.append(row)
    rows.append([KeyboardButton(text="Назад до категорій")])
    rows.append([KeyboardButton(text="Головне меню")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


# =========================
# FSM
# =========================
class CheckInStates(StatesGroup):
    waiting_for_start_choice = State()
    waiting_for_pause = State()
    waiting_for_breathing = State()
    waiting_for_region_detail = State()
    waiting_for_body_zone = State()
    waiting_for_custom_zone = State()
    waiting_for_subzone = State()
    waiting_for_custom_subzone = State()
    waiting_for_valence = State()
    waiting_for_feeling = State()
    waiting_for_custom_feeling = State()
    waiting_for_movement_type = State()
    waiting_for_direction = State()
    waiting_for_intensity = State()
    waiting_for_emotion = State()
    waiting_for_custom_emotion = State()
    waiting_for_note = State()
    waiting_after_summary = State()


# =========================
# MAIN
# =========================
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # -------- START --------
    @dp.message(CommandStart())
    async def start_handler(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            "Привіт, я твій Body Check-in помічник. Я допоможу тобі краще помічати, що відбувається в твоєму тілі.\n\n"
            "Нас не вчили прислухатися до свого тіла, але ніколи не пізно почати. "
            "Адже саме воно — твій найточніший навігатор, який першим сигналізує про стрес, втому, напругу чи потреби.\n\n"
            "Навчившись його чути, ти зможеш краще розуміти себе, свої емоції та стан — і вчасно про себе подбати 🤍",
            reply_markup=start_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_start_choice)

    @dp.message(F.text == "Головне меню")
    async def go_to_main_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer("Ти в головному меню.", reply_markup=main_menu())

    # -------- CHECK-IN START --------
    @dp.message(CheckInStates.waiting_for_start_choice, F.text == "🧠 Почати check-in")
    @dp.message(F.text == "🧠 Почати check-in")
    async def begin_checkin(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            "Зроби коротку паузу. Не треба нічого вигадувати — просто зверни увагу на себе.\n"
            "Коли будеш готова, натисни «Далі».",
            reply_markup=pause_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_pause)

    @dp.message(CheckInStates.waiting_for_pause, F.text == "Далі")
    async def ask_breathing(message: Message, state: FSMContext):
        await message.answer(
            "Яке зараз дихання?",
            reply_markup=breathing_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_breathing)

    # -------- BREATHING --------
    @dp.message(CheckInStates.waiting_for_breathing)
    async def save_breathing(message: Message, state: FSMContext):
        breathing = "" if message.text == "Пропустити" else message.text
        await state.update_data(breathing=breathing)
        await message.answer(
            "Хочеш уточнити, з якого боку або в якій частині тіла це відчувається?",
            reply_markup=region_detail_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_region_detail)

    # -------- REGION DETAIL --------
    @dp.message(CheckInStates.waiting_for_region_detail)
    async def save_region_detail(message: Message, state: FSMContext):
        region_detail = "" if message.text == "Пропустити" else message.text
        await state.update_data(region_detail=region_detail)
        await message.answer(
            "У якій зоні тіла це відчувається найсильніше?",
            reply_markup=body_zone_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_body_zone)

    # -------- BODY ZONE --------
    @dp.message(CheckInStates.waiting_for_body_zone, F.text == "✍️ Інше місце")
    async def ask_custom_zone(message: Message, state: FSMContext):
        await message.answer(
            "Напиши свій варіант місця в тілі.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(CheckInStates.waiting_for_custom_zone)

    @dp.message(CheckInStates.waiting_for_custom_zone)
    async def save_custom_zone(message: Message, state: FSMContext):
        await state.update_data(body_zone=message.text, body_subzone="")
        await message.answer(
            "Оціни це відчуття.",
            reply_markup=valence_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_valence)

    @dp.message(CheckInStates.waiting_for_body_zone)
    async def save_body_zone(message: Message, state: FSMContext):
        zone = clear_choice(message.text)
        await state.update_data(body_zone=zone)
        await message.answer(
            "Хочеш точніше назвати місце?",
            reply_markup=subzone_menu(zone),
        )
        await state.set_state(CheckInStates.waiting_for_subzone)

    # -------- SUBZONE --------
    @dp.message(CheckInStates.waiting_for_subzone, F.text == "✍️ Свій варіант")
    async def ask_custom_subzone(message: Message, state: FSMContext):
        await message.answer(
            "Напиши свій варіант точнішої локалізації.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(CheckInStates.waiting_for_custom_subzone)

    @dp.message(CheckInStates.waiting_for_custom_subzone)
    async def save_custom_subzone(message: Message, state: FSMContext):
        await state.update_data(body_subzone=message.text)
        await message.answer(
            "Оціни це відчуття.",
            reply_markup=valence_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_valence)

    @dp.message(CheckInStates.waiting_for_subzone)
    async def save_subzone(message: Message, state: FSMContext):
        await state.update_data(body_subzone=message.text)
        await message.answer(
            "Оціни це відчуття.",
            reply_markup=valence_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_valence)

    # -------- VALENCE --------
    @dp.message(CheckInStates.waiting_for_valence)
    async def save_valence(message: Message, state: FSMContext):
        await state.update_data(valence=message.text)
        data = await state.get_data()
        include_nausea = is_throat_choice(data)

        await message.answer(
            "Назви це відчуття.",
            reply_markup=feeling_menu(include_nausea=include_nausea),
        )
        await state.set_state(CheckInStates.waiting_for_feeling)

    # -------- FEELING --------
    @dp.message(CheckInStates.waiting_for_feeling, F.text == "Показати більше")
    async def show_more_feelings(message: Message, state: FSMContext):
        await message.answer(
            "Ось розширений список відчуттів:",
            reply_markup=feeling_more_menu(),
        )

    @dp.message(CheckInStates.waiting_for_feeling, F.text == "Назад до основних")
    async def back_to_main_feelings(message: Message, state: FSMContext):
        data = await state.get_data()
        include_nausea = is_throat_choice(data)
        await message.answer(
            "Повертаю основний список відчуттів:",
            reply_markup=feeling_menu(include_nausea=include_nausea),
        )

    @dp.message(CheckInStates.waiting_for_feeling, F.text == "Інше")
    async def ask_custom_feeling(message: Message, state: FSMContext):
        await message.answer(
            "Напиши своїм словом, яке це відчуття.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(CheckInStates.waiting_for_custom_feeling)

    @dp.message(CheckInStates.waiting_for_custom_feeling)
    async def save_custom_feeling(message: Message, state: FSMContext):
        await state.update_data(feeling=message.text)
        await message.answer(
            "Це відчуття статичне чи воно рухається?",
            reply_markup=movement_type_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_movement_type)

    @dp.message(CheckInStates.waiting_for_feeling)
    async def save_feeling(message: Message, state: FSMContext):
        if message.text in ["Показати більше", "Назад до основних", "Інше"]:
            return

        await state.update_data(feeling=message.text)
        await message.answer(
            "Це відчуття статичне чи воно рухається?",
            reply_markup=movement_type_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_movement_type)

    # -------- MOVEMENT --------
    @dp.message(CheckInStates.waiting_for_movement_type)
    async def save_movement_type(message: Message, state: FSMContext):
        movement_type = message.text
        await state.update_data(movement_type=movement_type)

        if movement_type == "Рухається":
            await message.answer(
                "Якщо рухається — куди?",
                reply_markup=direction_menu(),
            )
            await state.set_state(CheckInStates.waiting_for_direction)
        else:
            await state.update_data(direction="")
            await message.answer(
                "Яка інтенсивність у цього відчуття?",
                reply_markup=intensity_menu(),
            )
            await state.set_state(CheckInStates.waiting_for_intensity)

    @dp.message(CheckInStates.waiting_for_direction)
    async def save_direction(message: Message, state: FSMContext):
        direction = "" if message.text == "Пропустити" else message.text
        await state.update_data(direction=direction)
        await message.answer(
            "Яка інтенсивність у цього відчуття?",
            reply_markup=intensity_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_intensity)

    # -------- INTENSITY --------
    @dp.message(CheckInStates.waiting_for_intensity)
    async def save_intensity(message: Message, state: FSMContext):
        if not message.text.isdigit() or not 0 <= int(message.text) <= 10:
            await message.answer("Будь ласка, обери число від 0 до 10.")
            return

        await state.update_data(intensity=int(message.text))
        await message.answer(
            "На що це схоже емоційно?",
            reply_markup=emotion_menu(),
        )
        await state.set_state(CheckInStates.waiting_for_emotion)

    # -------- EMOTION --------
    @dp.message(CheckInStates.waiting_for_emotion, F.text == "Інше")
    async def ask_custom_emotion(message: Message, state: FSMContext):
        await message.answer(
            "Напиши своїм словом, на що це схоже емоційно.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(CheckInStates.waiting_for_custom_emotion)

    @dp.message(CheckInStates.waiting_for_custom_emotion)
    async def save_custom_emotion(message: Message, state: FSMContext):
        await state.update_data(emotion=message.text)
        data = await state.get_data()
        reflection = build_reflection(data)
        await message.answer(reflection, reply_markup=summary_menu())
        await state.set_state(CheckInStates.waiting_after_summary)

    @dp.message(CheckInStates.waiting_for_emotion)
    async def save_emotion(message: Message, state: FSMContext):
        emotion = clear_choice(message.text)
        await state.update_data(emotion=emotion)
        data = await state.get_data()
        reflection = build_reflection(data)
        await message.answer(reflection, reply_markup=summary_menu())
        await state.set_state(CheckInStates.waiting_after_summary)

    # -------- SUMMARY ACTIONS --------
    @dp.message(CheckInStates.waiting_after_summary, F.text == "Що можна зробити зараз")
    async def show_practice_after_summary(message: Message, state: FSMContext):
        data = await state.get_data()
        await message.answer(suggest_practice(data), reply_markup=summary_menu())

    @dp.message(CheckInStates.waiting_after_summary, F.text == "Додати нотатку")
    async def ask_note(message: Message, state: FSMContext):
        await message.answer(
            "Можна одним реченням. Додай думку, контекст або те, що хочеться не загубити.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(CheckInStates.waiting_for_note)

    @dp.message(CheckInStates.waiting_for_note)
    async def save_note(message: Message, state: FSMContext):
        await state.update_data(note=message.text)
        await message.answer(
            "Нотатку додано.",
            reply_markup=summary_menu(),
        )
        await state.set_state(CheckInStates.waiting_after_summary)

    @dp.message(CheckInStates.waiting_after_summary, F.text == "Зберегти запис")
    async def save_final_entry(message: Message, state: FSMContext):
        data = await state.get_data()

        entry = {
            "user_id": message.from_user.id,
            "timestamp": datetime.now().isoformat(),
            "breathing": data.get("breathing", ""),
            "region_detail": data.get("region_detail", ""),
            "body_zone": data.get("body_zone", ""),
            "body_subzone": data.get("body_subzone", ""),
            "valence": data.get("valence", ""),
            "feeling": data.get("feeling", ""),
            "movement_type": data.get("movement_type", ""),
            "direction": data.get("direction", ""),
            "intensity": data.get("intensity", ""),
            "emotion": data.get("emotion", ""),
            "note": data.get("note", ""),
        }

        save_entry(entry)

        await message.answer(
            "Запис збережено 🤍\n\n"
            "Тепер це спостереження залишиться в твоїй динаміці. "
            "Іноді навіть короткий check-in допомагає краще зрозуміти себе і вчасно помітити, що насправді відбувається.",
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

    # -------- QUICK RECORD --------
    @dp.message(F.text == "⚡ Швидкий запис")
    async def quick_record(message: Message):
        await message.answer(
            "Швидкий запис за 15 секунд.\n\n"
            "Напиши коротко у форматі:\n"
            "місце, відчуття, сила 0–10\n\n"
            "Приклад:\n"
            "груди, стиснення, 6",
            reply_markup=main_menu()
        )

    # -------- BODY DICTIONARY --------
    @dp.message(F.text == "📚 Тілесний словник")
    async def body_dictionary_handler(message: Message):
        await message.answer(
            "Обереш, що хочеться подивитись:",
            reply_markup=dictionary_menu()
        )

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
            "Кілька м’яких прикладів зв’язку між тілесними відчуттями й емоційним станом:\n\n"
            "Стиснення в грудях\n"
            "— часто буває поруч із тривогою, страхом, внутрішньою напругою або стримуванням емоцій\n\n"
            "Тяжкість у тілі\n"
            "— може з’являтись поруч із втомою, сумом, виснаженням, перевантаженням\n\n"
            "Клубок у горлі або напруга в шиї\n"
            "— іноді буває поруч із тривогою, стриманими сльозами, невисловленими словами, напруженням у контакті\n\n"
            "Порожнеча всередині\n"
            "— може бути пов’язана з виснаженням, самотністю, безсиллям, втратою контакту із собою\n\n"
            "Жар або тиск у тілі\n"
            "— іноді з’являється поруч із гнівом, роздратуванням, фрустрацією або сильним збудженням\n\n"
            "Холод, завмирання, оніміння\n"
            "— може виникати поруч зі страхом, перевантаженням або станом відсторонення\n\n"
            "Розширення, тепло, легкість\n"
            "— часто буває поруч із полегшенням, радістю, близькістю, відчуттям безпеки\n\n"
            "Свербіж, щипання, напруження по шкірі\n"
            "— іноді виникає на тлі збудження, тривоги, подразнення або перевантаження нервової системи\n\n"
            "Це не означає, що кожне відчуття має лише одну причину. "
            "Тіло і емоції пов’язані, але важливо дивитись на них м’яко і з цікавістю, а не шукати одну «правильну» відповідь.",
            reply_markup=dictionary_menu()
        )

    @dp.message(F.text == "Типи відчуттів")
    async def sensitivity_types(message: Message):
        await message.answer(
            "Типи відчуттів:\n\n"
            "Екстероцептивні\n"
            "— сигнали із зовнішнього світу: зір, слух, дотик, нюх, смак\n\n"
            "Пропріоцептивні\n"
            "— відчуття положення тіла, руху, напруження м’язів\n\n"
            "Інтероцептивні\n"
            "— внутрішні сигнали тіла: дихання, серцебиття, голод, тепло, напруга",
            reply_markup=dictionary_menu()
        )

    # -------- EMOTION DICTIONARY --------
    @dp.message(F.text == "💛 Словник емоцій і почуттів")
    async def emotion_dictionary_start(message: Message):
        await message.answer(
            "Обереш категорію:",
            reply_markup=emotion_dictionary_categories_menu()
        )

    @dp.message(F.text.in_(list(EMOTION_DICTIONARY_STAGE2.keys())))
    async def show_emotion_category(message: Message):
    items = EMOTION_DICTIONARY_STAGE2[message.text]
    await message.answer(
        f"{message.text}:",
        reply_markup=emotion_list_menu(items)
    )

    @dp.message(F.text == "Назад до категорій")
    async def back_to_emotion_categories(message: Message):
        await message.answer(
            "Обереш категорію:",
            reply_markup=emotion_dictionary_categories_menu()
        )

    @dp.message(F.text.in_(
    sum([v for v in EMOTION_DICTIONARY_STAGE2.values()], [])
))
async def show_emotion_item(message: Message):
    raw = message.text
    base_word = raw.split(":")[0].strip().lower()

    details = EMOTION_DETAILS.get(base_word)

    if details:
        text = (
            f"{raw}\n\n"
            f"Що це за емоція чи почуття:\n{details['what']}\n\n"
            f"Як це може відчуватись у тілі:\n{details['body']}\n\n"
            f"Про що це може бути:\n{details['about']}"
        )
    else:
        text = (
            f"{raw}\n\n"
            "Що це за емоція чи почуття:\n"
            "Це стан або почуття, яке може бути тоншим, складнішим або більш контекстним, ніж базові емоції.\n\n"
            "Як це може відчуватись у тілі:\n"
            "У тілі такі стани часто проявляються через зміни напруги, дихання, тонусу, температури, рухливості або контакту із собою.\n\n"
            "Про що це може бути:\n"
            "Часто такі стани пов’язані зі стосунками, досвідом, уявленням про себе, втомою, розчаруванням, надією або потребою в опорі."
        )

    await message.answer(
        text,
        reply_markup=emotion_dictionary_categories_menu()
    )

    # -------- PRACTICES --------
    @dp.message(F.text == "🌿 Практика на 1 хвилину")
    async def practice_menu_handler(message: Message):
        await message.answer(
            "Обереш практику:",
            reply_markup=practice_menu()
        )

    @dp.message(F.text.in_([
        "Заземлення",
        "Перед сном",
        "Кордони",
        "Активація енергії",
        "Зниження енергії",
        "Тілесний сканер",
        "Дихальні вправи",
    ]))
    async def empty_practice_stub(message: Message):
        await message.answer(
            "Ця практика скоро з’явиться 🤍",
            reply_markup=practice_menu()
        )

    # -------- SETTINGS --------
    @dp.message(F.text == "⚙️ Налаштування")
    async def settings(message: Message):
        await message.answer(
            "Налаштування поки в базовій версії.\n"
            "Тут уже можна видалити всі записи. "
            "Нагадування і час check-in додамо окремим етапом.",
            reply_markup=settings_menu()
        )

    @dp.message(F.text == "Видалити всі записи")
    async def delete_records(message: Message):
        all_data = load_data()
        filtered = [item for item in all_data if item.get("user_id") != message.from_user.id]
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        await message.answer(
            "Усі твої записи видалені.",
            reply_markup=settings_menu()
        )

    # -------- FALLBACK --------
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