from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    """
    Модель, описывающая поля БД для "Группы публикаций":
    title       - Название поста,
    slug        - Формат строки, улучшающий читаемость и seo-оптмизацию,
    description - Описание поста.
    Для каждого поля добавлены vebose-name.
    """

    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Slug-строка',
    )
    description = models.TextField(
        verbose_name='Описание',
    )

    def __str__(self):
        return self.title


class Post(models.Model):
    """
    Модель, описывающая поля БД для "Публикаций":
    text        - Текст публикации,
    pub_date    - Дата публикации,
    author      - Автор публикации,
    group       - Группа публикации.
    Для каждого поля добавлены vebose-name.
    """

    text = models.TextField(
        verbose_name='Текст публикации',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        verbose_name='Группа',
    )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = '-pub_date',
