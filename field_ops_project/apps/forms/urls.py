from django.urls import path
from . import views

urlpatterns = [
    # Anket Listesi
    path('list/', views.survey_list, name='survey_list'),
    
    # Yeni Anket Oluşturma (İsim düzeltildi: create_survey -> survey_create)
    path('create/', views.survey_create, name='survey_create'),
    
    # Anket Düzenleyici (Builder)
    path('builder/<int:pk>/', views.survey_builder, name='survey_builder'),
    
    # Anket Silme
    path('delete/<int:pk>/', views.survey_delete, name='survey_delete'),
    
    # Soru Ekleme
    path('question/add/<int:survey_id>/', views.question_create, name='question_create'),
    
    # Soru Silme
    path('question/delete/<int:question_id>/', views.question_delete, name='question_delete'),

    # Mevcut satırların arasına ekle:
    path('question/edit/<int:question_id>/', views.question_edit, name='question_edit'),

    # ...
    path('api/question-options/<int:question_id>/', views.get_question_options, name='get_question_options'),
]