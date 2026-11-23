# Activity Tracker

Следит за клавиатурой и мышью. Если ты пользовался **и тем и другим**, а потом **10 минут ничего не трогал**,
показывает окно: выбери проект, напиши комментарий, нажми «Изучил» / «Выполнил» / «Просто гуглил».
Записи сохраняются в SQLite. Сами нажатые клавиши **не записываются**, только факт активности.

## Установка и запуск

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[gui,dev]"
python -m activity_tracker                 # трекер + окно журнала
python -m activity_tracker --minimized     # журнал сразу прячется в трей
```

Готовый `ActivityTracker.exe` берётся из **Releases** репозитория (см. `docs/RELEASING.md`).

При старте автоматически применяются миграции Alembic. База: `~/.activity_tracker/tracker.db`,
лог: `~/.activity_tracker/tracker.log`.

| Переменная                       | Что делает                                              |
|----------------------------------|---------------------------------------------------------|
| `ACTIVITY_TRACKER_DB_URL`        | другая БД, например `sqlite:////tmp/test.db`            |
| `ACTIVITY_TRACKER_IDLE_SECONDS`  | сколько секунд бездействия ждать (по умолчанию 600)     |

macOS: дай терминалу доступ в «Конфиденциальность → Универсальный доступ / Мониторинг ввода».
Linux: работает под X11. Трей рассчитан в первую очередь на Windows.

## Журнал и трей

- Фильтры: проект, тип, период (`ДД.ММ.ГГГГ`, «Сегодня» / «7 дней»), поиск по комментарию и проекту.
- Таблица с итогами, полный комментарий выбранной записи, ручное добавление и удаление.
- **Крестик и кнопка «свернуть» прячут только окно журнала в трей.** Трекер продолжает работать.
  Значок в трее: клик (или «Открыть журнал») возвращает окно, «Выход» завершает программу.
- Окно-вопрос после паузы всегда появляется поверх всего, в трей не прячется.
- Если трей недоступен, окно просто сворачивается на панель задач.

Иконки (секундомер) лежат в `src/activity_tracker/assets/`, генерируются `python scripts/make_icons.py`.

## Архитектура

```
src/activity_tracker/
├── domain/            бизнес-правила, без зависимостей от БД и UI
│   ├── model.py         Project, ActivityEntry, ActivityKind (+ инварианты)
│   ├── tracker.py       ActivityTracker: «пора ли спрашивать» (время передаётся снаружи)
│   ├── queries.py       EntryFilter (правила фильтрации), EntryView (строка журнала)
│   └── repositories.py  порты хранилищ
├── application/       сценарии использования
│   ├── services.py      TrackerService
│   ├── unit_of_work.py  порт UnitOfWork
│   └── ports.py         порт ActivityMonitor (источник событий ввода)
├── presentation/      логика окон БЕЗ привязки к UI-библиотеке
│   ├── journal_presenter.py  вся логика журнала (фильтры, пресеты, добавление, удаление)
│   ├── journal_view.py       контракт JournalView + модели данных для экрана
│   ├── controller.py         цикл «опросил монитор → задал вопрос → сохранил»
│   ├── ports.py              порт TrayIcon
│   └── formatting.py, parsing.py   строки таблицы, разбор дат
├── infrastructure/    адаптеры
│   ├── db/              SQLAlchemy + Alembic (orm.py, repositories.py, unit_of_work.py, migrations/)
│   ├── input/monitor.py pynput → ActivityMonitor
│   ├── tray/pystray_tray.py   pystray → TrayIcon
│   └── logging_setup.py
├── ui/                Tkinter: ТОЛЬКО виджеты и склейка (tk_journal.py, dialog.py, entry_form.py, app.py)
└── selfcheck.py       проверка целостности сборки (--self-check)
```

Зависимости направлены внутрь: `ui, infrastructure → presentation → application → domain`.

## Как заменить БД или UI

**Другая SQL-база** (PostgreSQL, MySQL): поставь драйвер и задай `ACTIVITY_TRACKER_DB_URL`. Код не меняется,
миграции Alembic те же. **Не-SQL хранилище** (файл, Mongo, облако): реализуй `ProjectRepository`,
`EntryRepository` и `UnitOfWork` (порты в `domain/` и `application/`) и подставь в `ui/app.py`. Тесты
`tests/application` и `tests/presentation` при этом не меняются.

**Другой UI (Qt и т.п.):** переписывается только `ui/` (4 файла): реализовать `JournalView`, окно-вопрос
(функция `ask_question`), форму добавления и цикл (`QTimer` вызывает `controller.tick()`). Презентер,
контроллер, домен, БД, ввод и тесты остаются как есть. Трей: оставить pystray или реализовать порт `TrayIcon`
через `QSystemTrayIcon`.

## Тесты (TDD)

```bash
pytest
```

- `tests/domain`: чистые unit-тесты.
- `tests/application`: сценарии на in-memory фейках, без БД.
- `tests/presentation`: презентер и контроллер на фейковом View/мониторе, без tkinter.
- `tests/infrastructure`: реальный SQLite; схема создаётся **миграциями**; отдельный тест падает,
  если модели изменились, а миграцию забыли создать.
- `tests/test_selfcheck.py`: тот же прогон, что CI делает внутри собранного exe.

Цикл: падающий тест → минимальный код → рефакторинг. Новое правило начинай с `tests/domain`.

## Миграции (Alembic)

```bash
alembic revision --autogenerate -m "add something"   # проверь сгенерированный файл!
alembic upgrade head
alembic downgrade -1
```

## Сборка exe и релизы

```bash
pip install -e ".[gui,build]"
python scripts/build_exe.py            # dist/ActivityTracker.exe
dist/ActivityTracker.exe --self-check  # код выхода 0 = сборка цела
```

CI (`.github/workflows`): тесты на каждый push, релиз с exe по тегу `v*`. Про подпись и предупреждения
Windows: **`docs/RELEASING.md`**.
