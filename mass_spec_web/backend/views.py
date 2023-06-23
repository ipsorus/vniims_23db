import os
import re
from datetime import datetime
from pathlib import Path

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.views import View, generic
from django.views.decorators.csrf import csrf_exempt
from matchms.similarity import CosineGreedy

from .models import SpectrumMeasurement, Spectrum, Post, Tag, Metadata, CustomUser, Support
from .forms import CustomUserCreationForm, CustomAuthenticationForm, TagForm, PostForm, CustomUserChangeForm, \
    SupportForm

import json
from io import BytesIO

import pymzml
from bootstrap_modal_forms.generic import BSModalCreateView, BSModalLoginView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from .utils import ObjectDetailMixin, ObjectCreateMixin, ObjectUpdateMixin, ObjectDeleteMixin, UserDetailMixin, \
    UserUpdateMixin, generate_spectrum_plot, SpectrumMixin, \
    SpectrumUpdateMixin, SpectrumDeleteMixin


BASE_DIR = Path(__file__).resolve().parent.parent

sources = {
    0: "Не выбрано",
    1: "Жидкостная хроматография (LC)",
    2: "Газовая хроматография (GC)",
    3: "Прямая инъекция/инфузия (DI)",
    4: "Капиллярный электрофорез (CE)",
}
levels = {
    0: "Не выбрано",
    1: "MS",
    2: "MS2",
    3: "MS3",
    4: "MS4",
    5: "MS5",
}
ionzations = {
    0: "Не выбрано",
    1: "Химическая ионизация при атмосферном давлении (APCI)",
    2: "Электронный удар (EI)",
    3: "Химическая ионизация (CI)",
    4: "Ионизация электрораспылением (ESI)",
    5: "Быстрая атомная бомбардировка (FAB)",
    6: "Лазерная десорбция ионизация с матрицей (MALDI)",
}
polarities = {
    0: "Не выбрано",
    1: "Положительный",
    2: "Отрицательный",
}


def check_admin(user):
    return user.is_superuser


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = 'authentication/signup.html'
    success_message = 'Вы успешно зарегистрированы. Авторизуйтесь.'
    success_url = reverse_lazy('main_page_url')


class CustomLoginView(BSModalLoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'authentication/login.html'
    success_message = 'Вы успешно авторизовались.'
    success_url = reverse_lazy('display')


class UserDetail(UserDetailMixin, View):
    model = CustomUser
    template = 'users/profile.html'


class UserUpdate(LoginRequiredMixin, UserUpdateMixin, View):
    model = CustomUser
    model_form = CustomUserChangeForm
    template = 'users/update_profile.html'
    raise_exception = True


@user_passes_test(check_admin)
def users_list(request):
    users = CustomUser.objects.all()
    context = {
        'count': users.count(),
        'users': users
    }
    return render(request, 'users/users_list.html', context=context)


def news_page(request):
    search_query = request.GET.get('search', '')

    if search_query:
        posts = Post.objects.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))
    else:
        posts = Post.objects.all()
    paginator = Paginator(posts, 5)

    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    is_paginated = page.has_other_pages()

    if page.has_previous():
        prev_url = '?page={}'.format(page.previous_page_number())
    else:
        prev_url = ''
    if page.has_next():
        next_url = '?page={}'.format(page.next_page_number())
    else:
        next_url = ''

    context = {
        'page_object': page,
        'is_paginated': is_paginated,
        'prev_url': prev_url,
        'next_url': next_url,
    }
    return render(request, 'news.html', context=context)


def support_page(request):
    search_query = request.GET.get('search', '')

    if search_query:
        support_posts = Support.objects.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))
    else:
        support_posts = Support.objects.all()
    paginator = Paginator(support_posts, 5)

    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    is_paginated = page.has_other_pages()

    if page.has_previous():
        prev_url = '?page={}'.format(page.previous_page_number())
    else:
        prev_url = ''
    if page.has_next():
        next_url = '?page={}'.format(page.next_page_number())
    else:
        next_url = ''

    context = {
        'page_object': page,
        'is_paginated': is_paginated,
        'prev_url': prev_url,
        'next_url': next_url,
    }
    return render(request, 'support_notifications.html', context=context)


