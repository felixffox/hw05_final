import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms

from posts.models import Group, Post, Comment
from posts.models import Follow

User = get_user_model()

TESTS_POSTS_NUM = 13

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group_1 = Group.objects.create(
            title='Test-group',
            slug='test-slug',
            description='Test-description',
        )
        cls.group_2 = Group.objects.create(
            title='Test-group-2',
            slug='test-slug-2',
            description='Test-description-2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test-post',
            group=cls.group_1,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            text='Test-text',
            author=cls.user,
            post=cls.post
        )
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': 'HasNoName'}),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}),
            'posts/create_post.html': reverse(
                'posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        template = 'posts/create_post.html'
        reverse_name = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        )
        with self.subTest(reverse_name=reverse_name):
            response = self.authorized_client.get(reverse_name)
            self.assertTemplateUsed(response, template)

    def test_index_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post_object = response.context['page_obj'][0]
        post_text_0 = post_object.text
        post_author_0 = post_object.author.username
        post_group_0 = post_object.group.title
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_text_0, 'Test-post')
        self.assertEqual(post_author_0, 'HasNoName')
        self.assertEqual(post_group_0, 'Test-group')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_cache_index(self):
        test_post = Post.objects.create(
            text='some text',
            author=self.user,
            group=self.group_1
        )
        count_posts = Post.objects.count()
        self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(count_posts, 2)

        test_post.delete()
        cache.clear()

        count_posts = Post.objects.count()
        self.assertEqual(count_posts, 1)

    def test_group_list_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        post_object = response.context['page_obj'][0]
        post_text_0 = post_object.text
        post_author_0 = post_object.author.username
        post_group_0 = post_object.group.title
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_text_0, 'Test-post')
        self.assertEqual(post_author_0, 'HasNoName')
        self.assertEqual(post_group_0, 'Test-group')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_profile_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'HasNoName'}))
        post_object = response.context['page_obj'][0]
        post_text_0 = post_object.text
        post_author_0 = post_object.author.username
        post_group_0 = post_object.group.title
        post_image_0 = Post.objects.first().image
        self.assertEqual(post_text_0, 'Test-post')
        self.assertEqual(post_author_0, 'HasNoName')
        self.assertEqual(post_group_0, 'Test-group')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_post_detail_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_object = response.context['post']
        post_text_0 = post_object.text
        post_author_0 = post_object.author.username
        post_group_0 = post_object.group.title
        post_image_0 = Post.objects.first().image
#        post_comment_0 = Comment.objects.create()
        self.assertEqual(post_text_0, 'Test-post')
        self.assertEqual(post_author_0, 'HasNoName')
        self.assertEqual(post_group_0, 'Test-group')
        self.assertEqual(post_image_0, 'posts/small.gif')
#        self.assertEqual(post_comment_0, 'Test-text')

    def test_post_create_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_post_on_pages(self):
        list_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
        )
        for tested_url in list_urls:
            response = self.authorized_author.get(tested_url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_post_no_in_another_group(self):
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}))
        posts = response.context['page_obj'].object_list
        self.assertNotIn(self.post.pk, posts)

    def test_comment(self):
        form_data = {
            'text': 'Текст комментария',
        }
        response_guest = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ), data=form_data
        )
        response_user = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}
            ), data=form_data
        )
        self.assertEqual(response_guest.status_code, 302)
        self.assertEqual(response_user.status_code, 302)
        self.assertRedirects(
            response_guest,
            f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )
        self.assertRedirects(response_user, f'/posts/{self.post.pk}/')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FollowingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group_1 = Group.objects.create(
            title='Test-group',
            slug='test-slug',
            description='Test-description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test-post',
            group=cls.group_1,
        )
        cache.clear()

    def setUp(self):
        self.nonfollower = User.objects.create_user(username='nonfollower')
        self.nonfollower_client = Client()
        self.nonfollower_client.force_login(self.nonfollower)
        self.follower = User.objects.create_user(username='follower')
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.author = Client()
        self.author.force_login(self.post.author)
        self.follow_object = Follow.objects.create(
            user=self.follower,
            author=self.post.author
        )
        cache.clear()

    def test_user_can_subscribe(self):
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_user_can_unsubscribe(self):
        self.follow_object.delete()
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_following_post_in_feed(self):
        Follow.objects.create(
            user=self.follower,
            author=User.objects.create_user(username='author')
        )
        response = self.follower_client.get('/follow/')
        post_text_0 = response.context['page_obj'][0].text
        self.assertEqual(post_text_0, 'Test-post')
        # в качестве неподписанного пользователя проверяем собственную ленту
        response = self.nonfollower_client.get('/follow/')
        self.assertNotContains(response, 'Test-post')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Test-title',
            slug='test-slug',
            description='Test-description',
        )
        cls.post = []
        for i in range(TESTS_POSTS_NUM):
            cls.post.append(
                Post.objects.create(
                    author=cls.user,
                    text=f'Test-text {i}',
                    group=cls.group,
                )
            )
        cache.clear()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_paginator_first_page(self):
        reverse_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
        ]
        for reverse_name in reverse_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_second_page(self):
        reverse_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'HasNoName'}),
        ]
        for reverse_name in reverse_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_new_post(self):
        post_0 = Post.objects.create(
            author=User.objects.create_user(username='Test-User'),
            text='Test-text',
            group=Group.objects.last()
        )
        reverse_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'Test-User'}),
        ]
        for reverse_name in reverse_list:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                posts = response.context['page_obj'].object_list

                posts_ids = []
                for post in posts:
                    posts_ids.append(post.id)
                self.assertIn(post_0.id, posts_ids)
