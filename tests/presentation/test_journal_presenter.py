from datetime import date, datetime

import pytest

from activity_tracker.application.services import TrackerService
from activity_tracker.domain.errors import ValidationError
from activity_tracker.domain.model import ActivityKind
from activity_tracker.presentation.journal_presenter import JournalPresenter
from activity_tracker.presentation.journal_view import ALL, FilterInput

from ..application.fakes import FakeUnitOfWork
from .fakes import FakeView

NOW = datetime(2026, 11, 23, 18, 0)
TODAY = NOW.date()


def when(day, hour=10):
    return datetime(2026, 11, day, hour, 0)


@pytest.fixture
def uow():
    return FakeUnitOfWork()


@pytest.fixture
def service(uow):
    service = TrackerService(lambda: uow, clock=lambda: NOW)
    service.add_manual_entry("Alembic", ActivityKind.LEARNED, "читал доки", when(20), when(20, 11))
    service.add_manual_entry("Трекер", ActivityKind.DONE, "написал окно\nжурнала", when(22), when(22, 12))
    service.add_manual_entry("", ActivityKind.BROWSING, "", when(23), when(23, 11))
    return service


@pytest.fixture
def view():
    return FakeView()


@pytest.fixture
def presenter(service, view):
    presenter = JournalPresenter(service, view, today=lambda: TODAY, now=lambda: NOW)
    presenter.start()
    return presenter


def projects_of(view):
    return [row.cells[3] for row in view.rows]


def test_start_shows_everything_newest_first_with_summary(presenter, view):
    assert projects_of(view) == ["—", "Трекер", "Alembic"]
    assert view.status == ("Записей: 3 · Время: 4 ч 00 мин", False)
    assert view.details == ""


def test_start_offers_all_plus_known_projects(presenter, view):
    assert view.project_choices[0] == ALL
    assert set(view.project_choices[1:]) == {"Alembic", "Трекер"}


def test_filter_by_project(presenter, view):
    presenter.on_inputs_changed(FilterInput(project="Alembic"))

    assert projects_of(view) == ["Alembic"]
    assert view.status == ("Записей: 1 · Время: 1 ч 00 мин", False)


def test_filter_by_kind_label(presenter, view):
    presenter.on_inputs_changed(FilterInput(kind="Выполнил"))

    assert projects_of(view) == ["Трекер"]


def test_filter_by_text_and_date(presenter, view):
    presenter.on_inputs_changed(FilterInput(text="ДОКИ"))
    assert projects_of(view) == ["Alembic"]

    presenter.on_inputs_changed(FilterInput(date_from="22.11.2026"))
    assert projects_of(view) == ["—", "Трекер"]


def test_invalid_date_shows_error_and_keeps_previous_rows(presenter, view):
    calls_before = view.show_rows_calls

    presenter.on_inputs_changed(FilterInput(date_from="мусор"))

    assert view.status[1] is True and "ДД.ММ.ГГГГ" in view.status[0]
    assert view.show_rows_calls == calls_before
    assert len(view.rows) == 3


def test_reversed_date_range_shows_error(presenter, view):
    presenter.on_inputs_changed(FilterInput(date_from="23.11.2026", date_to="01.11.2026"))

    assert view.status[1] is True


def test_selecting_row_shows_full_comment_and_clearing_hides_it(presenter, view):
    tracker_id = view.rows[1].id

    presenter.on_selection_changed(tracker_id)
    assert view.details == "написал окно\nжурнала"

    presenter.on_selection_changed(None)
    assert view.details == ""


def test_row_cells_flatten_multiline_comment(presenter, view):
    assert view.rows[1].cells[5] == "написал окно журнала"


def test_preset_today(presenter, view):
    presenter.preset_today()

    assert (view.inputs.date_from, view.inputs.date_to) == ("23.11.2026", "23.11.2026")
    assert projects_of(view) == ["—"]


def test_preset_week_covers_last_seven_days_including_today(presenter, view):
    presenter.preset_week()

    assert (view.inputs.date_from, view.inputs.date_to) == ("17.11.2026", "23.11.2026")
    assert len(view.rows) == 3


def test_reset_filters_restores_defaults(presenter, view):
    presenter.on_inputs_changed(FilterInput(project="Alembic", text="x"))

    presenter.reset_filters()

    assert view.inputs == FilterInput()
    assert len(view.rows) == 3


class TestDelete:
    def test_confirmed_delete_removes_entry(self, presenter, view):
        victim = view.rows[0].id

        presenter.delete_entry(victim)

        assert victim not in [row.id for row in view.rows]
        assert len(view.rows) == 2

    def test_declined_delete_keeps_entry(self, presenter, view):
        view.confirm_answer = False

        presenter.delete_entry(view.rows[0].id)

        assert len(view.rows) == 3

    def test_nothing_selected_does_not_even_ask(self, presenter, view):
        presenter.delete_entry(None)

        assert view.confirm_calls == 0


class TestAddEntry:
    def test_form_gets_projects_and_sensible_defaults(self, presenter, view):
        presenter.add_entry()

        projects, defaults = view.new_entry_request
        assert set(projects) == {"Alembic", "Трекер"}
        assert defaults.start_text == "23.11.2026 17:30"
        assert defaults.end_text == "23.11.2026 18:00"
        assert defaults.kind_label == "Изучил"
        assert defaults.kind_labels == ("Изучил", "Выполнил", "Просто гуглил")
        assert defaults.project == projects[0]

    def test_saved_entry_appears_in_list_and_projects(self, presenter, view):
        def user_fills_form(submit):
            submit("Новый проект", "Выполнил", "сделал форму", "23.11.2026 09:00", "23.11.2026 09:45")
            return True

        view.on_new_entry = user_fills_form
        presenter.add_entry()

        assert "Новый проект" in projects_of(view)
        assert "Новый проект" in view.project_choices

    def test_submit_reports_bad_time_as_validation_error(self, presenter, view):
        errors = []

        def user_fills_form(submit):
            try:
                submit("П", "Выполнил", "x", "завтра", "23.11.2026 09:45")
            except ValidationError as exc:
                errors.append(str(exc))
            return False

        view.on_new_entry = user_fills_form
        presenter.add_entry()

        assert errors and "ДД.ММ.ГГГГ" in errors[0]
        assert len(view.rows) == 3  # ничего не сохранилось

    def test_submit_applies_domain_rules(self, presenter, view):
        def user_fills_form(submit):
            with pytest.raises(ValidationError):
                submit("", "Изучил", "комментарий", "23.11.2026 09:00", "23.11.2026 09:45")
            return False

        view.on_new_entry = user_fills_form
        presenter.add_entry()
