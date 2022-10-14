import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Group, Post
from django.test import Client, TestCase, override_settings
from django.urls import reverse


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Test-user')
        cls.group = Group.objects.create(
            title='Test-title',
            slug='test-slug',
            description='Test-description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test-text',
            group=cls.group
        )
        cls.form = PostCreateForm()
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)
        cache.clear()

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Test-text',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.post.author}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.user.id,
                text='Test-text',
                group=self.group.id
            ).exists()
        )

    def test_edit_post(self):
        posts_count = Post.objects.count()
        old_post = Post.objects.get(pk=self.post.id)
        another_group = Group.objects.create(
            title='Test-title-2',
            slug='test-slug-2'
        )
        form_data = {
            'text': 'Test-text',
            'group': another_group.pk,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', args=(self.post.id, )),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            )
        )
        new_post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(old_post.author, self.post.author)
        self.assertTrue(new_post.text == form_data['text'])
        self.assertTrue(new_post.group.pk == form_data['group'])

    def test_post_with_picture(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Test-text',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.post.author}
        )
        )
        self.assertTrue(
            Post.objects.filter(
                author=self.user.id,
                text='Test-text',
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )
