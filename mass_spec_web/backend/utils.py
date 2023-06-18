import os
import re
from datetime import datetime
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

from .models import SpectrumMeasurement, Spectrum, Metadata
from io import BytesIO

import pymzml

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from plotly.offline import plot
from plotly.graph_objs import Figure

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


class UserDetailMixin:
    model = None
    template = None

    def get(self, request, username):
        obj = get_object_or_404(self.model, username__iexact=username)

        spectrums = Spectrum.objects.filter(author=request.user)

        context = {
            self.model.__name__.lower(): obj,
            'admin_object': obj,
            'spectrums': spectrums
        }
        return render(request, self.template, context=context)


class UserUpdateMixin:
    model = None
    model_form = None
    template = None

    def get(self, request, username):
        obj = self.model.objects.get(username__iexact=username)
        bound_form = self.model_form(instance=obj)
        return render(request, self.template, context={'form': bound_form, self.model.__name__.lower(): obj})

    def post(self, request, username):
        obj = self.model.objects.get(username__iexact=username)
        bound_form = self.model_form(request.POST, instance=obj)

        if bound_form.is_valid():
            new_obj = bound_form.save()
            return redirect(new_obj)
        return render(request, self.template, context={'form': bound_form, self.model.__name__.lower(): obj})


class ObjectDetailMixin:
    model = None
    template = None

    def get(self, request, id):
        obj = get_object_or_404(self.model, id=id)
        return render(request, self.template, context={self.model.__name__.lower(): obj, 'admin_object': obj})


class ObjectCreateMixin:
    model_form = None
    template = None

    def get(self, request):
        form = self.model_form()
        return render(request, self.template, context={'form': form})

    def post(self, request):
        bound_form = self.model_form(request.POST)

        if bound_form.is_valid():
            new_obj = bound_form.save()
            return redirect(new_obj)
        return render(request, self.template, context={'form': bound_form})


class ObjectUpdateMixin:
    model = None
    model_form = None
    template = None

    def get(self, request, id):
        obj = self.model.objects.get(id=id)
        bound_form = self.model_form(instance=obj)
        return render(request, self.template, context={'form': bound_form, self.model.__name__.lower(): obj})

    def post(self, request, id):
        obj = self.model.objects.get(id=id)
        bound_form = self.model_form(request.POST, instance=obj)

        if bound_form.is_valid():
            new_obj = bound_form.save()
            return redirect(new_obj)
        return render(request, self.template, context={'form': bound_form, self.model.__name__.lower(): obj})


class ObjectDeleteMixin:
    model = None
    template = None
    redirect_url = None

    def get(self, request, id):
        obj = self.model.objects.get(id=id)
        return render(request, self.template, context={self.model.__name__.lower(): obj})

    def post(self, request, id):
        obj = self.model.objects.get(id=id)
        obj.delete()
        return redirect(reverse(self.redirect_url))


