from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password/change/', auth_views.PasswordChangeView.as_view(template_name='users/password_change.html'), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'), name='password_change_done'),
    
    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('settings/', views.UserSettingsView.as_view(), name='settings'),
    
    # User management (admin only)
    path('manage/', views.UserManagementView.as_view(), name='user_management'),
    path('manage/create/', views.UserCreateView.as_view(), name='user_create'),
    path('manage/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('manage/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('manage/<int:pk>/permissions/', views.UserPermissionsView.as_view(), name='user_permissions'),
    
    # Teams
    path('teams/', views.TeamListView.as_view(), name='team_list'),
    path('teams/create/', views.TeamCreateView.as_view(), name='team_create'),
    path('teams/<uuid:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('teams/<uuid:pk>/members/', views.TeamMembershipView.as_view(), name='team_members'),
    
    # Activity logs
    path('activity/', views.UserActivityView.as_view(), name='activity'),
    path('activity/user/<int:user_id>/', views.UserActivityDetailView.as_view(), name='user_activity_detail'),
    
    # API endpoints
    path('api/permissions/', views.user_permissions_api, name='api_permissions'),
]