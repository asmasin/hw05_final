from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User


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

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post(self):
        """Функция тестирует создание новой записи в базе данных
        при отправке валидной формы со страницы создания поста."""
        qs = list(Post.objects.values_list('id', flat=True))
        form_data = {
            'text': 'new test post',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        diff_qs = Post.objects.all().exclude(id__in=qs)
        self.assertRedirects(response, reverse(
            'posts:profile',
            args={self.author.username})
        )
        if len(diff_qs) == 1:
            new_post = diff_qs[0]
            self.assertEqual(new_post.group.id, form_data['group'])
            self.assertEqual(new_post.text, form_data['text'])

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