class SpectrumUpdateMixin:
    model = None
    template = None

    def get(self, request, id):
        obj = self.model.objects.get(id=id)
        if obj.draft:
            measurement = SpectrumMeasurement.objects.filter(spectrum_id=id)[0]
            peaks_list = obj.spectrum_json
            metadata = Metadata.objects.filter(spectrum_id=id)
            plot_div = generate_spectrum_plot(peaks_list=peaks_list)

            context = {
                'spectrum': obj,
                'plot_div': plot_div,
                'peaks_list': peaks_list,
                'metadata': metadata,
                'source': measurement.source,
                'level': measurement.level,
                'ionization': measurement.ionization,
                'polarity': measurement.polarity,
            }
            return render(request, self.template, context=context)
        else:
            return redirect('spectrum_detail_url', obj.id)

    def post(self, request, id):

        if request.POST.get('_method', None) == "CANCEL":
            return redirect('spectrum_detail_url', id)

        obj = self.model.objects.get(id=id)
        obj.name = request.POST.get("Name")
        obj.reg_num = request.POST.get("Number")
        obj.formula = request.POST.get("Formula")
        obj.cas = request.POST.get("Cas")
        obj.exact_mass = request.POST.get("Exact_mass")

        i = 0
        peaks = ''
        peaks_list = []
        while True:
            x = request.POST.get("x%d" % i, None)
            if x is None:
                break
            y = request.POST.get("y%d" % i, None)
            active = request.POST.get("active%d" % i)
            if active != 'on':
                i += 1
                continue

            x = x.replace(',', '.')
            y = y.replace(',', '.')
            peaks += f'{x}:{y} '
            peaks_list.append([float(x), float(y)])

            i += 1

        obj.spectrum = peaks.rstrip(' ')
        obj.spectrum_json = peaks_list

        fields_list = []
        saved_fields = []

        fields = Metadata.objects.filter(spectrum_id=obj.id)
        for field in fields:
            saved_fields.append(field.name.lower())
        for i in range(0, 30):
            key = request.POST.get("key%d" % i, None)
            if key is None:
                continue
            value = request.POST.get("value%d" % i, None)

            if key.lower() in saved_fields:
                field = Metadata.objects.get(spectrum_id=obj.id, name__iexact=key)
                item = {'name': key, 'value': value}
                fields_list.append(item)
                field.name = key
                field.value = value
                field.save()
                saved_fields.remove(key.lower())
            else:
                field = Metadata.objects.create(spectrum_id=obj.id)
                item = {'name': key, 'value': value}
                fields_list.append(item)
                field.name = key
                field.value = value
                field.save()

        if saved_fields:
            for item in saved_fields:
                field = Metadata.objects.get(spectrum_id=obj.id, name__iexact=item)
                field.delete()

        measurements = SpectrumMeasurement.objects.get(spectrum_id=obj.id)
        measurements.source = request.POST.get("source")
        measurements.level = request.POST.get("level")
        measurements.ionization = request.POST.get("ionization")
        measurements.polarity = request.POST.get("polarity")
        measurements.save()

        measurement_list = ["source", "level", "ionization", "polarity"]
        for meas in measurement_list:
            value = request.POST.get(meas)
            item = {'name': meas, 'value': value}
            fields_list.append(item)

        obj.metaDataMap = fields_list
        obj.date_updated = datetime.now()
        obj.save()

        generate_spectrum_mini_plot(peaks_list=peaks_list, save_image=True, id=obj.id)

        return redirect('spectrum_detail_url', obj.id)


class SpectrumDeleteMixin:
    model = None
    template = None
    redirect_url = None

    def get(self, request, id):
        obj = self.model.objects.get(id=id)
        return render(request, self.template, context={self.model.__name__.lower(): obj})

    def post(self, request, id):
        obj = self.model.objects.get(id=id)
        obj.delete()
        return redirect(reverse(self.redirect_url))


