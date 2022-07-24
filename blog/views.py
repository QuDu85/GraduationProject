from compat import render_to_string
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

from .models import Post, Report
import operator
from django.urls import reverse_lazy
from django.contrib.staticfiles.views import serve
from background_task import background
from .keras_predict import predict_video
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test


# def home(request):
#     context = {
#         'posts': Post.objects.all()
#     }
#     return render(request, 'blog/home.html', context)

def search(request):
    template='blog/home.html'

    query=request.GET.get('q')

    result=Post.objects.filter(Q(title__icontains=query) | Q(author__username__icontains=query) | Q(content__icontains=query))
    paginate_by=2
    context={ 'posts':result }
    return render(request,template,context)
   
def is_admin(user):
    return user.is_superuser

# def getfile(request):
#    return serve(request, 'File')

@background(schedule=30)
def process_video(id, video_url):
    try:
        video = Post.objects.get(pk=id)
    except:
        print("Post not found")
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
def report_video(request, id):
    try:
        video = Post.objects.get(pk=id)
        if video.author == request.user:
            message = 'You cannot report your own video'
        elif video.status != 'A' or request.method!='POST' or request.user.is_superuser:
            message = 'Invalid action'
        elif request.user.report_set.filter(video=video).exists():
            message = 'You\'ve already reported this video'
        else:
            report = Report(reporter = request.user, video = video, label = request.POST['label'], status = 'S')
            report.save()
            message = 'Report submitted'
        return render(request, 'blog/post_detail.html', {'object':video, 'message':message})
    except:
        message = 'Post not found'
        return render(request, 'blog/post_detail.html', {'message':message})

@login_required
@user_passes_test(is_admin)
def unblock_video(request, id):
    try:
        video = Post.objects.get(pk=id)
        if video.status !='A':
            video.status = 'A'
            video.save()
        return redirect('/post/{}'.format(id))
    except:
        return redirect('/post/{}'.format(id))

@login_required
@user_passes_test(is_admin)
def block_video(request, id):
    try:
        video = Post.objects.get(pk=id)
        if video.status != 'R' and request.method == 'POST':
            video.status = 'R'
            label = request.POST['label']
            video.label = label
            video.save()
        return redirect('/post/{}'.format(id))
    except:
        return redirect('/post/{}'.format(id))

@login_required
@user_passes_test(is_admin)
def delete_report(request, id):
    try:
        video = Post.objects.get(pk=id)
        reports = Report.objects.filter(status='S', video=video)
        for report in reports:
            report.status = 'R'
            report.save()
        return redirect('/reports/{}'.format(id))
    except:
        return redirect('/reports/{}'.format(id))

class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 3

    def get_queryset(self):
        return Post.objects.filter(status='A').order_by('-date_posted')


class PostRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Post
    template_name = 'blog/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 3

    def get_queryset(self):
        return Post.objects.filter(status='M').order_by('-date_posted')

    def test_func(self):
        return self.request.user.is_superuser

class ReportListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Post
    template_name = 'blog/report_list.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 3

    def get_queryset(self):
        return Post.objects.filter(status='A', report__status='S').order_by('-date_posted')

    def test_func(self):
        return self.request.user.is_superuser

class ReportDetailView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Report
    template_name = 'blog/report_detail.html'
    context_object_name = 'reports'
    paginate_by = 3

    def get_queryset(self):
        post = get_object_or_404(Post, pk=self.kwargs.get('id'))
        return Report.objects.filter(status='S', video=post).order_by('-date_submitted')

    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super(ReportDetailView, self).get_context_data(**kwargs)
        context.update({
            'post': get_object_or_404(Post, pk=self.kwargs.get('id')),
        })
        return context

class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'  
    context_object_name = 'posts'
    paginate_by = 3

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        if self.request.user.is_superuser or self.request.user==user:
            return Post.objects.filter(author=user).order_by('-date_posted')
        else:
            return Post.objects.filter(author=user, status='A').order_by('-date_posted')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'content', 'file']

    def form_valid(self, form):
        if self.request.user.profile.is_locked:
            return render(self.request, 'blog/warning_forbidden.html')
        form.instance.author = self.request.user
        response = super().form_valid(form)
        process_video(form.instance.id, form.instance.file.path)
        return response


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    template_name = 'blog/post_form.html'
    fields = ['title', 'content']

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

# def about(request):
#     return render(request, 'blog/about.html', {'title': 'About'})
