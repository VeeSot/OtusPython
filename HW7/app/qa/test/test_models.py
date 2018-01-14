from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from profiles.models import Profile
from qa.models import Tags, Questions


class QuestionIndexViewTests(TestCase):
    def setUp(self):
        user = User.objects.create(username='Bob', email='bob@example.com')
        self.profile = Profile.objects.create(user=user)

    def test_get_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('questions'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There aren't questions")

    def test_create_question_without_tags(self):
        request_body = {'user': self.profile.user.pk, 'title': 'Foo', 'content': 'bar'}
        response = self.client.post(reverse('questions'), request_body)
        self.assertEqual(response.status_code, 201)

    def test_create_question_with_tags(self):
        tag1 = Tags.objects.create(name='foo')
        tag2 = Tags.objects.create(name='bar')
        request_body = {'user': self.profile.user.id, 'title': 'Foo', 'content': 'bar', 'tags': [tag1.id, tag2.id]}
        response = self.client.post(reverse('questions'), request_body)
        self.assertEqual(response.status_code, 201)

    def test_create_answer(self):
        alice = User.objects.create(username='Alice', email='alice@example.com')
        author = Profile.objects.create(user=alice)
        q = Questions.objects.create(user=author,
                                     title='What is meaning of life',
                                     content='Do you have any ideas about it')

        request_body = {'question': q.id, 'content': 'Erm...is it 42?'}
        response = self.client.post(reverse('questions') + str(q.id), request_body)
        self.assertEqual(response.status_code, 201)
