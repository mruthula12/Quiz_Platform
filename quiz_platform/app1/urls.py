from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_user, name="register"),
    path("quizzes/", views.quiz_list_create, name="quiz_list_create"),
    path("user/quizzes/", views.quiz_list_for_user, name="quiz_list_for_user"),
    path("submit_quiz/", views.submit_quiz, name="submit_quiz"),
    path("login/", views.login_user, name="login"),   
    path("categories/", views.create_or_update_category, name="create_category"),
    path("marks/history/",views.user_mark_history, name="user_mark_history"),

]
