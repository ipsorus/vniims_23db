import os
import re
from datetime import datetime
from pathlib import Path

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.views import View

from .models import SpectrumMeasurement, Spectrum, Post, Tag, Metadata, CustomUser
from .forms import CustomUserCreationForm, CustomAuthenticationForm, TagForm, PostForm, CustomUserChangeForm
from . import forms
import numpy
from PIL import Image
from matplotlib import pyplot
import json
from io import BytesIO

import pymzml
from bootstrap_modal_forms.generic import BSModalCreateView, BSModalLoginView
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse

from plotly.offline import plot
from plotly.graph_objs import Figure

import pathlib
import matplotlib

from .utils import ObjectDetailMixin, ObjectCreateMixin, ObjectUpdateMixin, ObjectDeleteMixin, UserDetailMixin, \
    UserUpdateMixin, generate_spectrum_mini_plot, generate_spectrum_plot, save_object, SpectrumMixin, \
    SpectrumUpdateMixin, SpectrumDeleteMixin

matplotlib.use('Agg')

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


def main(request):
    return render(request, 'index.html')


class SignUpView(BSModalCreateView):
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
    paginator = Paginator(users, 10)

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
        'count': users.count(),
        'page_object': page,
        'is_paginated': is_paginated,
        'prev_url': prev_url,
        'next_url': next_url
    }
    return render(request, 'users/users_list.html', context=context)


def posts_list(request):
    search_query = request.GET.get('search', '')

    if search_query:
        posts = Post.objects.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))
    else:
        posts = Post.objects.all()
    paginator = Paginator(posts, 2)

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
        'next_url': next_url
    }
    return render(request, 'index.html', context=context)


class PostDetail(ObjectDetailMixin, View):
    model = Post
    template = 'news/post_detail.html'


class PostCreate(LoginRequiredMixin, ObjectCreateMixin, View):
    model_form = PostForm
    template = 'news/post_create.html'
    raise_exception = True


class PostUpdate(LoginRequiredMixin, ObjectUpdateMixin, View):
    model = Post
    model_form = PostForm
    template = 'news/post_update_form.html'
    raise_exception = True


class PostDelete(LoginRequiredMixin, ObjectDeleteMixin, View):
    model = Post
    template = 'news/post_delete_form.html'
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
    if request.method == 'POST' and 'keyword_search' in request.POST:
        search_queryes = dict()
        res = []
        test = request.POST
        print('test', test)
        if request.POST['Name']:
            res = list(Spectrum.objects.filter(name__icontains=request.POST['Name']))
            print('res', res)
            search_queryes.update({'Название': request.POST['Name']})
        if request.POST['Formula']:
            res2 = Metadata.objects.filter(value__icontains=request.POST['Formula']).values_list('spectrum', flat=True)
            print('res2', res2)
            search_queryes.update({'Формула': request.POST['Formula']})
            for item in res2:
                res.append(Spectrum.objects.get(id=item))
        print('res_before', res)
        res_set = set(res)

        if res:
            res_set = set(res)
            print('res_after', res_set)

            def map_spectrum(spectrum: Spectrum):
                precursor_type = Metadata.objects.filter(spectrum_id=spectrum.id, name='Precursor_type')
                spectrum_type = Metadata.objects.filter(spectrum_id=spectrum.id, name='Spectrum_type')
                precursor_mz = Metadata.objects.filter(spectrum_id=spectrum.id, name='PrecursorMZ')
                instrument_type = Metadata.objects.filter(spectrum_id=spectrum.id, name='Instrument_type')
                ion_mode = Metadata.objects.filter(spectrum_id=spectrum.id, name='Ion_mode')
                collision_energy = Metadata.objects.filter(spectrum_id=spectrum.id, name='Collision_energy')
                formula = Metadata.objects.filter(spectrum_id=spectrum.id, name='Formula')

                fields = [precursor_type, spectrum_type, precursor_mz, instrument_type, ion_mode, collision_energy,
                          formula]
                peaks_list = spectrum.spectrum_json

                plot_div = generate_spectrum_mini_plot(peaks_list=peaks_list)

                return {
                    'plot_div': plot_div,
                    'name': spectrum.name,
                    'id': spectrum.id,
                    'author': spectrum.author,
                    'create_date': spectrum.date_created,
                    'fields': fields
                }

            objects = list(map(map_spectrum, res_set))
            return render(request, 'spectra/spectrum_search_result.html',
                          context={'objects': objects, 'search_queryes': search_queryes})
        else:
            return render(request, 'spectra/spectrum_search_result.html',
                          context={'objects': res, 'search_queryes': search_queryes})
    return render(request, 'spectra/query/search.html', context={'context': context})


