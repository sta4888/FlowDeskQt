class DomainError(Exception):
    """Базовая ошибка предметной области."""


class ValidationError(DomainError):
    """Нарушено бизнес-правило. Текст ошибки можно показывать пользователю."""
