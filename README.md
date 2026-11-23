# Activity Tracker

Следит за клавиатурой и мышью. Если ты пользовался **и тем и другим**, а потом **10 минут ничего не трогал**,
показывает окно: выбери проект, напиши комментарий, нажми «Изучил» / «Выполнил» / «Просто гуглил».
Записи сохраняются в SQLite. Сами нажатые клавиши **не записываются**, только факт активности.

## Журнал

Главное окно показывает все записи и позволяет с ними работать:

- **Фильтры:** проект, тип, период (`ДД.ММ.ГГГГ`, кнопки «Сегодня» / «7 дней»), поиск по комментарию и проекту.
- **Таблица:** дата, время, длительность, проект, тип, комментарий. Внизу итог: число записей и суммарное время
  (пропущенные не учитываются). Выбранная запись показывает полный комментарий.
- **«Добавить запись…»:** ручное добавление, в том числе задним числом (проект, тип, начало, конец, комментарий).
- **«Удалить выбранную»** (или клавиша Delete): с подтверждением.
- Крестик **сворачивает** окно, трекер продолжает работать. Полностью выйти можно кнопкой «Выйти из трекера».

## Установка и запуск

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m activity_tracker                 # трекер + окно журнала
python -m activity_tracker --minimized     # то же, но журнал стартует свёрнутым
```

При старте автоматически применяются миграции Alembic. База по умолчанию: `~/.activity_tracker/tracker.db`.

| Переменная                       | Что делает                                              |
|----------------------------------|---------------------------------------------------------|
| `ACTIVITY_TRACKER_DB_URL`        | другой URL БД, например `sqlite:////tmp/test.db`        |
| `ACTIVITY_TRACKER_IDLE_SECONDS`  | сколько секунд бездействия ждать (по умолчанию 600)     |

macOS: дай терминалу доступ в «Конфиденциальность → Универсальный доступ / Мониторинг ввода».
Linux: работает под X11, на Wayland глобальный перехват ввода ограничен.

## Архитектура (DDD)

```
src/activity_tracker/
├── domain/            чистая бизнес-логика, без зависимостей от БД и UI
│   ├── model.py         Project, ActivityEntry, ActivityKind (+ инварианты)
│   ├── queries.py       EntryFilter (правила фильтрации), EntryView (строка журнала)
│   ├── tracker.py       ActivityTracker: «пора ли спрашивать» (время передаётся снаружи)
│   ├── repositories.py  порты: ProjectRepository, EntryRepository
│   └── errors.py
├── application/       сценарии использования
│   ├── services.py      TrackerService (record_entry, add_manual_entry, search_entries,
│   │                    delete_entry, record_skipped, list_projects)
│   └── unit_of_work.py  порт UnitOfWork
├── infrastructure/    адаптеры к внешнему миру
│   ├── db/              SQLAlchemy: orm.py (маппинг), repositories.py, unit_of_work.py,
│   │                    database.py, migrations/ (Alembic)
│   └── input/monitor.py pynput → ActivityTracker
└── ui/                Tkinter и вспомогательный код
    ├── journal.py       окно журнала        ├── parsing.py     разбор дат (без tkinter)
    ├── entry_form.py    форма добавления    ├── formatting.py  строки таблицы (без tkinter)
    ├── dialog.py        вопрос после паузы  └── app.py         composition root
```

Зависимости направлены внутрь: `ui/infrastructure → application → domain`. Доменные классы ничего не знают
про SQLAlchemy: маппинг императивный (`orm.py`). Правила валидации («для работы нужны проект и комментарий»)
живут в домене, окно просто показывает его `ValidationError`.

## Тесты (TDD)

```bash
pytest
```

- `tests/domain`: чистые unit-тесты, мгновенные.
- `tests/application`: сценарии на in-memory фейках (`fakes.py`), без БД.
- `tests/ui`: разбор дат и форматирование (чистые функции, без tkinter).
- `tests/infrastructure`: реальный SQLite во временной папке; схема создаётся **миграциями**.
  Отдельный тест падает, если модели изменились, а миграцию забыли создать.

Рабочий цикл: пишешь падающий тест → минимальный код → рефакторинг. Новое правило начинай с `tests/domain`.

## Миграции (Alembic)

Поменял таблицу в `infrastructure/db/orm.py`, затем:

```bash
alembic revision --autogenerate -m "add something"   # проверь сгенерированный файл!
alembic upgrade head
alembic downgrade -1
alembic current
```

## Полезные запросы

```sql
-- время по проектам и видам активности (в минутах)
SELECT p.name, e.kind, COUNT(*) AS записей,
       ROUND(SUM((julianday(e.ended_at) - julianday(e.started_at)) * 1440)) AS минут
FROM entries e JOIN projects p ON p.id = e.project_id
GROUP BY p.name, e.kind;
```

Значения `kind`: `learned`, `done`, `browsing`, `skipped`.