def spectrum_list(request):
    def map_spectrum(spectrum: Spectrum):
        precursor_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Precursor_type')
        spectrum_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Spectrum_type')
        precursor_mz = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='PrecursorMZ')
        instrument_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Instrument_type')
        ion_mode = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Ion_mode')
        collision_energy = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Collision_energy')
        formula = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Formula')

        fields = [precursor_type, spectrum_type, precursor_mz, instrument_type, ion_mode, collision_energy, formula]
        peaks_list = spectrum.spectrum_json

        plot_div = generate_spectrum_mini_plot(peaks_list=peaks_list)

        return {
            'spectrum': spectrum,
            'plot_div': plot_div,
            'name': spectrum.name,
            'id': spectrum.id,
            'author': spectrum.author,
            'create_date': spectrum.date_created,
            'fields': fields
        }

    spectrums = Spectrum.objects.filter(draft=False)
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


# @login_required()
@user_passes_test(check_admin)
def spectrum_draft_list(request):
    def map_spectrum(spectrum: Spectrum):
        precursor_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Precursor_type')
        spectrum_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Spectrum_type')
        precursor_mz = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='PrecursorMZ')
        instrument_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Instrument_type')
        ion_mode = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Ion_mode')
        collision_energy = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Collision_energy')
        formula = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Formula')

        fields = [precursor_type, spectrum_type, precursor_mz, instrument_type, ion_mode, collision_energy, formula]
        peaks_list = spectrum.spectrum_json

        plot_div = generate_spectrum_mini_plot(peaks_list=peaks_list)

        return {
            'spectrum': spectrum,
            'plot_div': plot_div,
            'name': spectrum.name,
            'id': spectrum.id,
            'author': spectrum.author,
            'create_date': spectrum.date_created,
            'fields': fields
        }

    spectrums = Spectrum.objects.filter(draft=True)
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
                print(request.POST['reject_reason'])
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


class UploadSpectrum(SpectrumMixin, View):

    def upload_spectrum(self, request):
        if request.method == 'POST':
            if request.POST.get('_method', None) == "DELETE":
                return redirect('spectra/upload/upload_file.html')
            if request.POST.get('_method', None) == "CREATE":
                try:
                    save_object(request)
                    messages.success(request, 'Ваша запись успешно добавлена!')
                    return redirect('upload_result')
                except ValidationError:
                    messages.error(request, 'Пожалуйста, исправьте ошибки.')

            if 'file' in request.FILES:
                spectrum_prepare(request)
                # file = request.FILES['file']
                # file_content = BytesIO(file.read())
                #
                # metadata = {}
                # peaks_list = []
                # for line in file_content:
                #     item = line.decode('utf8').replace("'", '"')
                #
                #     if re.match(r'([0-9]*\.?[0-9]+)\s*:\s*([0-9]*\.?[0-9]+)', item) or re.match(
                #             r'([0-9]+\.?[0-9]*)[ \t]+([0-9]*\.?[0-9]+)(?:\s*(?:[;\n])|(?:"?(.+)"?\n?))?', item):
                #
                #         ion = item.strip().replace("\t", ' ').split(' ')
                #
                #         d = [float(ion[0]), float(ion[1])]
                #
                #         peaks_list.append(d)
                #
                #     else:
                #         item = item.split(':')
                #         metadata.update({item[0].lower(): item[1].strip()})
                #
                # plot_div = generate_spectrum_plot(peaks_list=peaks_list)
                #
                # context = {'peaks_list': peaks_list,
                #            'plot_div': plot_div,
                #            'metadata': metadata}
                #
                # # return redirect('upload_peaks', id=measurement.id)
                # # return redirect('upload_peaks', id=spectrum.id)
                # # return redirect('upload_peaks', ions=ions)
                # return render(request, 'spectra/upload/spectrum_create_form.html', context=context)

            if 'pastedSpectrum' in request.POST:
                spectrum_prepare(request)
                # print('rew', request.POST)
                # try:
                #     SpectrumSaver().save_object(request)
                #     messages.success(request, 'Ваша запись успешно добавлена!')
                #     return redirect('upload_result')
                # except ValidationError:
                #     messages.error(request, 'Пожалуйста, исправьте ошибки.')

        return render(request, 'spectra/upload/upload_file.html')


