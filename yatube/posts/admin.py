from django.contrib import admin

from .models import Group, Post


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """
    Класс, описывающий отображаемые поля в админке для модели Group,
    list_display        - список полей для отображения,
    search_fields       - поле по которому работает поиск,
    empty_value_display - название по-умолчания для пустых полей.
    """

    list_display = (
        'pk',
        'title',
        'slug',
        'description',
    )
    search_fields = (
        'title',
    )
    empty_value_display = "-пусто-"


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Класс, описывающий отображаемые поля в админке для модели Post,
    list_display        - список полей для отображения,
    list_editable       - поле, которое редактируется в списке,
    search_fields       - поле по которому работает поиск,
    list_filter         - поле по которому установлена сортировка списка,
    empty_value_display - название по-умолчания для пустых полей.
    """

    list_display = (
        'pk',
        'text',
        'group',
        'pub_date',
        'author',
    )
    list_editable = (
        'group',
    )
    search_fields = (
        'text',
    )
    list_filter = (
        'pub_date',
    )
    empty_value_display = '-пусто-'
