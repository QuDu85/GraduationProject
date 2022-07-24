from django.urls import path
from .views import (
    PostListView,
    PostRequestListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    ReportDetailView,
    ReportListView,
    UserPostListView
)
from . import views

urlpatterns = [
    path('', PostListView.as_view(), name='blog-home'),
    path('request/', PostRequestListView.as_view(), name='post-requests'),
    path('user/<str:username>', UserPostListView.as_view(), name='user-posts'),
    path('post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('manual/<int:id>/', views.manual_request, name='request-create'),
    path('report/<int:id>/', views.report_video, name='report-video'),
    path('reports/', ReportListView.as_view(), name='post-reports'),
    path('reports/<int:id>/', ReportDetailView.as_view(), name='report-detail'),
    path('reports/<int:id>/delete/', views.delete_report, name='report-delete'),
    path('approve/<int:id>/', views.unblock_video, name='request-approve'),
    path('reject/<int:id>/', views.block_video, name='request-reject'),
    path('post/new/', PostCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('search/',views.search,name='search' ),
]
