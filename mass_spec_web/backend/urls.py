from django.urls import path
from . import views
from .views import posts_list, tags_list, PostDetail, TagDetail, SpectrumDetail, spectrum_list, TagCreate, PostCreate, \
    TagUpdate, PostUpdate, TagDelete, PostDelete, spectrum_search, UserDetail, UserUpdate, users_list, upload_result, \
    UploadSpectrum, spectrum_draft_list, SpectrumReviewDetail, SpectrumUpdate, SpectrumDelete

urlpatterns = [
    path('', posts_list, name='main_page_url'),
    path('post/create/', PostCreate.as_view(), name='post_create_url'),
    path('post/<str:slug>/', PostDetail.as_view(), name='post_detail_url'),
    path('post/<str:slug>/update/', PostUpdate.as_view(), name='post_update_url'),
    path('post/<str:slug>/delete/', PostDelete.as_view(), name='post_delete_url'),
    path('tags/', tags_list, name='tags_list_url'),
    path('tag/create/', TagCreate.as_view(), name='tag_create_url'),
    path('tag/<str:slug>/', TagDetail.as_view(), name='tag_detail_url'),
    path('tag/<str:slug>/update/', TagUpdate.as_view(), name='tag_update_url'),
    path('tag/<str:slug>/delete/', TagDelete.as_view(), name='tag_delete_url'),
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
    path('display/', views.view_spectrum1, name='display'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login')
]
