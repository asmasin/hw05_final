from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class StaticPagesURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='test post',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticPagesURLTests.user)
        self.author_client = Client()
        self.author_client.force_login(StaticPagesURLTests.author)

    def test_urls(self):
        """
        Фунцкция тестирует доступность страниц
        с учетом прав доступа пользователя.
        """
        urls = (
            (
                '/',
                self.client,
                HTTPStatus.OK
            ),
            (
                f'/group/{self.group.slug}/',
                self.client,
                HTTPStatus.OK
            ),
            (
                '/create/',
                self.authorized_client,
                HTTPStatus.OK
            ),
            (
                f'/posts/{self.post.id}/edit/',
                self.author_client,
                HTTPStatus.OK
            ),
            (
                f'/profile/{self.author.username}/',
                self.client,
                HTTPStatus.OK
            ),
            (
                f'/posts/{self.post.id}/',
                self.client,
                HTTPStatus.OK
            ),
            (
                '/unexisting_page/',
                self.client,
                HTTPStatus.NOT_FOUND
            ),
        )

        for address, client, status in urls:
            with self.subTest():
                response = client.get(address)
                self.assertEqual(response.status_code, status)

    def test_tmpls(self):
        """
        Функция тестирует соответствие шаблонов страниц.
        """
        templates = (
            (
                '/',
                self.client,
                'posts/index.html'
            ),
            (
                f'/group/{self.group.slug}/',
                self.client,
                'posts/group_list.html'
            ),
            (
                '/create/',
                self.authorized_client,
                'posts/create_post.html'
            ),
            (
                f'/posts/{self.post.id}/edit/',
                self.author_client,
                'posts/create_post.html'
            ),
            (
                f'/profile/{self.author.username}/',
                self.client,
                'posts/profile.html'
            ),
            (
                f'/posts/{self.post.id}/',
                self.client,
                'posts/post_detail.html'
            ),
            (
                '/nonexist-page/',
                self.client,
                'core/404.html',
            ),
        )

        for address, client, template in templates:
            with self.subTest():
                response = client.get(address)
                self.assertTemplateUsed(response, template)

    def test_redirects(self):
        """
        Функция тестирует редиректы со страниц создания
        и редактирования поста, с учетом прав пользователя.
        """
        redirects = (
            (
                '/create/',
                self.client,
                '/auth/login/?next=/create/'
            ),
            (
                f'/posts/{self.post.id}/edit/',
                self.client,
                f'/auth/login/?next=/posts/{self.post.id}/edit/'
            ),
            (
                f'/posts/{self.post.id}/edit/',
                self.authorized_client,
                f'/posts/{self.post.id}/'
            ),
        )

        for address, client, redirect in redirects:
            with self.subTest():
                response = client.get(address)
                self.assertRedirects(response, redirect)