def main_page(request):
    spectrum_etalon = cache.get('spectrum_etalon')
    spectrum_users = cache.get('spectrum_users')
    users = cache.get('users')
    if not spectrum_etalon:
        spectrum_etalon = Spectrum.objects.filter(is_etalon=True, draft=False).count()
        cache.set('spectrum_etalon', spectrum_etalon, 360)

    if not spectrum_users:
        spectrum_users = Spectrum.objects.filter(is_etalon=False, draft=False).count()
        cache.set('spectrum_users', spectrum_users, 360)

    if not users:
        users = CustomUser.objects.all().count()
        cache.set('users', users, 360)

    search_query = request.GET.get('search', '')

    if search_query:
        support_posts = Support.objects.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))
    else:
        support_posts = Support.objects.all()
    paginator = Paginator(support_posts, 2)

    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    is_paginated = page.has_other_pages()

    if page.has_previous():
        prev_url = '?page={}'.format(page.previous_page_number())
    else:
        prev_url = ''
    if page.has_next():
        next_url = '?page={}'.format(page.next_page_number())
    else:
        next_url = ''

    context = {
        'page_object': page,
        'is_paginated': is_paginated,
        'prev_url': prev_url,
        'next_url': next_url,
        'spectrum_etalon': spectrum_etalon,
        'spectrum_users': spectrum_users,
        'users': users
    }
    return render(request, 'index.html', context=context)


class NewsDetail(ObjectDetailMixin, View):
    model = Post
    template = 'news/post_detail.html'


class NewsCreate(LoginRequiredMixin, ObjectCreateMixin, View):
    model_form = PostForm
    template = 'news/post_create.html'
    raise_exception = True


class NewsUpdate(LoginRequiredMixin, ObjectUpdateMixin, View):
    model = Post
    model_form = PostForm
    template = 'news/post_update_form.html'
    raise_exception = True


class NewsDelete(LoginRequiredMixin, ObjectDeleteMixin, View):
    model = Post
    template = 'news/post_delete_form.html'
    redirect_url = 'main_page_url'
    raise_exception = True


class SupportDetail(ObjectDetailMixin, View):
    model = Support
    template = 'support/support_detail.html'


class SupportCreate(LoginRequiredMixin, ObjectCreateMixin, View):
    model_form = SupportForm
    template = 'support/support_create.html'
    raise_exception = True


class SupportUpdate(LoginRequiredMixin, ObjectUpdateMixin, View):
    model = Support
    model_form = SupportForm
    template = 'support/support_update_form.html'
    raise_exception = True


class SupportDelete(LoginRequiredMixin, ObjectDeleteMixin, View):
    model = Support
    template = 'support/support_delete_form.html'
    redirect_url = 'main_page_url'
    raise_exception = True


class SpectrumUpdate(LoginRequiredMixin, SpectrumUpdateMixin, View):
    model = Spectrum
    template = 'spectra/display/spectrum_update_form.html'
    raise_exception = True


class SpectrumDelete(LoginRequiredMixin, SpectrumDeleteMixin, View):
    model = Spectrum
    template = 'spectra/display/spectrum_delete_form.html'
    redirect_url = 'main_page_url'
    raise_exception = True


def tags_list(request):
    tags = Tag.objects.all()
    return render(request, 'news/tags_list.html', context={'tags': tags})


class TagDetail(ObjectDetailMixin, View):
    model = Tag
    template = 'news/tag_detail.html'


class TagCreate(LoginRequiredMixin, ObjectCreateMixin, View):
    model_form = TagForm
    template = 'news/tag_create.html'


class TagUpdate(LoginRequiredMixin, ObjectUpdateMixin, View):
    model = Tag
    model_form = TagForm
    template = 'news/tag_update_form.html'
    raise_exception = True


