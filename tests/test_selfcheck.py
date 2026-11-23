from activity_tracker.selfcheck import run


def test_selfcheck_passes_on_a_clean_checkout():
    """Тот же прогон CI делает внутри собранного exe: миграции, БД, иконки."""
    assert run(check_gui_libs=False) == 0
