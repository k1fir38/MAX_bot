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