class TagDelete(LoginRequiredMixin, ObjectDeleteMixin, View):
    model = Tag
    template = 'news/tag_delete_form.html'
    redirect_url = 'tags_list_url'
    raise_exception = True


def map_spectrum(spectrum: Spectrum):
    precursor_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Precursor_type')
    spectrum_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Spectrum_type')
    precursor_mz = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='PrecursorMZ')
    instrument_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Instrument_type')
    ion_mode = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Ion_mode')
    collision_energy = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Collision_energy')
    formula = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Formula')

    fields = [precursor_type, spectrum_type, precursor_mz, instrument_type, ion_mode, collision_energy, formula]
    # peaks_list = spectrum.spectrum_json

    # plot_div = generate_spectrum_mini_plot(peaks_list=peaks_list, save_image=True, id=spectrum.id)

    return {
        'spectrum': spectrum,
        'image': "plots/plot-%d.png" % spectrum.pk,
        'name': spectrum.name,
        'id': spectrum.pk,
        'author': spectrum.author,
        'create_date': spectrum.date_created,
        'fields': fields
    }


@csrf_exempt
def spectrum_similarity_search(request):
    if request.POST:
        if 'peaks' in request.POST:
            spectrums = Spectrum.objects.filter(draft=False, is_etalon=True)

            import numpy as np
            from matchms import calculate_scores
            from matchms import Spectrum as Spec
            from matchms.similarity import MetadataMatch

            references = []
            total_matches = []

            for spectrum in spectrums:
                mz = []
                intensity = []
                sorted_etalon_peaks = sorted(spectrum.spectrum_json, key=lambda peak: float(peak[0]))
                for item in sorted_etalon_peaks:
                    mz.append(float(item[0]))
                    intensity.append(float(item[1]))

                # formula = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Formula')
                # print('mz', mz)

                spectrum_test = Spec(mz=np.array(mz),
                                     intensities=np.array(intensity),
                                     metadata={"id": spectrum.id})

                references.append(spectrum_test)

            mz_query = []
            intensity_query = []
            peaks_list = json.loads(request.POST.get('peaks'))
            sorted_peaks = sorted(peaks_list, key=lambda peak: float(peak[0]))
            for item in sorted_peaks:
                mz_query.append(float(item[0]))
                intensity_query.append(float(item[1]))

            spectrum_query = Spec(mz=np.array(mz_query),
                                  intensities=np.array(intensity_query))

            for reference in references:
                cosine_greedy = CosineGreedy(tolerance=0.2)

                score = cosine_greedy.pair(reference, spectrum_query)
                # print(
                #     f"Cosine score is {score['score']:.2f} with {score['matches']} matched peaks, id: {reference.get('id')}")
                if float(f"{score['score']:.2f}") >= float(request.POST.get('minSimilarity')):
                    total_matches.append({'id': reference.get('id'),
                                          'score': float(f"{score['score']:.2f}"),
                                          'matched_peaks': int(f"{score['matches']}"),
                                          'name': Spectrum.objects.filter(id=reference.get('id')).values_list('name', flat=True).get()})

            # print('total', total_matches, len(total_matches))

            res = []

            if total_matches:
                return render(request, 'spectra/query/spectrum_similarity_result.html',
                              context={'objects': total_matches, 'count': len(total_matches)})
                # for item in total_matches:
                #     res.append(Spectrum.objects.get(id=item['id']))
                # objects = list(map(map_spec, res))
                # return render(request, 'spectra/spectrum_similarity_result.html',
                #               context={'objects': objects, 'count': len(objects)})
            else:
                return render(request, 'spectra/query/spectrum_similarity_result.html',
                              context={'objects': res})

        if 'pastedSpectrumSearch' in request.POST:
            peaks_list = []
            try:
                try:
                    peaks = [item.split(":") for item in request.POST.get('pastedSpectrumSearch').split(' ') if item != '' and
                             (re.match(r'([0-9]*\.?[0-9]+)\s*:\s*([0-9]*\.?[0-9]+)', item))]

                    if not peaks:
                        assert False
                    sorted_peaks = sorted(peaks, key=lambda peak: float(peak[0]))
                    for item in sorted_peaks:
                        peaks_list.append([float(item[0]), float(item[1])])

                except AssertionError:
                    for line in request.POST.get('pastedSpectrumSearch').splitlines():

                        item = line.replace("'", '"')
                        item = " ".join(item.split())
                        if re.match(r'([0-9]*\.?[0-9]+)\s*:\s*([0-9]*\.?[0-9]+)', item) or re.match(
                                r'([0-9]+\.?[0-9]*)[ \t]+([0-9]*\.?[0-9]+)(?:\s*(?:[;\n])|(?:"?(.+)"?\n?))?', item):
                            ion = item.strip().replace("\t", ' ').split(' ')
                            peaks_list.append([float(ion[0]), float(ion[1])])

                plot_div = generate_spectrum_plot(peaks_list=peaks_list)

                context = {'plot_div': plot_div,
                           'peaks': peaks_list}

                return render(request, 'spectra/query/spectrum_search_detail.html', context=context)
            except ValueError:
                messages.error(request, 'Невозможно загрузить масс-спектр. Проверьте передаваемые данные')
                return redirect('spectrum_search')

        if 'file' in request.FILES:
            peaks_list = []
            file = request.FILES['file']
            file_content = BytesIO(file.read())

            try:
                try:
                    for line in file_content:
                        item = line.decode('utf8').replace("'", '"')
                        item = " ".join(item.split())
                        if re.match(r'([0-9]*\.?[0-9]+)\s*:\s*([0-9]*\.?[0-9]+)', item) or re.match(
                                r'([0-9]+\.?[0-9]*)[ \t]+([0-9]*\.?[0-9]+)(?:\s*(?:[;\n])|(?:"?(.+)"?\n?))?', item):
                            ion = item.strip().replace("\t", ' ').split(' ')
                            peaks_list.append([float(ion[0]), float(ion[1])])
                    if not peaks_list:
                        assert False

                except AssertionError:
                    peaks = [item.split(":") for item in request.POST.get('pastedSpectrum').split(' ') if
                             item != '' and (re.match(r'([0-9]*\.?[0-9]+)\s*:\s*([0-9]*\.?[0-9]+)', item))]

                    sorted_peaks = sorted(peaks, key=lambda peak: float(peak[0]))
                    for item in sorted_peaks:
                        peaks_list.append([float(item[0]), float(item[1])])

            except:
                messages.error(request, f'Невозможно загрузить масс-спектр. Проверьте передаваемые данные.')
                return redirect('spectrum_search')

            if not peaks_list:
                messages.error(request, 'Невозможно загрузить масс-спектр. Проверьте передаваемые данные. Отсутствуют данные о спектре.')
                return redirect('spectrum_search')

            plot_div = generate_spectrum_plot(peaks_list=peaks_list)

            context = {'plot_div': plot_div,
                       'peaks': peaks_list}

            return render(request, 'spectra/query/spectrum_search_detail.html', context=context)


