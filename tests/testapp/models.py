from django.contrib.auth.models import User
from django.db import models


class Note(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)


class Tag(models.Model):
    name = models.CharField(max_length=100)


class Blog(models.Model):
    name = models.CharField(max_length=100)


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    publish_date = models.DateField(null=True)

    blog = models.ForeignKey(Blog, null=True, on_delete=models.CASCADE)
    author = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    note = models.ForeignKey(Note, null=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)


class Cover(models.Model):
    comment = models.CharField(max_length=100)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)


class Page(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    previous_page = models.ForeignKey('self', null=True, on_delete=models.CASCADE)


class A(models.Model):
    title = models.CharField(max_length=100)
    b = models.ForeignKey('B', null=True, on_delete=models.CASCADE)


class B(models.Model):
    name = models.CharField(max_length=100)
    c = models.ForeignKey('C', null=True, on_delete=models.CASCADE)


class C(models.Model):
    title = models.CharField(max_length=100)
    a = models.ForeignKey('A', null=True, on_delete=models.CASCADE)


class Person(models.Model):
    name = models.CharField(max_length=100)
    best_friend = models.ForeignKey('self', null=True, on_delete=models.CASCADE)

    date_joined = models.DateField(auto_now_add=True)
    time_joined = models.TimeField(auto_now_add=True)
    datetime_joined = models.DateTimeField(auto_now_add=True)
