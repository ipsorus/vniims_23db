import os
from pathlib import Path
from .models import UserProfile, SpectrumMeasurement, SpectrumPeak, SpectrumField
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from . import forms
import numpy
from PIL import Image
from matplotlib import pyplot
import json
from io import BytesIO

import pymzml
from bootstrap_modal_forms.generic import BSModalCreateView, BSModalLoginView
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from plotly.offline import plot
from plotly.graph_objs import Figure

import pathlib
import matplotlib
matplotlib.use('Agg')

BASE_DIR = Path(__file__).resolve().parent.parent

# class SubmitterView(ReadOnlyModelViewSet):
#     queryset = Submitter.objects.all()
#     serializer_class = SubmitterSerializer
# from .permissions import IsOwnerProfileOrReadOnly

# class SubmitterView(ReadOnlyModelViewSet):
#     # authentication_classes = (SessionAuthentication, BasicAuthentication, TokenAuthentication)
#     # permission_classes = (
#     #     permissions.IsAuthenticatedOrReadOnly,
#     # )
#     queryset = UserProfile.objects.all()
#     serializer_class = SubmitterSerializer
#
#     def get(self, request, format=None):
#         content = {
#             'user': str(request.user),  # `django.contrib.auth.User` instance.
#             'auth': str(request.auth),  # None
#         }
#         return Response(content)
#
#     def post(self, request):
#         serializer = SubmitterSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#

#
#
# from rest_framework.generics import (ListCreateAPIView, RetrieveUpdateDestroyAPIView, )
# from rest_framework.permissions import IsAuthenticated
# from .models import UserProfile
#
# from .serializers import UserProfileSerializer
#
#
# # Create your views here.
#
# class UserProfileListCreateView(ListCreateAPIView):
#     authentication_classes = []
#     queryset = UserProfile.objects.all()
#     serializer_class = UserProfileSerializer
#     permission_classes = [AllowAny, IsAuthenticated]
#
#     @ensure_csrf_cookie
#     def perform_create(self, serializer):
#         user = self.request.user
#         serializer.save(user=user)
#
#
# class UserProfileDetailView(RetrieveUpdateDestroyAPIView):
#     authentication_classes = []
#     queryset = UserProfile.objects.all()
#     serializer_class = UserProfileSerializer
#     permission_classes = [AllowAny, IsOwnerProfileOrReadOnly, IsAuthenticated]
#
#
# class MyObtainTokenPairView(TokenObtainPairView):
#     permission_classes = (AllowAny,)
#     serializer_class = MyTokenObtainPairSerializer


# class Index(generic.ListView):
#     model = UserProfile
#     context_object_name = 'user'
#     template_name = 'index.html'


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


def get_5_largest(intensity_list: list[float]) -> list[int]:
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


class SignUpView(BSModalCreateView):
    form_class = CustomUserCreationForm
    template_name = 'authentication/signup.html'
    success_message = 'Вы успешно зарегистрированы. Авторизуйтесь.'
    success_url = reverse_lazy('upload')