def upload_metadata(request, id):
    def get_value(d: dict, name: str):
        s = d.get(name, None)
        if s is None:
            return None
        return int(s)

    object = SpectrumMeasurement.objects.filter(spectrum_id=id)

    if request.method == "POST":
        SpectrumMeasurement.objects.filter(spectrum_id=id).delete()
        if not object:
            object = SpectrumMeasurement.objects.create(spectrum_id=id)
        object.source = get_value(request.POST, "source")
        object.level = get_value(request.POST, "level")
        object.ionization = get_value(request.POST, "ionization")
        object.polarity = get_value(request.POST, "polarity")
        object.save()
        return redirect('upload_fields', id=id)

    return render(request, 'spectra/upload/metadata.html', {"id": id, "obj": object})


def upload_fields(request, id):
    if request.method == "POST":
        # SpectrumField.objects.filter(measurement_id=id).delete()
        SpectrumField.objects.filter(spectrum_id=id).delete()
        # metadata_list = []

        # field = SpectrumField.objects.create(spectrum_id=id)
        for i in range(0, 100):
            key = request.POST.get("key%d" % i, None)
            if key is None:
                continue
            value = request.POST.get("value%d" % i, None)

            field = SpectrumField.objects.create(spectrum_id=id)
            # field = SpectrumField.objects.create(id=id)
            # metadata_list.append([key, value])
            field.key = key
            field.value = value
            field.save()
        # field.meta_data = metadata_list
        # field.save()

        return redirect('upload_review', id=id)

    # fields = SpectrumField.objects.filter(measurement_id=id)
    fields = SpectrumField.objects.filter(spectrum_id=id)
    return render(request, 'spectra/upload/fields.html', {'fields': fields, "id": id})


