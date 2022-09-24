import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='hasnoname')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='test post',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post(self):
        """
        Функция тестирует создание новой записи в базе данных
        при отправке валидной формы со страницы создания поста.
        """
        posts_before_create = list(Post.objects.values_list('id', flat=True))
        pic = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='pic.jpg',
            content=pic,
            content_type='image/jpg',
        )
        form_data = {
            'text': 'test post',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        posts_after_create = Post.objects.exclude(
            id__in=posts_before_create
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args={self.author.username})
        )
        if len(posts_after_create) == 1:
            for post in posts_after_create:
                self.assertEqual(form_data['text'], post.text)
                self.assertEqual(form_data['group'], post.group.id)
                self.assertTrue(
                    Post.objects.filter(
                        text=form_data['text'],
                        group=form_data['group'],
                        image='posts/pic.jpg',
                    ).exists()
                )

    def test_edit_post(self):
        """
        Функция тестирует изменение поста с post_id в базе данных
        при отправке валидной формы со страницы редактирования поста.
        """
        posts_count = Post.objects.count()
        new_group = Group.objects.create(
            title='new test title',
            slug='new-test-slug',
            description='new test description'
        )
        form_data = {
            'text': 'test post',
            'group': new_group.id,
        }
        self.author_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            flow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                group=form_data['group'],
                text=form_data['text'],
            ).exists()
        )

    def test_authorized_user_post_comment(self):
        """
        Функция тестирует отправку комментариев
        с формы авторизованными пользователями.
        """
        comments_before_create = list(
            Comment.objects.values_list('id', flat=True)
        )
        comment = 'test comment'
        self.user_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data={'text': comment},
            follow=True,
        )
        comments_after_create = Comment.objects.all().exclude(
            id__in=comments_before_create
        ).count()
        self.assertEqual(comments_after_create, self.post.comments.count())
        self.assertTrue(self.post.comments.filter(text=comment).exists())

    def test_guest_user_cant_post_comment(self):
        """
        Функция тестирует отправку комментариев
        с формы неавторизованными пользователями.
        """
        comment = 'test comment'
        comments_count_before = self.post.comments.count()
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data={'text': comment},
            follow=True,
        )
        self.assertEqual(comments_count_before, self.post.comments.count())
        self.assertFalse(self.post.comments.filter(text=comment).exists())