class SpectrumMixin:
    def get(self, request):
        print('request.path', request.path)
        return render(request, 'spectra/upload/upload_file.html')

    def post(self, request):
        metadata = {}
        peaks_list = []

        if request.POST.get('_method', None) == "CREATE":
            try:
                save_object(request)
                messages.success(request, 'Ваша запись успешно добавлена!')
                return redirect('upload_result')
            except ValidationError as error:
                messages.error(request, error)
                return

        if request.POST.get('_method', None) == "DELETE":
            return redirect('upload')

        if 'file' in request.FILES:
            file = request.FILES['file']
            file_content = BytesIO(file.read())

            for line in file_content:
                item = line.decode('utf8').replace("'", '"')
                try:
                    if re.match(r'([0-9]*\.?[0-9]+)\s*:\s*([0-9]*\.?[0-9]+)', item) or re.match(
                            r'([0-9]+\.?[0-9]*)[ \t]+([0-9]*\.?[0-9]+)(?:\s*(?:[;\n])|(?:"?(.+)"?\n?))?', item):

                        ion = item.strip().replace("\t", ' ').split(' ')
                        peaks_list.append([float(ion[0]), float(ion[1])])

                    else:
                        item = item.split(':')
                        metadata.update({item[0].lower(): item[1].strip()})
                except:
                    messages.error(request, f'Невозможно загрузить масс-спектр. Проверьте передаваемые данные.')
                    return redirect('upload')

            if not peaks_list:
                messages.error(request, 'Невозможно загрузить масс-спектр. Проверьте передаваемые данные. Отсутствуют данные о спектре.')
                return redirect('upload')

            plot_div = generate_spectrum_plot(peaks_list=peaks_list)

            context = {'peaks_list': peaks_list,
                       'plot_div': plot_div,
                       'metadata': metadata}

            return render(request, 'spectra/upload/spectrum_create_form.html', context=context)

        if 'pastedSpectrum' in request.POST:
            if request.POST.get('pastedSpectrum'):
                try:
                    try:
                        peaks = [item.split(":") for item in request.POST.get('pastedSpectrum').split(' ') if item != '' and
                                 (re.match(r'([0-9]*\.?[0-9]+)\s*:\s*([0-9]*\.?[0-9]+)', item))]

                        if not peaks:
                            assert False
                        sorted_peaks = sorted(peaks, key=lambda peak: float(peak[0]))
                        for item in sorted_peaks:
                            peaks_list.append([float(item[0]), float(item[1])])

                    except AssertionError:
                        for line in request.POST.get('pastedSpectrum').splitlines():

                            item = line.replace("'", '"')
                            item = " ".join(item.split())
                            if re.match(r'([0-9]*\.?[0-9]+)\s*:\s*([0-9]*\.?[0-9]+)', item) or re.match(
                                    r'([0-9]+\.?[0-9]*)[ \t]+([0-9]*\.?[0-9]+)(?:\s*(?:[;\n])|(?:"?(.+)"?\n?))?', item):
                                ion = item.strip().replace("\t", ' ').split(' ')
                                peaks_list.append([float(ion[0]), float(ion[1])])

                    plot_div = generate_spectrum_plot(peaks_list=peaks_list)

                    context = {'peaks_list': peaks_list,
                               'plot_div': plot_div,
                               'metadata': metadata}

                    return render(request, 'spectra/upload/spectrum_create_form.html', context=context)

                except:
                    messages.error(request, 'Невозможно загрузить масс-спектр. Проверьте передаваемые данные')
                    return redirect('upload')

            else:
                messages.error(request, 'Невозможно загрузить масс-спектр. Проверьте передаваемые данные')
                return redirect('upload')


def save_object(request):
    obj = Spectrum.objects.create()
    obj.author = request.user
    obj.name = request.POST.get("Name")
    obj.reg_num = request.POST.get("Number")
    obj.formula = request.POST.get("Formula")
    obj.cas = request.POST.get("Cas")
    obj.exact_mass = request.POST.get("Exact_mass")

    i = 0
    peaks = ''
    peaks_list = []
    while True:
        x = request.POST.get("x%d" % i, None)
        if x is None:
            break
        y = request.POST.get("y%d" % i, None)
        active = request.POST.get("active%d" % i)
        if active != 'on':
            i += 1
            continue

        x = x.replace(',', '.')
        y = y.replace(',', '.')
        peaks += f'{x}:{y} '
        peaks_list.append([float(x), float(y)])

        i += 1
    if not peaks_list:
        messages.error(request, 'Не выбраны пики для спектра')

    obj.spectrum = peaks.rstrip(' ')
    obj.spectrum_json = peaks_list

    fields_list = []
    for i in range(0, 100):
        key = request.POST.get("key%d" % i, None)
        if key is None:
            continue
        value = request.POST.get("value%d" % i, None)

        field = Metadata.objects.create(spectrum_id=obj.id)
        item = {'name': key, 'value': value}
        fields_list.append(item)
        field.name = key
        field.value = value
        field.save()

    measurements = SpectrumMeasurement.objects.create(spectrum_id=obj.id)
    measurements.source = request.POST.get("source")
    measurements.level = request.POST.get("level")
    measurements.ionization = request.POST.get("ionization")
    measurements.polarity = request.POST.get("polarity")
    measurements.save()

    measurement_list = ["source", "level", "ionization", "polarity"]
    for meas in measurement_list:
        value = request.POST.get(meas)
        item = {'name': meas, 'value': value}
        fields_list.append(item)

    obj.metaDataMap = fields_list
    obj.save()

    generate_spectrum_mini_plot(peaks_list=peaks_list, save_image=True, id=obj.id)

    return obj


