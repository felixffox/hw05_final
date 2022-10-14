from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user_2 = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Test-group',
            slug='test-slug',
            description='Test-description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test-post',
        )
        cache.clear()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)
        user_author = PostURLTest.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(user_author)
        cache.clear()

    def test_home_url(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_url(self):
        response = self.guest_client.get('/group/test-slug/')
        self.assertEqual(response.status_code, 200)

    def test_profile_url(self):
        response = self.authorized_client.get(
            '/profile/HasNoName',
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_post_url(self):
        response = self.guest_client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, 200)

    def test_unexisting_url(self):
        response = self.guest_client.get('/unexisting_page')
        self.assertEqual(response.status_code, 404)

    def test_create_post_url(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_edit_post_url(self):
        response = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, 200)

    def test_guest_create_redirect(self):
        response = self.guest_client.get('/create/')
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_guest_edit_redirect(self):
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_authorized_client_not_author_edit_redirect(self):
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(response, f'/posts/{self.post.id}/')

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_auth(self):
        templates_url_names = {
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)