@csrf_exempt
def spectrum_search(request):
    sourceIntroduction = [
        {'name': "Жидкостная хроматография", 'abv': 'LC'},
        {'name': "Газовая хроматография", 'abv': 'GC'},
        {'name': "Прямая инъекция/инфузия", 'abv': 'DI'},
        {'name': "Капиллярный электрофорез", 'abv': 'CE'}
    ]

    ionizationMethod = [
        {'name': "Химическая ионизация при атмосферном давлении", 'abv': '(APCI)'},
        {'name': "Электронный удар", 'abv': '(EI)'},
        {'name': "Химическая ионизация", 'abv': '(CI)'},
        {'name': "Ионизация электрораспылением", 'abv': '(ESI)'},
        {'name': "Быстрая атомная бомбардировка", 'abv': '(FAB)'},
        {'name': "Лазерная десорбция ионизация с матрицей", 'abv': '(MALDI)'}
    ]

    msType = [{'name': 'MS1'}, {'name': 'MS2'}, {'name': 'MS3'}, {'name': 'MS4'}, {'name': 'MS5'}]
    ionMode = [{'name': "Положительный"}, {'name': "Отрицательный"}]
    context = {
        'sourceIntroduction': sourceIntroduction,
        'ionizationMethod': ionizationMethod,
        'msType': msType,
        'ionMode': ionMode
    }

    if request.GET:
        search_url = ''
        search_queryes = dict()
        res = []

        if request.GET.get('Name', ''):
            res = list(Spectrum.objects.filter(Q(name__icontains=request.GET.get('Name', ''))).filter(draft=False))
            search_queryes.update({'Название': request.GET.get('Name', '')})
            search_url += f"&Name={request.GET.get('Name', '')}"
        if request.GET.get('Formula', ''):
            # res2 = Metadata.objects.filter(Q(value__icontains=request.GET.get('Formula', ''))).values_list('spectrum', flat=True)
            res2 = list(Spectrum.objects.filter(Q(formula__icontains=request.GET.get('Formula', ''))).filter(draft=False))
            search_queryes.update({'Формула': request.GET.get('Formula', '')})
            search_url += f"&Formula={request.GET.get('Formula', '')}"
            res += res2
            # for item in res2:
            #     res.append(Spectrum.objects.get(id=item))
        if request.GET.get('Cas', ''):
            res3 = list(Spectrum.objects.filter(Q(cas__icontains=request.GET.get('Cas', ''))).filter(draft=False))
            search_queryes.update({'CAS-номер': request.GET.get('Cas', '')})
            search_url += f"&Cas={request.GET.get('Cas', '')}"
            res += res3
        if request.GET.get('Exact_mass', ''):
            res4 = list(Spectrum.objects.filter(Q(exact_mass__icontains=request.GET.get('Exact_mass', ''))).filter(draft=False))
            search_queryes.update({'Точная масса': request.GET.get('Exact_mass', '')})
            search_url += f"&Exact_mass={request.GET.get('Exact_mass', '')}"
            res += res4

        if res:
            res_set = set(res)

            objects = list(map(map_spectrum, res_set))

            paginator = Paginator(objects, 10)

            page_number = request.GET.get('page', 1)
            page = paginator.get_page(page_number)

            is_paginated = page.has_other_pages()

            if page.has_previous():
                prev_url = f'?page={page.previous_page_number()}{search_url}'
            else:
                prev_url = ''
            if page.has_next():
                next_url = f'?page={page.next_page_number()}{search_url}'
            else:
                next_url = ''

            context = {
                'search_url': search_url,
                'count': len(res_set),
                'search_queryes': search_queryes,
                'page_object': page,
                'is_paginated': is_paginated,
                'prev_url': prev_url,
                'next_url': next_url
            }
            return render(request, 'spectra/query/spectrum_search_result.html', context=context)

        else:
            return render(request, 'spectra/query/spectrum_search_result.html',
                          context={'objects': res, 'search_queryes': search_queryes})

    else:
        return render(request, 'spectra/query/search.html', context={'context': context})


