from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from ..constants import POST_COUNT, TEST_POST_COUNT


class PostPagesTests(TestCase):
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
            group=cls.group,
            text='test post',
        )

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_views_uses_correct_template(self):
        """Функция тестирует соответствие шаблонов для view-функций."""
        pages_names_templates = {
            reverse(
                'posts:index'
            ):
            'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.group.slug,
                }
            ):
            'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.author.username,
                }
            ):
            'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id,
                }
            ):
            'posts/post_detail.html',
        }
        for reverse_name, template in pages_names_templates.items():
            with self.subTest():
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        response = self.user_client.get(
            reverse('posts:post_create',)
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')
        response = self.author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': self.post.id,
                }
            )
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_correct_context(self):
        """Функция проверяет контекст, передаваемый
        в шаблон при вызове главной страницы."""
        response = self.client.get(
            reverse('posts:index')
        )
        index_context = response.context['page_obj'].object_list
        self.assertEqual(index_context, [self.post])

    def test_group_correct_context(self):
        """Функция тестирует контекст, передаваемый в
        шаблон при вызове страницы группы постов."""
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={
                    'slug': self.group.slug,
                }
            )
        )
        group_context = response.context['group']
        page_context = response.context['page_obj'].object_list
        self.assertEqual(group_context, self.group)
        self.assertEqual(page_context, [self.post])

    def test_profile_correct_context(self):
        """Функция тестирует контекст, передаваемый в
        шаблон при вызове страницы профиля пользователя."""
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.author.username,
                }
            )
        )
        author_context = response.context['author']
        page_context = response.context['page_obj'].object_list
        self.assertEqual(author_context, self.author)
        self.assertEqual(page_context, [self.post])

    def test_detail_correct_context(self):
        """Функция тестирует контекст, передаваемый в
        шаблон при вызове страницы поста."""
        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id,
                }
            )
        )
        post_context = response.context['post']
        self.assertEqual(post_context, self.post)

    def test_edit_correct_context(self):
        """Функция тестирует контекст, передаваемый в
        шаблон при вызове страницы редактирования поста."""
        response = self.author_client.get(
            reverse(
                'posts:post_edit',
                kwargs={
                    'post_id': (self.post.id),
                }
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest():
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertTrue(response.context.get('is_edit'))
                self.assertEqual(response.context.get('post'), self.post)

    def test_create_correct_context(self):
        """Функция тестирует контекст, передаваемый
        в шаблон при вызове страницы создания поста."""
        response = self.user_client.get(
            reverse(
                'posts:post_create',
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest():
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_location(self):
        """Функция тестирует отображение поста на главной, странице профайла
        и странице группы, если при создании поста была указана группа."""
        new_group = Group.objects.create(
            title='new test title',
            slug='new-test-slug',
            description='new description'
        )
        test_post = Post.objects.create(
            author=self.author,
            group=new_group,
            text='new post'
        )

        locations = (
            (
                'posts:index',
                {
                },
            ),
            (
                'posts:profile',
                {
                    'username': (test_post.author.username),
                },
            ),
            (
                'posts:group_list',
                {
                    'slug': (test_post.group.slug),
                },
            ),
            (
                'posts:group_list',
                {
                    'slug': (self.group.slug),
                },
            ),
        )
        for address, kwargs in locations:
            response = self.client.get(reverse(address, kwargs=kwargs))
            page_obj_context = response.context['page_obj'].object_list
            with self.subTest():
                if kwargs == {'slug': self.group.slug}:
                    self.assertNotEqual(test_post, page_obj_context[0])
                else:
                    self.assertEqual(test_post, page_obj_context[0])

    def test_paginator(self):
        """Тестирование паджинатора."""
        test_posts = [
            Post(
                text=f'test paginator text {i}',
                group=self.group,
                author=self.author,
            ) for i in range(TEST_POST_COUNT)
        ]
        Post.objects.bulk_create(test_posts)
        paginator_pages = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author.username}/',
        )

        for pages in paginator_pages:
            response = self.client.get(pages)
            page_context = response.context['page_obj'].object_list
            with self.subTest():
                self.assertEqual(len(page_context), POST_COUNT)
                p_2 = self.client.get((pages) + '?page=2')
                if response == p_2.context['page_obj'].object_list:
                    self.assertEqual(len(page_context),
                                     TEST_POST_COUNT - POST_COUNT)
