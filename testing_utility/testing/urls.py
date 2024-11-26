from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),  
    path('logout/', views.logout_view, name='logout'),
    path('test_website/', views.test, name='test_website'),
    path('register/', views.register, name='register'),
    path('submit-links/', views.run_tests_view, name='run_tests'),
    path('result', views.result, name='result'),
    path("form-test", views.form_test, name='form_test'),
    path('navigation/', views.navigation,name = 'navigation'),
    path('navigation-test/', views.navigation_view, name='navigation_test'),
    path("end-to-end", views.navigation_view_new, name="navigation_new")
]