class CustomLoginView(BSModalLoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'authentication/login.html'
    success_message = 'Вы успешно авторизовались.'
    success_url = reverse_lazy('display')


def main(request):
    return render(request, 'index.html')


def upload_spectrum(request):
    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']
        file_content = BytesIO(file.read())

        measurement = SpectrumMeasurement.objects.create()
        measurement.save()

        for line in file_content:
            item = line.decode('utf8').replace("'", '"').split(':')
            key, value = item[0], item[1].strip()

            if key.lower().startswith("peak"):
                x, y = value.split(' ')
                SpectrumPeak.objects.create(measurement=measurement, x=x, y=y)
            else:
                field = SpectrumField.objects.create(measurement=measurement)
                field.key = key
                field.value = value
                field.save()

        return redirect('upload_peaks', id=measurement.id)

    return render(request, 'spectra/upload/upload_file.html')


def upload_metadata(request, id):
    def get_value(d: dict, name: str):
        s = d.get(name, None)
        if s is None:
            return None
        return int(s)

    object = SpectrumMeasurement.objects.get(id=id)

    if request.method == "POST":
        object.source = get_value(request.POST, "source")
        object.level = get_value(request.POST, "level")
        object.ionization = get_value(request.POST, "ionization")
        object.polarity = get_value(request.POST, "polarity")
        object.save()
        return redirect('upload_fields', id=id)

    return render(request, 'spectra/upload/metadata.html', {"id": id, "obj": object})


def upload_fields(request, id):
    if request.method == "POST":
        SpectrumField.objects.filter(measurement_id=id).delete()

        for i in range(0, 100):
            key = request.POST.get("key%d" % i, None)
            if key is None:
                continue
            value = request.POST.get("value%d" % i, None)

            field = SpectrumField.objects.create(measurement_id=id)
            field.key = key
            field.value = value
            field.save()

        return redirect('upload_review', id=id)

    fields = SpectrumField.objects.filter(measurement_id=id)
    return render(request, 'spectra/upload/fields.html', {'fields': fields, "id": id})


def generate_plot(id):
    peaks = SpectrumPeak.objects.filter(measurement_id=id)
    x_axis = numpy.array(list(map(lambda p: p.x, peaks)))
    y_axis = numpy.array(list(map(lambda p: p.y, peaks)))

    fig = pyplot.figure()
    pyplot.bar(x_axis, y_axis)
    # fig.legend('')
    # pyplot.axis('off')
    filename = os.path.join(BASE_DIR, 'staticfiles/plots/plot-%d.png' % id)
    fig.savefig(filename, bbox_inches='tight')


def upload_peaks(request, id):
    if request.method == "POST":
        if request.POST.get('_method', None) == "DELETE":
            SpectrumMeasurement.objects.get(id=id).delete()
            return redirect('upload')

        SpectrumPeak.objects.filter(measurement_id=id).delete()
        i = 0

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
            peak = SpectrumPeak.objects.create(
                measurement_id=id, x=float(x), y=float(y), comment=comment)
            peak.save()

            i += 1

        generate_plot(id)

        return redirect('upload_metadata', id=id)

    peaks = SpectrumPeak.objects.filter(measurement_id=id)

    trace1 = {
        "x": list(map(lambda p: p.x, peaks)),
        "y": list(map(lambda p: p.y, peaks)),
    }

    result = get_5_largest(trace1['y'])

    test_data = []
    for i in range(len(trace1['x'])):
        test_data.append([trace1['x'][i], trace1['y'][i]])

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

    p = pymzml.plot.Factory()
    test_plot = ''

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

    return render(request, 'spectra/upload/peaks.html', {'plot_div': plot_div, 'peaks': peaks})


def upload_review(request, id):
    measurement = SpectrumMeasurement.objects.get(id=id)
    peaks = SpectrumPeak.objects.filter(measurement_id=id)
    fields = SpectrumField.objects.filter(measurement_id=id)

    trace1 = {
        "x": list(map(lambda p: p.x, peaks)),
        "y": list(map(lambda p: p.y, peaks)),
    }

    result = get_5_largest(trace1['y'])

    test_data = []
    for i in range(len(trace1['x'])):
        test_data.append([trace1['x'][i], trace1['y'][i]])

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

    p = pymzml.plot.Factory()
    test_plot = ''

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

    name = "Spectrum #%d" % measurement.id
    name_field = SpectrumField.objects.filter(
        measurement=measurement, key="Name").first()
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
    return render(request, 'spectra/upload/review.html', context)


def view_spectrum(request, id):
    measurement = SpectrumMeasurement.objects.get(id=id)
    peaks = SpectrumPeak.objects.filter(measurement_id=id)
    fields = SpectrumField.objects.filter(measurement_id=id)

    trace1 = {
        "x": list(map(lambda p: p.x, peaks)),
        "y": list(map(lambda p: p.y, peaks)),
    }

    result = get_5_largest(trace1['y'])

    test_data = []
    for i in range(len(trace1['x'])):
        test_data.append([trace1['x'][i], trace1['y'][i]])

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

    p = pymzml.plot.Factory()
    test_plot = ''

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

    name = "Spectrum #%d" % measurement.id
    name_field = SpectrumField.objects.filter(
        measurement=measurement, key="Name").first()
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
    return render(request, 'spectra/display/viewSpectrum1.html', context)

def spectrum_list(request):
    def map_measurement(measurement: SpectrumMeasurement):
        name = "Spectrum #%d" % measurement.id
        name_field = SpectrumField.objects.filter(
            measurement=measurement, key="Name").first()
        if name_field is not None:
            name = name_field.value

        return {
            'name': name,
            'id': measurement.id,
            'image': "plots/plot-%d.png" % measurement.id
        }

    objects = list(map(map_measurement, SpectrumMeasurement.objects.all()))
    return render(request, 'spectra/spectrum_list.html', {'objects': objects})


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
