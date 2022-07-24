from msilib.schema import ListView
from re import U
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

from users.models import Profile

from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import (
    ListView,
    DetailView,
    CreateView
)

def is_admin(user):
    return user.is_superuser

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Your account has been created! You are now able to log in')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def register_admin(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.instance.is_superuser = True
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Your account has been created! You are now able to log in')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register_admin.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'users/profile_list.html'
    context_object_name = 'users'
    ordering = ['-date_joined']
    paginate_by = 4

    def get_queryset(self):
        return User.objects.order_by('-date_joined')
    
    def test_func(self):
        return self.request.user.is_superuser

@login_required
@user_passes_test(is_admin)
def ban_user(request, username):
    usr = get_object_or_404(User, username=username)
    user = usr.profile
    if not user.is_locked:
        user.is_locked = True
        user.save()
    return redirect('/user/{}'.format(username))

@login_required
@user_passes_test(is_admin)
def unban_user(request, username):
    usr = get_object_or_404(User, username=username)
    user = usr.profile
    if user.is_locked:
        user.is_locked = False
        user.save()
    return redirect('/user/{}'.format(username))
