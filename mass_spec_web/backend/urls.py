from django.urls import path
from . import views
from .views import tags_list, TagDetail, SpectrumDetail, spectrum_list, TagCreate, TagUpdate, TagDelete, \
    spectrum_search, UserDetail, UserUpdate, users_list, upload_result, \
    UploadSpectrum, spectrum_draft_list, SpectrumReviewDetail, SpectrumUpdate, SpectrumDelete, \
    spectrum_similarity_search, main_page, news_page, NewsCreate, NewsDetail, NewsUpdate, NewsDelete, SupportCreate, \
    SupportDetail, SupportUpdate, SupportDelete, SignUpView, support_page

urlpatterns = [
    path('', main_page, name='main_page_url'),
    path('support_notifications/', support_page, name='support_page_url'),
    path('news/', news_page, name='news_page_url'),
    path('support/create/', SupportCreate.as_view(), name='support_create_url'),
    path('news/create/', NewsCreate.as_view(), name='news_create_url'),
    path('support/<int:id>/', SupportDetail.as_view(), name='support_detail_url'),
    path('news/<int:id>/', NewsDetail.as_view(), name='news_detail_url'),
    path('support/<int:id>/update/', SupportUpdate.as_view(), name='support_update_url'),
    path('news/<int:id>/update/', NewsUpdate.as_view(), name='news_update_url'),
    path('support/<int:id>/delete/', SupportDelete.as_view(), name='support_delete_url'),
    path('news/<int:id>/delete/', NewsDelete.as_view(), name='news_delete_url'),
    path('tags/', tags_list, name='tags_list_url'),
    path('tag/create/', TagCreate.as_view(), name='tag_create_url'),
    path('tag/<int:id>/', TagDetail.as_view(), name='tag_detail_url'),
    path('tag/<int:id>/update/', TagUpdate.as_view(), name='tag_update_url'),
    path('tag/<int:id>/delete/', TagDelete.as_view(), name='tag_delete_url'),
    path('upload/', UploadSpectrum.as_view(), name='upload'),
    path('display/spectrum_detail/<int:id>/', SpectrumDetail.as_view(), name='spectrum_detail_url'),
    path('display/spectrum_detail/<int:id>/update/', SpectrumUpdate.as_view(), name='spectrum_update_url'),
    path('display/spectrum_detail/<int:id>/delete/', SpectrumDelete.as_view(), name='spectrum_delete_url'),
    path('display/spectrum_review_detail/<int:id>/', SpectrumReviewDetail.as_view(), name='spectrum_review_detail'),
    path('spectrum_list/', spectrum_list, name='spectrum_list'),
    path('spectrum_draft_list/', spectrum_draft_list, name='spectrum_draft_list'),
    path('upload_result/', upload_result, name='upload_result'),
    path('user_profile/<str:username>/', UserDetail.as_view(), name='user-profile'),
    path('update_profile/<str:username>/update/', UserUpdate.as_view(), name='update_profile'),
    path('users_list/', users_list, name='users_list'),
    path('spectrum_search/', spectrum_search, name='spectrum_search'),
    path('spectrum_similarity_search/', spectrum_similarity_search, name='spectrum_similarity_search'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login')
]