# def generate_spectrum_plot(peaks_list: list, id: str | int = None, save_image: bool = False):
#     layout = {
#         "plot_bgcolor": '#fff',
#         "xaxis": {
#             "title": "m/z, Da" if not save_image else None,
#             "ticklen": 5,
#             "tickwidth": 1,
#             "ticks": "outside",
#             "showgrid": True if not save_image else False,
#             "linecolor": '#DCDCDC',
#             "gridcolor": '#F5F5F5',
#             "tickcolor": 'white',
#             "tickfont": {'color': '#696969'}
#         },
#         "yaxis": {
#             "title": "Intensity, cps" if not save_image else None,
#             "ticklen": 5,
#             "tickwidth": 1,
#             "ticks": "outside",
#             "showgrid": True if not save_image else None,
#             "linecolor": '#DCDCDC',
#             "gridcolor": '#F5F5F5',
#             "tickcolor": 'white',
#             "tickfont": {'color': '#696969'}
#         },
#         "hoverlabel": {
#             "bgcolor": "white",
#             "font_size": 14,
#             "font_family": "sans-serif"
#         }
#     }
#     peaks_values = {
#         "x": list(map(lambda p: p[0], peaks_list)),
#         "y": list(map(lambda p: p[1], peaks_list)),
#     }
#
#     p = pymzml.plot.Factory()
#     p.new_plot()
#     spectrum_plot = p.add(peaks_list, color=(30, 144, 255), style="sticks", name="peaks")
#     fig = Figure(data=spectrum_plot, layout=layout)
#
#     if save_image:
#         if not os.path.exists(os.path.join(BASE_DIR, 'staticfiles/plots')):
#             os.mkdir(os.path.join(BASE_DIR, 'staticfiles/plots'))
#         filename = os.path.join(BASE_DIR, 'staticfiles/plots/plot-%d.png' % id)
#         fig.write_image(format='png', file=filename)
#
#     else:
#         result = get_5_largest(peaks_values['y'])
#
#         for i in range(len(result)):
#             fig.add_annotation(x=peaks_values['x'][result[i]], y=peaks_values['y'][result[i]],
#                                text=peaks_values['x'][result[i]],
#                                showarrow=False,
#                                yshift=10)
#         fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
#
#         plot_div = plot(fig, output_type='div', include_plotlyjs=True,
#                         show_link=False, link_text="")
#
#         return plot_div
#
#
# def generate_spectrum_mini_plot(peaks_list: list):
#     layout = {
#         "plot_bgcolor": '#fff',
#         "xaxis": {
#             "ticklen": 5,
#             "tickwidth": 1,
#             "ticks": "outside",
#             "linecolor": '#DCDCDC',
#             "tickcolor": 'white',
#             "tickfont": {'color': '#696969'}
#         },
#         "yaxis": {
#             "ticklen": 5,
#             "tickwidth": 1,
#             "ticks": "outside",
#             "linecolor": '#DCDCDC',
#             "tickcolor": 'white',
#             "tickfont": {'color': '#696969'}
#         }
#     }
#
#     p = pymzml.plot.Factory()
#     p.new_plot()
#     spectrum_plot = p.add(peaks_list, color=(30, 144, 255), style="sticks", name="peaks")
#     fig = Figure(data=spectrum_plot, layout=layout)
#     fig.update_traces(hoverinfo='skip')
#     fig.update_layout(width=400, height=300, margin={"l": 0, "r": 0, "t": 0, "b": 0})
#
#     plot_div = plot(fig, output_type='div', include_plotlyjs=True,
#                     show_link=False, link_text="", config=dict(displayModeBar=False))
#
#     return plot_div


def upload_peaks(request, id):
    if request.method == "POST":
        if request.POST.get('_method', None) == "DELETE":
            # SpectrumMeasurement.objects.get(id=id).delete()
            Spectrum.objects.get(id=id).delete()
            return redirect('upload')

        # SpectrumPeak.objects.filter(measurement_id=id).delete()
        SpectrumPeak.objects.filter(spectrum_id=id).delete()
        i = 0
        peaks_values = dict()
        peaks_x = []
        peaks_y = []
        while True:
            x = request.POST.get("x%d" % i, None)
            if x is None:
                break
            y = request.POST.get("y%d" % i, None)
            comment = request.POST.get("comment%d" % i, "")
            active = request.POST.get("active%d" % i)
            if active != 'on':
                i += 1
                continue

            x = x.replace(',', '.')
            y = y.replace(',', '.')
            peak = SpectrumPeak.objects.create(spectrum_id=id, x=float(x), y=float(y), comment=comment)

            # peak = spectrum.peaks.objects.create(peaks_data=float(x), y=float(y), comment=comment)
            peak.save()

            # peaks_x.append(float(x))
            # peaks_y.append(float(y))
            # d = {"x": peaks_x, "y": peaks_y}
            #
            # peaks_values.update(d)

            i += 1
        # peaks_items = SpectrumPeak.objects.create(spectrum_id=id, peaks_data=peaks_values)
        # peaks_items.save()

        return redirect('upload_metadata', id=id)

    peaks_list = SpectrumPeak.objects.filter(spectrum_id=id)

    # peaks_values = peaks[0].peaks_data
    #
    # peaks_list = []
    # for i in range(len(peaks_values['x'])):
    #     peaks_list.append([peaks_values['x'][i], peaks_values['y'][i]])

    # print('fddf', peaks_list)
    #
    # peaks_values = dict()
    # peaks_x = []
    # peaks_y = []
    # for peak in peaks_list:
    #     peaks_x.append(float(peak[0]))
    #     peaks_y.append(float(peak[1]))
    #     d = {"x": peaks_x, "y": peaks_y}
    #
    #     peaks_values.update(d)

    peaks_values = {
        "x": list(map(lambda p: p.x, peaks)),
        "y": list(map(lambda p: p.y, peaks)),
    }
    plot_div = SpectrumPlot().generate_spectrum_plot(peaks_list=peaks_list)

    return render(request, 'spectra/upload/peaks.html', {'plot_div': plot_div, 'peaks': peaks})


