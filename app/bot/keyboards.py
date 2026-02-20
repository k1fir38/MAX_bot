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
        [CallbackButton(text="📋 Мои задания", payload="menu:manage_assignments")],
        [CallbackButton(text="👀 Проверить работы", payload="menu:check")],
        [CallbackButton(text="💬 Чат с AI", payload="menu:chat")],
        [CallbackButton(text="🗑️ Удалить пользователя", payload="menu:reset_account")]
    ]
    return ButtonsPayload(buttons=buttons).pack()

def kb_teacher_assignments(assignments):
    """Список заданий учителя"""
    buttons = []
    for task in assignments:
        # Текст: Название (Группа). Payload: id задания
        buttons.append([CallbackButton(
            text=f"{task.title} ({task.target_group})", 
            payload=f"task_manage:{task.id}"
        )])
    return ButtonsPayload(buttons=buttons).pack()

def kb_confirm_delete_task(task_id):
    """Подтверждение удаления конкретного задания"""
    buttons = [
        [CallbackButton(text="🔥 Да, удалить навсегда", payload=f"task_del_yes:{task_id}")],
        [CallbackButton(text="❌ Отмена", payload="menu:manage_assignments")]
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

def kb_get_ai_role():
    buttons = [
        [
            CallbackButton(text="💻 Программист", payload="ai_role:coder"),
            CallbackButton(text="🎓 Учитель", payload="ai_role:teacher")
        ],
        [
            CallbackButton(text="🇬🇧 English", payload="ai_role:english"),
            CallbackButton(text="🍕 Друг", payload="ai_role:friend")
        ],
        [
            CallbackButton(text="♻️ Обычный помощник", payload="ai_role:default")
        ]
    ]
    return ButtonsPayload(buttons=buttons).pack()

def kb_confirm_reset():
    buttons = [
        [CallbackButton(text="✅ Да, сбросить всё", payload="reset:confirm")],
        [CallbackButton(text="❌ Отмена", payload="reset:cancel")]
    ]
    return ButtonsPayload(buttons=buttons).pack()

def kb_manage_single_assignment(task_id, title, group):
    buttons = [
        [
            CallbackButton(text="📝 Просмотр JSON", payload=f"task_view:{task_id}"),
            CallbackButton(text="🗑 Удалить", payload=f"task_del:{task_id}")
        ],
        [
            CallbackButton(text="⬅️ Назад к списку", payload="menu:manage_assignments")
        ]
    ]
    return ButtonsPayload(buttons=buttons).pack()

def kb_student_assignments_list(tasks):
    """Клавиатура со списком доступных тестов для студента"""
    buttons = []
    for task in tasks:
        # Текст: Название задания. Payload: st_task_select:ID
        buttons.append([CallbackButton(text=f"📝 {task.title}", payload=f"st_task_select:{task.id}")])
    
    buttons.append([CallbackButton(text="⬅️ Назад к предметам", payload="menu:get_task")])
    return ButtonsPayload(buttons=buttons).pack()