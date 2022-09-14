import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..constants import POST_COUNT, TEST_POST_COUNT
from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(
            TEMP_MEDIA_ROOT,
            ignore_errors=True,
        )

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)
        cache.clear()

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
        Post.objects.all().delete()
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
            page1_context = self.client.get(
                pages,
            ).context['page_obj'].object_list
            with self.subTest():
                self.assertEqual(len(page1_context), POST_COUNT)
            page2_context = self.client.get(
                (pages) + '?page=2'
            ).context['page_obj'].object_list
            with self.subTest():
                self.assertEqual(
                    len(page2_context),
                    TEST_POST_COUNT - POST_COUNT
                )

    def test_post_with_image(self):
        """"""
        pic = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        upload = SimpleUploadedFile(
            name='pic.jpg',
            content=pic,
            content_type='image/jpg',
        )
        post_with_pic = Post.objects.create(
            author=self.author,
            group=self.group,
            text='test post',
            image=upload,
        )
        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': post_with_pic.id,
                }
            )
        )
        post_context = response.context['post']
        self.assertEqual(post_context, post_with_pic)
        urls = {
            'posts:index': {},
            'posts:group_list': {
                'slug': post_with_pic.group.slug,
            },
            'posts:profile': {
                'username': (post_with_pic.author.username)
            }
        }
        for url, kwargs in urls.items():
            with self.subTest():
                response = self.client.get(
                    reverse(
                        url,
                        kwargs=kwargs,
                    )
                )
                page_obj_context = response.context['page_obj'].object_list
                self.assertIn(post_with_pic, page_obj_context)

    def test_cache(self):
        """"""
        test_post = Post.objects.create(
            author=self.author,
            group=self.group,
            text='test post cache',
        )
        new_post = self.client.get(
            reverse(
                'posts:index',
            )
        ).content
        test_post.delete()
        new_post_deleted = self.client.get(
            reverse(
                'posts:index',
            )
        ).content
        cache.clear()
        clear_cache = self.client.get(
            reverse(
                'posts:index'
            )
        ).content
        self.assertEqual(new_post, new_post_deleted)
        self.assertNotEqual(new_post, clear_cache)

    def test_authorized_user_post_comment(self):
        """"""
        comments_before_create = list(
            Comment.objects.values_list(
                'id',
                flat=True,
            )
        )
        comment = 'test comment'
        self.user_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.id,
                },
            ),
            data={
                'text': comment,
            },
            follow=True,
        )
        comments_after_create = Comment.objects.all().exclude(
            id__in=comments_before_create
        ).count()
        self.assertEqual(comments_after_create, self.post.comments.count())
        self.assertTrue(self.post.comments.filter(text=comment).exists())

    def test_guest_user_post_comment(self):
        """"""
        comment = 'test comment'
        comments_count_before = self.post.comments.count()
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.id,
                },
            ),
            data={
                'text': comment,
            },
            follow=True,
        )
        self.assertEqual(comments_count_before, self.post.comments.count())
        self.assertFalse(self.post.comments.filter(text=comment).exists())

    def test_comment_correct_context(self):
        """"""
        comment = 'test comment'
        self.user_client.post(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.id,
                }
            ),
            data={
                'text': comment,
            },
            follow=True,
        )
        response = self.user_client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': self.post.id,
                }
            )
        )
        comment = response.context['comments'].filter(text=comment)
        self.assertTrue(comment.exists())

    def test_subscribe(self):
        """"""
        self.user_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={
                    'username': self.author.username,
                }
            )
        )
        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.author,
        ).exists()
        )

    def test_unsubscribe(self):
        """"""
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        self.user_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={
                    'username': self.author.username
                }
            )
        )
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.author,
        ).exists()
        )

    def test_new_posts_in_subscribers_(self):
        """"""
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        new_post = Post.objects.create(
            author=self.author,
            text='test post',
        )
        response = self.user_client.get(
            reverse(
                'posts:follow_index',
            )
        )
        page_obj_context = response.context['page_obj'].object_list
        self.assertIn(new_post, page_obj_context)

    def test_no_new_posts_in_not_subscribers_feed(self):
        """"""
        new_post = Post.objects.create(
            author=self.author,
            text='test post',
        )
        response = self.user_client.get(
            reverse(
                'posts:follow_index',
            )
        )
        page_obj_context = response.context['page_obj'].object_list
        self.assertNotIn(new_post, page_obj_context)