def spectrum_list(request):
    spectrums = Spectrum.objects.filter(draft=False, is_etalon=False)
    objects = list(map(map_spectrum, spectrums))

    paginator = Paginator(objects, 10)

    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    is_paginated = page.has_other_pages()

    if page.has_previous():
        prev_url = '?page={}'.format(page.previous_page_number())
    else:
        prev_url = ''
    if page.has_next():
        next_url = '?page={}'.format(page.next_page_number())
    else:
        next_url = ''

    context = {
        'count': spectrums.count(),
        'page_object': page,
        'is_paginated': is_paginated,
        'prev_url': prev_url,
        'next_url': next_url
    }
    return render(request, 'spectra/spectrum_list.html', context=context)


def spectrum_certified_list(request):
    spectrums = Spectrum.objects.filter(draft=False, is_etalon=True)
    objects = list(map(map_spectrum, spectrums))

    paginator = Paginator(objects, 10)

    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    is_paginated = page.has_other_pages()

    if page.has_previous():
        prev_url = '?page={}'.format(page.previous_page_number())
    else:
        prev_url = ''
    if page.has_next():
        next_url = '?page={}'.format(page.next_page_number())
    else:
        next_url = ''

    context = {
        'count': spectrums.count(),
        'page_object': page,
        'is_paginated': is_paginated,
        'prev_url': prev_url,
        'next_url': next_url
    }
    return render(request, 'spectra/spectrum_certified_list.html', context=context)


