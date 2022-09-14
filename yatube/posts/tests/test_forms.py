import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post(self):
        """Функция тестирует создание новой записи в базе данных
        при отправке валидной формы со страницы создания поста."""
        posts_before_create = list(Post.objects.values_list('id', flat=True))
        form_data = {
            'text': 'new test post',
            'author': self.post.author,
            'group': self.group.id,
            
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        posts_after_create = Post.objects.all().exclude(
            id__in=posts_before_create
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args={self.author.username})
        )
        for post in posts_after_create:
            self.assertEqual(post.text, form_data['text'])
            self.assertEqual(post.author, form_data['author'])
            self.assertEqual(post.group.id, form_data['group'])

    def test_edit_post(self):
        """Функция тестирует изменение поста с post_id в базе данных
        при отправке валидной формы со страницы редактирования поста."""
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
            reverse(
                'posts:post_edit',
                args=[self.post.id],
            ),
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

    def test_create_post_with_img(self):
        """
        Description.
        """
        posts_count = Post.objects.count()
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
        self.author_client.post(
            reverse(
                'posts:post_create',
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/pic.jpg'
            ).exists()
        )
