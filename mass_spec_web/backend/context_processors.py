from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

from mass_spec_web.backend.forms import CustomAuthenticationForm, CustomUserCreationForm


# def login_view(request): # Вьюшка для авторизации
#
#     if request.method == 'GET':
#         form_log = CustomAuthenticationForm(request.POST or None)
#
#         data = {
#             'form_log': form_log,
#         }
#         return data
#
#     if request.method == 'POST':
#         if request.POST.get('submit') == 'Войти':
#             form_log = CustomAuthenticationForm(request.POST or None)
#             if form_log.is_valid():
#                 username = form_log.cleaned_data['username']
#                 password = form_log.cleaned_data['password']
#                 user = authenticate(username=username, password=password)
#                 if user:
#                     profile = login(request, user)
#                     return {}
#             data = {
#                 'form_log': form_log,
#             }
#             return data
#         return {}
#
#
# def registration_view(request): # Вьюшка для регистрации
#
#     if request.method == 'GET':
#         form_reg = CustomUserCreationForm(request.POST or None)
#
#         context = {
#             'form_reg': form_reg,
#         }
#         return context
#
#     if request.method == 'POST':
#         if request.POST.get('submit') == 'Зарегистрироваться':
#             form_reg = CustomUserCreationForm(request.POST or None)
#             if form_reg.is_valid():
#                 new_user = form_reg.save(commit=False)
#                 new_user.username = form_reg.cleaned_data['username']
#                 new_user.email = form_reg.cleaned_data['email']
#                 new_user.save()
#                 new_user.set_password(form_reg.cleaned_data['password'])
#                 new_user.save()
#                 User.objects.create(
#                     user=new_user,
#                 )
#                 user = authenticate(username=form_reg.cleaned_data['username'], password=form_reg.cleaned_data['password'])
#                 login(request, user)
#                 return {}
#             context = {
#                 'form_reg': form_reg,
#             }
#             return context
#         return {}
