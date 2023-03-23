FROM python:3.10.4-alpine3.15

COPY requirements.txt /temp/requirements.txt
COPY mass_spec_app /mass_spec_app
WORKDIR /mass_spec_app
EXPOSE 8000

RUN apk add postgresql-client build-base postgresql-dev

RUN pip install --upgrade pip && pip install -r /temp/requirements.txt

RUN adduser --disabled-password mass_spec_app-user

USER mass_spec_app-user
