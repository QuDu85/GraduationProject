from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)

from users.models import Profile

from .models import Post
import operator
from django.urls import reverse_lazy
from django.contrib.staticfiles.views import serve
from background_task import background
from .keras_predict import predict_video
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test


def home(request):
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'blog/home.html', context)

def search(request):
    template='blog/home.html'

    query=request.GET.get('q')

    result=Post.objects.filter(Q(title__icontains=query) | Q(author__username__icontains=query) | Q(content__icontains=query))
    paginate_by=2
    context={ 'posts':result }
    return render(request,template,context)
   
def is_admin(user):
    return user.is_superuser

def getfile(request):
   return serve(request, 'File')

@background(schedule=30)
def process_video(id, video_url):
    try:
        video = Post.objects.get(pk=id)
    except:
        return
    video.status = 'P'
    video.save()
    safe, label = predict_video(video_url)
    if safe:
        video.status = 'A'
    else:
        video.status = 'F'
    video.label = label
    video.save()
    return safe

@login_required
def manual_request(request, id):
    try:
        video = Post.objects.get(pk=id)
        if video.author == request.user and video.status == 'F':
            video.status = 'M'
            video.save()
        return redirect('/post/{}'.format(id))
    except:
        return redirect('/post/{}'.format(id))

@login_required
@user_passes_test(is_admin)
def request_approve(request, id):
    try:
        video = Post.objects.get(pk=id)
        if video.status == 'M':
            video.status = 'A'
            video.save()
        return redirect('/post/{}'.format(id))
    except:
        return redirect('/post/{}'.format(id))

@login_required
@user_passes_test(is_admin)
def request_reject(request, id):
    try:
        video = Post.objects.get(pk=id)
        if video.status == 'M':
            video.status = 'R'
            video.save()
        return redirect('/post/{}'.format(id))
    except:
        return redirect('/post/{}'.format(id))


class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 3

    def get_queryset(self):
        return Post.objects.filter(status='A').order_by('-date_posted')


class PostRequestListView(ListView, UserPassesTestMixin):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 3

    def get_queryset(self):
        return Post.objects.filter(status='M').order_by('-date_posted')

    def test_func(self):
        post = self.get_object()
        return self.request.user.is_superuser

class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'  
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'



class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        process_video(form.instance.id, form.instance.file.path)
        return response


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'
    template_name = 'blog/post_confirm_delete.html'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False

def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})
