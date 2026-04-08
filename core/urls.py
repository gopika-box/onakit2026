from django.urls import path

from .views import *

urlpatterns = [
    path('',landing_page,name='landing_page'),
    path('login/',login_view,name='login_view'),
    path('dashboard/',dashboard_redirect,name='dashboard_redirect'),
    
    path('user-dashboard/',user_dashboard, name='user_dashboard'),
    path('coordinator-dashboard/',coordinator_dashboard, name='coordinator_dashboard'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/master-sheet/', master_sheet, name='master_sheet'),
    path('admin-dashboard/update-payment/<int:user_id>/<str:month>/', update_payment, name='update_payment'),

    path('admin-dashboard/manage-users/', manage_users, name='manage_users'),
    path('admin-dashboard/edit-user/<int:user_id>/', edit_user, name='edit_user'),
    path('admin-dashboard/add-user/', add_user, name='add_user'),
    path('admin-dashboard/delete-user/<int:user_id>/', delete_user, name='delete_user'),

    
     path('logout/',logout,name='logout'),
]
