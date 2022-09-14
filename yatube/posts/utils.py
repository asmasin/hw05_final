from django.core.paginator import Paginator

from .constants import POST_COUNT


def page_nav(request, posts):
    """Функция которая делит контент по страницам
    и создает постраничную навигацию.
    Принимает на вход запрос и данные пост ов,
    возвращает объект страницы"""
    paginator = Paginator(posts, POST_COUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
