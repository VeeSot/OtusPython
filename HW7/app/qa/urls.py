from django.conf.urls import url

from HW7.app.qa.views import questions

urlpatterns = [
    url(r'q/$', questions, name='questions'),
    url(r'q/(?P<idx>[0-9]+)$', questions, name='questions'),
]
