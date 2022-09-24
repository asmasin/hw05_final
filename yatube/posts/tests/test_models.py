from django.test import TestCase

from ..constants import TEST_TEXT_COUNT
from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug ',
            description='test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test post longer than 15 characters',
        )

    def test_models_have_correct_object_names(self):
        """
        Функция тестирует правильное отображение
        значение поля __str__ в объекте модели.
        """
        expected_values = (
            (
                self.group.title,
                str(self.group)
            ),
            (
                self.post.text[:TEST_TEXT_COUNT],
                str(self.post)
            ),
        )
        for expected_value, received_value in expected_values:
            with self.subTest():
                self.assertEqual(expected_value, received_value)
