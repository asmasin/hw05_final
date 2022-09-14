from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    """
    Функция добавляет возможность использовать фильтры,
    обрабатывающие переменные напрямую в шаблоне.
    """
    return field.as_widget(attrs={'class': css})
