from django.db import models

from profiles.models import Profile


class Tags(models.Model):
    name = models.CharField(verbose_name='Название',max_length=255)


class Questions(models.Model):
    user = models.ForeignKey(Profile, verbose_name='Автор')
    title = models.CharField(max_length=1024, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    tags = models.ManyToManyField(Tags)


class Answers(models.Model):
    accepted = models.BooleanField(verbose_name='Ответ принят?')
    user = models.ForeignKey(Profile, verbose_name='Автор')
    content = models.TextField(verbose_name='Содержание')
    created_at = models.DateTimeField(verbose_name='Дата добавления', auto_now_add=True)