@login_required()
@user_passes_test(check_admin)
def spectrum_draft_list(request):

    spectrums = Spectrum.objects.filter(draft=True)

    context = {
        'count': spectrums.count(),
        'spectrums': spectrums
    }
    return render(request, 'spectra/spectrum_draft_list.html', context=context)


class SpectrumReviewDetail(LoginRequiredMixin, View):
    def get(self, request, id):
        spectrum = get_object_or_404(Spectrum, id=id)
        if spectrum:
            measurement = SpectrumMeasurement.objects.filter(spectrum_id=id)[0]
            peaks_list = spectrum.spectrum_json
            fields = Metadata.objects.filter(spectrum_id=id)
            plot_div = generate_spectrum_plot(peaks_list=peaks_list)

            name = spectrum.name

            context = {
                'spectrum': spectrum,
                'name': name,
                'plot_div': plot_div,
                'peaks_list': peaks_list,
                'fields': fields,
                'id': id,
                'source': sources[measurement.source],
                'level': levels[measurement.level],
                'ionization': ionzations[measurement.ionization],
                'polarity': polarities[measurement.polarity],
            }
            return render(request, 'spectra/display/spectrum_draft_detail.html', context=context)

    def post(self, request, id):
        spectrum = get_object_or_404(Spectrum, id=id)
        if 'reject_reason' in request.POST:
            if request.POST['reject_reason']:
                spectrum.reject_reason = request.POST['reject_reason']
                spectrum.draft = True
                spectrum.date_curated = datetime.now()
                spectrum.save()
                return redirect('spectrum_draft_list')
        else:
            spectrum.draft = False
            spectrum.date_curated = datetime.now()
            spectrum.save()
            return redirect('spectrum_draft_list')


class SpectrumDetail(View):
    def get(self, request, id):
        spectrum = get_object_or_404(Spectrum, id=id)
        if spectrum:
            measurement = SpectrumMeasurement.objects.filter(spectrum_id=id)[0]
            peaks_list = spectrum.spectrum_json
            fields = Metadata.objects.filter(spectrum_id=id)
            plot_div = generate_spectrum_plot(peaks_list=peaks_list)

            name = spectrum.name

            context = {
                'spectrum': spectrum,
                'name': name,
                'plot_div': plot_div,
                'peaks_list': peaks_list,
                'fields': fields,
                'id': id,
                'source': sources[measurement.source],
                'level': levels[measurement.level],
                'ionization': ionzations[measurement.ionization],
                'polarity': polarities[measurement.polarity],
            }
            return render(request, 'spectra/display/spectrum_detail.html', context=context)


def upload_result(request):
    return render(request, 'spectra/upload/upload_result.html')


def contacts(request):
    return render(request, 'contacts.html')


class UploadSpectrum(SpectrumMixin, View):
    pass


def custom_page_not_found_view(request, exception):
    return render(request, "errors/404.html", {})


def custom_error_view(request, exception=None):
    return render(request, "errors/500.html", {})


def custom_permission_denied_view(request, exception=None):
    return render(request, "errors/403.html", {})


def custom_bad_request_view(request, exception=None):
    return render(request, "errors/400.html", {})