def upload_review(request, id):
    # measurement = SpectrumMeasurement.objects.get(id=id)
    # peaks = SpectrumPeak.objects.filter(measurement_id=id)
    # fields = SpectrumField.objects.filter(measurement_id=id)
    spectrum = Spectrum.objects.get(id=id)
    measurement = SpectrumMeasurement.objects.filter(spectrum_id=id)[0]
    peaks = SpectrumPeak.objects.filter(spectrum_id=id)
    fields = SpectrumField.objects.filter(spectrum_id=id)

    peaks_values = {
        "x": list(map(lambda p: p.x, peaks)),
        "y": list(map(lambda p: p.y, peaks)),
    }

    plot_div = generate_spectrum_plot(peaks_values=peaks_values)

    name = "Spectrum #%d" % spectrum.id
    name_field = SpectrumField.objects.filter(
        spectrum=spectrum, key="Name").first()
    if name_field is not None:
        name = name_field.value

    context = {
        'name': name,
        'plot_div': plot_div,
        'peaks': peaks,
        'fields': fields,
        'id': id,
        'source': sources[measurement.source],
        'level': levels[measurement.level],
        'ionization': ionzations[measurement.ionization],
        'polarity': polarities[measurement.polarity],
    }
    Spectrum.objects.filter(id=id).update(name=name)
    generate_spectrum_plot(peaks_values=peaks_values, id=id, save_image=True)

    return render(request, 'spectra/upload/review.html', context)


def create_spectrum(request, data):
    print('data', data)

    def get_5_largest(intensity_list: list[float]) -> list[int]:
        """
        Returns the indices of the 5 largest ion intensities.

        :param intensity_list: List of Ion intensities
        """

        largest = [0, 0, 0, 0, 0]

        print('intensity_list', intensity_list)

        # Find out largest value
        for idx, intensity in enumerate(intensity_list):
            if intensity > intensity_list[largest[0]]:
                largest[0] = idx

        # Now find next four largest values
        for j in [1, 2, 3, 4]:
            for idx, intensity in enumerate(intensity_list):
                # if intensity_list[i] > intensity_list[largest[j]] and intensity_list[i] < intensity_list[largest[j-1]]:
                if intensity_list[largest[j]] < intensity < intensity_list[largest[j - 1]]:
                    largest[j] = idx
        print('largest', largest)

        return largest

    trace1 = {
        "x": [74.03,
              100.13,
              133.06,
              134.06,
              133.06,
              162.13,
              177.17,
              178.97,
              185.17,
              212.13,
              213.10,
              214.94,
              226.32,
              241.11,
              256.09,
              257.74,
              258.26,
              259.84,
              329.11,
              331.08],
        "y": [0.39,
              1.29,
              1.00,
              0.50,
              2.55,
              1.22,
              6.77,
              0.52,
              0.73,
              8.49,
              17.80,
              1.50,
              0.36,
              1.14,
              39.05,
              3.13,
              1.89,
              0.45,
              20.05,
              1.39]
    }

    result = get_5_largest(trace1['y'])

    trace_len = len(trace1['x'])
    test_data = []
    for i in range(trace_len):
        test_data.append([trace1['x'][i], trace1['y'][i]])

    layout = {
        # "title": "Mass Spectrum for scan 13332",
        "plot_bgcolor": '#fff',
        "xaxis": {
            "title": "m/z, Da",
            "ticklen": 5,
            "tickwidth": 1,
            "ticks": "outside",
            "showgrid": True,
            "linecolor": '#DCDCDC',
            "gridcolor": '#F5F5F5',
            "tickcolor": 'white',
            "tickfont": {'color': '#696969'}
        },
        "yaxis": {
            "title": "Intensity, cps",
            "ticklen": 5,
            "tickwidth": 1,
            "ticks": "outside",
            "showgrid": True,
            "linecolor": '#DCDCDC',
            "gridcolor": '#F5F5F5',
            "tickcolor": 'white',
            "tickfont": {'color': '#696969'}
        },
        "hoverlabel": {
            "bgcolor": "white",
            "font_size": 14,
            "font_family": "sans-serif"
        }
    }

    p = pymzml.plot.Factory()

    p.new_plot()
    test = p.add(test_data, color=(30, 144, 255), style="sticks", name="peaks")

    test_plot = test

    fig = Figure(data=test_plot, layout=layout)
    for i in range(len(result)):
        fig.add_annotation(x=trace1['x'][result[i]], y=trace1['y'][result[i]],
                           text=trace1['x'][result[i]],
                           showarrow=False,
                           yshift=10)

    plot_div = plot(fig, output_type='div', include_plotlyjs=True,
                    show_link=False, link_text="")
    return render(request, "spectra/display/viewSpectrum.html", context={'plot_div': plot_div})