def get_5_largest(intensity_list: list[float]) -> list[int]:
    largest = [0, 0, 0, 0, 0]
    # Find out largest value
    for idx, intensity in enumerate(intensity_list):
        if intensity > intensity_list[largest[0]]:
            largest[0] = idx

    # Now find next four largest values
    for j in [1, 2, 3, 4]:
        for idx, intensity in enumerate(intensity_list):
            if intensity_list[largest[j]] < intensity < intensity_list[largest[j - 1]]:
                largest[j] = idx
    return largest


def generate_spectrum_plot(peaks_list: list):
    layout = {
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
    peaks_values = {
        "x": list(map(lambda p: p[0], peaks_list)),
        "y": list(map(lambda p: p[1], peaks_list)),
    }

    p = pymzml.plot.Factory()
    p.new_plot()
    spectrum_plot = p.add(peaks_list, color=(30, 144, 255), style="sticks", name="peaks")
    fig = Figure(data=spectrum_plot, layout=layout)

    result = get_5_largest(peaks_values['y'])

    for i in range(len(result)):
        fig.add_annotation(x=peaks_values['x'][result[i]], y=peaks_values['y'][result[i]],
                           text=peaks_values['x'][result[i]],
                           showarrow=False,
                           yshift=10)
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})

    plot_div = plot(fig, output_type='div', include_plotlyjs=True,
                    show_link=False, link_text="")

    return plot_div


def generate_spectrum_mini_plot(peaks_list: list, save_image: bool = False, id: str = None):
    layout = {
        "plot_bgcolor": '#fff',
        "xaxis": {
            "ticklen": 5,
            "tickwidth": 1,
            "ticks": "outside",
            "linecolor": '#DCDCDC',
            "tickcolor": 'white',
            "tickfont": {'color': '#696969'}
        },
        "yaxis": {
            "ticklen": 5,
            "tickwidth": 1,
            "ticks": "outside",
            "linecolor": '#DCDCDC',
            "tickcolor": 'white',
            "tickfont": {'color': '#696969'}
        }
    }

    p = pymzml.plot.Factory()
    p.new_plot()
    spectrum_plot = p.add(peaks_list, color=(30, 144, 255), style="sticks", name="peaks")
    fig = Figure(data=spectrum_plot, layout=layout)
    fig.update_traces(hoverinfo='skip')
    fig.update_layout(width=400, height=300, margin={"l": 0, "r": 0, "t": 0, "b": 0})

    if save_image:
        if not os.path.exists(os.path.join(BASE_DIR, 'staticfiles/plots')):
            os.mkdir(os.path.join(BASE_DIR, 'staticfiles/plots'))
        filename = os.path.join(BASE_DIR, 'staticfiles/plots/plot-%d.png' % id)
        fig.write_image(format='png', file=filename)

    plot_div = plot(fig, output_type='div', include_plotlyjs=True,
                    show_link=False, link_text="", config=dict(displayModeBar=False, staticPlot=True))

    return plot_div


def map_spectrum(spectrum: Spectrum):
    precursor_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Precursor_type')
    spectrum_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Spectrum_type')
    precursor_mz = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='PrecursorMZ')
    instrument_type = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Instrument_type')
    ion_mode = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Ion_mode')
    collision_energy = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Collision_energy')
    formula = Metadata.objects.filter(spectrum_id=spectrum.id, name__icontains='Formula')

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
