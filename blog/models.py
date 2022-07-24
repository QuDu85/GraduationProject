from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
import os

class Post(models.Model):
	title = models.CharField(max_length=100)
	file = models.FileField(upload_to='Files')
	content = models.TextField()
	date_posted = models.DateTimeField(default=timezone.now)
	author = models.ForeignKey(User, on_delete=models.CASCADE)
	status = models.CharField(max_length=1, default='S')
	label = models.TextField(max_length=10, default='N/A')

	def __str__(self):
		return self.title

	def extension(self):
		name, extension = os.path.splitext(self.file.name)
		return extension

	def get_absolute_url(self):
		return reverse('post-detail', kwargs={'pk': self.pk})

class Report(models.Model):
	reporter = models.ForeignKey(User, on_delete=models.CASCADE)
	video = models.ForeignKey(Post, on_delete=models.CASCADE)
	label = models.TextField(max_length=10, default='N/A')
	status = models.CharField(max_length=1, default='S')
	date_submitted = models.DateTimeField(default=timezone.now)