def view_spectrum1(request):
    def get_5_largest(intensity_list: list[float]) -> list[int]:
        """
        Returns the indices of the 5 largest ion intensities.

        :param intensity_list: List of Ion intensities
        """

        largest = [0, 0, 0, 0, 0]

        print('intensity_list', intensity_list)

        # Find out largest value
        for idx, intensity in enumerate(intensity_list):
            if intensity > intensity_list[largest[0]]:
                largest[0] = idx

        # Now find next four largest values
        for j in [1, 2, 3, 4]:
            for idx, intensity in enumerate(intensity_list):
                # if intensity_list[i] > intensity_list[largest[j]] and intensity_list[i] < intensity_list[largest[j-1]]:
                if intensity_list[largest[j]] < intensity < intensity_list[largest[j - 1]]:
                    largest[j] = idx
        print('largest', largest)

        return largest

    trace1 = {
        "x": [74.03,
              100.13,
              133.06,
              134.06,
              133.06,
              162.13,
              177.17,
              178.97,
              185.17,
              212.13,
              213.10,
              214.94,
              226.32,
              241.11,
              256.09,
              257.74,
              258.26,
              259.84,
              329.11,
              331.08],
        "y": [0.39,
              1.29,
              1.00,
              0.50,
              2.55,
              1.22,
              6.77,
              0.52,
              0.73,
              8.49,
              17.80,
              1.50,
              0.36,
              1.14,
              39.05,
              3.13,
              1.89,
              0.45,
              20.05,
              1.39]
    }

    result = get_5_largest(trace1['y'])
    print('result', result)

    trace_len = len(trace1['x'])
    test_data = []
    for i in range(trace_len):
        test_data.append([trace1['x'][i], trace1['y'][i]])

    print('test', test_data)

    # data = Figure([trace1])

    # fig = Figure(data=data, layout=layout)
    # plot_div = py.plot(fig)

    """
    This script shows how to plot multiple spectra in one plot and
    how to use label for the annotation of spectra.
    The first plot is an MS1 spectrum with the annotated precursor ion.
    The second plot is a zoom into the precursor isotope pattern.
    The third plot is an annotated fragmentation spectrum (MS2) of the
    peptide HLVDEPQNLIK from BSA.
    These examples also show the use of 'layout' to define the appearance
    of a plot.
    usage:
        ./plot_spectrum_with_annotation.py
    """

    # First we define some general layout attributes
    layout = {
        # "title": "Mass Spectrum for scan 13332",
        "plot_bgcolor": '#fff',
        "xaxis": {
            "title": "m/z, Da",
            "ticklen": 5,
            "tickwidth": 1,
            "ticks": "outside",
            "showgrid": True,
            "linecolor": '#DCDCDC',
            "gridcolor": '#F5F5F5',
            "tickcolor": 'white',
            "tickfont": {'color': '#696969'}
        },
        "yaxis": {
            "title": "Intensity, cps",
            "ticklen": 5,
            "tickwidth": 1,
            "ticks": "outside",
            "showgrid": True,
            "linecolor": '#DCDCDC',
            "gridcolor": '#F5F5F5',
            "tickcolor": 'white',
            "tickfont": {'color': '#696969'}
        },
        "hoverlabel": {
            "bgcolor": "white",
            "font_size": 14,
            "font_family": "sans-serif"
        }
    }

    # The example BSA file will be used

    data_directory = pathlib.Path(".").resolve().parent / "pyms-data"
    # Change this if the data files are stored in a different location

    example_file = data_directory / "BSA1.mzML.gz"

    # run = pymzml.run.Reader(example_file)
    p = pymzml.plot.Factory()

    # print('run', run)
    test_plot = ''
    # for spec in run:
    #     print('spec', spec)
    #     for mz, i in spec.highest_peaks(5):
    #         print(mz, i)

    #    data = [[3.00089765e+02, 3.43102612e+03],
    # [3.00181327e+02, 1.18180896e+03],
    # [3.00202675e+02, 1.51617456e+03],
    # [3.00298289e+02, 1.71985474e+03],
    # [3.00334598e+02, 1.11525964e+03],
    # [3.01141460e+02, 4.06243359e+04],
    # [3.01216728e+02, 1.44548083e+03],
    # [3.01273990e+02, 1.02758801e+03],
    # [3.01987541e+02, 2.08935547e+03],
    # [3.02009014e+02, 1.02140710e+03],
    # [3.02044972e+02, 2.55872314e+03],
    # [3.02081653e+02, 1.08234814e+03],
    # [3.02144804e+02, 3.78598608e+03],
    # [3.02160047e+02, 1.50109509e+03],
    # [3.02196406e+02, 1.15957288e+03]
    # ]

    p.new_plot()
    test = p.add(test_data, color=(30, 144, 255), style="sticks", name="peaks")

    # filename = "example_plot_{0}_{1}.html".format(
    #     os.path.basename(example_file), spec.ID
    # )
    # p.save(
    #     filename=filename,
    #     layout=layout,
    # )
    # print("Plotted file: {0}".format(filename))

    print('p', test)

    print('testttttt', p.get_data())
    test_plot = test

    # break

    # fig = Figure(data=[Bar(
    #     x=trace1['x'],
    #     y=trace1['y'],
    #     width=1, base='lines'
    # )], layout=layout)

    # fig.show()
    fig = Figure(data=test_plot, layout=layout)
    # fig.update_traces(hovertemplate='m/z=%{x}<br>Intensity=%{y}')
    # fig.update_layout(
    #     hoverlabel=dict(
    #         bgcolor="white",
    #         font_size=14,
    #         font_family="Rockwell"
    #     )
    # )
    for i in range(len(result)):
        fig.add_annotation(x=trace1['x'][result[i]], y=trace1['y'][result[i]],
                           text=trace1['x'][result[i]],
                           showarrow=False,
                           yshift=10)
    # fig.update_layout(plot_bgcolor='#fff')
    # fig.update_xaxes(showline=True, linewidth=1, linecolor='#DCDCDC', gridcolor='#F5F5F5', tickcolor='white', tickfont={'color': '#696969'})
    # fig.update_yaxes(showline=True, linewidth=1, linecolor='#DCDCDC', gridcolor='#F5F5F5', tickcolor='white', tickfont={'color': '#696969'})
    # fig.update_yaxes(showline=True, linewidth=1, linecolor='#DCDCDC', gridcolor='#F5F5F5', griddash='longdash', tickcolor='white', tickfont={'color': '#696969'})

    # plot_div = plot(fig, output_type='div', include_plotlyjs=True, show_link=False, link_text="", config=dict(displayModeBar=False))
    plot_div = plot(fig, output_type='div', include_plotlyjs=True,
                    show_link=False, link_text="")
    return render(request, "spectra/display/viewSpectrum.html", context={'plot_div': plot_div})
