from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from .models import Post, Group, Follow
from django.http import response
from django.core.cache import cache
from django.core.cache.backends import locmem

User = get_user_model()


class TestStringMethods(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="nikita", email="nikita@nik.com", password="qwerty")
        self.post = Post.objects.create(text="Hello World", author=self.user)
        self.group = Group.objects.create(title="Happy", slug="happy", description="Good day")

    def test_profile(self):
        response = self.client.get("/nikita/")
        self.assertEqual(response.status_code, 200, msg="Ошибка создания профиля")

    def test_post_create(self):
        self.client.login(username="nikita", password="qwerty")
        response = self.client.post("/new/", {"text":"Hello World"})
        self.assertEqual(response.status_code, 302)
        response_one = self.client.get("/")
        self.assertContains(response_one, text="Hello World")

    def test_redirect(self):
        response = self.client.get("/new/")
        self.assertRedirects(response, "/auth/login/?next=/new/", status_code=302, target_status_code=200, msg_prefix="", fetch_redirect_response=True)

    def test_new_post_after_publication(self):
        self.client.login(username="nikita", password="qwerty")
        test_text = "Hello World-test"
        self.post = Post.objects.create(text=test_text, author=self.user)
        post_id = self.post.pk
        response = self.client.get("/")
        self.assertContains(response, test_text)
        response_one = self.client.get("/nikita/")
        self.assertContains(response, test_text)
        response_two = self.client.get("/nikita/{post_id}/")
        self.assertContains(response, test_text)

    def test_edit_post(self):
        self.client.login(username="nikita", password="qwerty")
        test_text = "Hello World-test-01"
        post_id = self.post.pk
        self.post = Post.objects.create(text=test_text, author=self.user)
        response = self.client.post("/nikita/{post_id}/edit/", {"text":"test_text"})
        self.assertEqual(response.status_code, 302)
        response_one = self.client.get("/")
        self.assertContains(response_one, test_text)
        response_two = self.client.get("/nikita/")
        self.assertContains(response_two, test_text)
        response_three =self.client.get("/nikita/{post_id}/")
        self.assertContains(response_three, test_text)

    def test_404(self):
        self.client.login(username="nikita", password="qwerty")
        response = self.client.get("/404/")
        self.assertEqual(response.status_code, 404)

    def test_page_with_img(self):
        self.client.login(username="nikita", password="qwerty")
        self.post = Post.objects.create(text="Hello World", author=self.user)
        post_id = self.post.pk
        with open("media/posts/katzen.jpg", "rb") as img:
            self.client.post(f"/nikita/{post_id}/edit/", {"author":self.user, "text":"add_image", "image":img})
        response = self.client.get(f"/nikita/{post_id}/")
        self.assertContains(response, text="img")

    def test_all_with_img(self):
        self.client.login(username="nikita", password="qwerty")
        self.group = Group.objects.create(title="Happy", slug="happy", description="Good day")
        self.post = Post.objects.create(text="Hello World", author=self.user, group=self.group)
        post_id = self.post.pk
        with open("media/posts/katzen.jpg", "rb") as img:
            self.client.post(f"/nikita/{post_id}/edit/", {"author":self.user, "group":self.group, "text":"add_image", "image":img})
        response = self.client.get("/")
        self.assertContains(response, text="img")
        response_one = self.client.get(f"/nikita/")
        self.assertContains(response_one, text="img")
        response_two = self.client.get("/group/happy")
        self.assertContains(response_two, text="img")

    def test_file_not_img(self):
        self.client.login(username="nikita", password="qwerty")
        self.post = Post.objects.create(text="Hello World", author=self.user)
        post_id = self.post.pk
        with open("media/posts/text.txt", "rb") as img:
            self.client.post(f"/nikita/{post_id}/edit/", {"author":self.user, "text":"add_image", "image":img})
        response = self.client.get(f"/nikita/{post_id}/")
        self.assertNotContains(response, text="img")

    def test_cache(self):
        self.client.login(username="nikita", password="qwerty")
        response = self.client.post('/new/', {'text': 'test text'}, follow=True)
        self.assertRedirects(response, '/')
        self.assertTrue(locmem._caches[''])
        cache.clear()
        self.assertFalse(locmem._caches[''])


    class TestSubscription(TestCase):
        def setUp(self):
            cache.clear()
            self.client = Client()
            self.follower = User.objects.create(
                username="follower",
                email="follower@follow.com",
                password="follower"
            )
            self.following = User.objects.create(
                username="following",
                email="following@follow.com",
                password="following"
            )

    def test_follow_unfollow(self):
        self.client.login(self.follower)
        self.post = Post.objects.create(text="Hello World", author=self.following)
        response = self.client.get(f"/{self.following}/follow/")
        self.assertRedirects(response, f"/{self.following}/", status_code=302)
        response_one = Follow.objects.filter(user=self.follower).exists()
        self.assertTrue(response_one)
        response_two = self.client.get(f"/{self.following}/unfollow/")
        self.assertRedirects(response_two, f"/{self.following}/", status_code=302,)
        response_three = Follow.objects.filter(user=self.follower).exists()
        self.assertFalse(response_three)

        
    def test_post_on_follow_page(self):
        self.text = "Hellow world"
        self.unfollower = User.objects.create(username="unfollower", email="unfollower@unfollow.ru", password="unfollower")
        self.client.login(self.follower)
        self.client.get(f"/{self.following}/follow/")
        self.post = Post.objects.create(text=self.text, author=self.following)
        response = self.client.get("/follow/")
        self.assertContains(response, self.text, status_code=200, html=False)
        self.client.logout()
        self.client.login(self.unfollower)
        response_one= self.client.get("/follow/")
        self.assertNotContains(response_one, self.text, html=False)


    def test_comments(self):
        response = self.client.get(f'/{self.random_user}/{self.post_create.id}/comment/')
        expected_url_one = f'/{self.random_user}/{self.post_create.id}/'
        self.assertRedirects(response, expected_url_one, status_code=302, target_status_code=200)
        self.client.logout()
        expected_url_two = f"/auth/login/?next=/{self.random_user}/{self.post_create.id}/comment/"
        self.assertRedirects(response, expected_url_two, status_code=302, target_status_code=200)

    def tearDown(self):
        print("The end testing")