from maxapi.types.attachments.attachment import ButtonsPayload
from maxapi.types.attachments.buttons import CallbackButton


def kb_auth_role():
    """Выбор роли при регистрации"""
    buttons = [
        [
            CallbackButton(text="🎓 Я Студент", payload="reg:student"),
            CallbackButton(text="👨‍🏫 Я Преподаватель", payload="reg:teacher")
        ]
    ]
    return ButtonsPayload(buttons=buttons).pack()

def kb_student_menu():
    """Меню студента"""
    buttons = [
        [CallbackButton(text="📝 Получить задание", payload="menu:get_task")],
        [CallbackButton(text="📊 Мои результаты", payload="menu:grades")],
        [CallbackButton(text="💬 Чат с AI", payload="menu:chat")],
        [CallbackButton(text="🗑️ Удалить пользователя", payload="menu:reset_account")]
    ]
    return ButtonsPayload(buttons=buttons).pack()

def kb_teacher_menu():
    """Меню преподавателя"""
    buttons = [
        [CallbackButton(text="➕ Создать задание", payload="menu:create_task")],
        [CallbackButton(text="👀 Проверить работы", payload="menu:check")],
        [CallbackButton(text="💬 Чат с AI", payload="menu:chat")],
        [CallbackButton(text="🗑️ Удалить пользователя", payload="menu:reset_account")]
    ]
    return ButtonsPayload(buttons=buttons).pack()

def kb_choose_discipline(disciplines):
    """Меню дисциплин преподавателя"""
    buttons = []
    # Добавляем существующие дисциплины
    for disc in disciplines:
        buttons.append([CallbackButton(text=disc.name, payload=f"disc_select:{disc.id}")])
    
    # Кнопка для создания новой
    buttons.append([CallbackButton(text="➕ Создать новую дисциплину", payload="disc_create_new")])
    return ButtonsPayload(buttons=buttons).pack()

def kb_test_options(options):
    """Меню выбора ответа"""
    buttons = []
    for opt in options:
        # Ограничим длину текста на кнопке, если нужно
        buttons.append([CallbackButton(text=str(opt), payload=f"answer:{opt}")])
    return ButtonsPayload(buttons=buttons).pack()

def kb_student_choose_discipline(disciplines):
    """Меню дисциплин студента"""
    buttons = []
    for disc in disciplines:
        buttons.append([CallbackButton(text=disc.name, payload=f"st_disc_select:{disc.id}")])
    return ButtonsPayload(buttons=buttons).pack()