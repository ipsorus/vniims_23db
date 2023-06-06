from django.contrib.auth.models import AbstractUser
from django.db import models

from django.urls import reverse


class CustomUser(AbstractUser):
    patronymic = models.CharField(max_length=64, blank=True, db_index=True, verbose_name="Отчество")
    organization = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="Организация")
    position = models.CharField(max_length=128, verbose_name="Должность")
    work_experience = models.CharField(max_length=64, blank=True, verbose_name="Опыт работы")

    def get_absolute_url(self):
        return reverse('user-profile', kwargs={'username': self.username})

    def get_update_url(self):
        return reverse('update_profile', kwargs={'username': self.username})

    def get_delete_url(self):
        return reverse('post_delete_url', kwargs={'username': self.username})

    def __str__(self):
        return self.username


class Post(models.Model):
    title = models.CharField(max_length=150, db_index=True, verbose_name="Заголовок статьи")
    body = models.TextField(blank=True, db_index=True, verbose_name="Текст статьи")
    date_pub = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField('Tag', blank=True, related_name='posts', verbose_name="Тэги")

    def get_absolute_url(self):
        return reverse('post_detail_url', kwargs={'id': self.id})

    def get_update_url(self):
        return reverse('post_update_url', kwargs={'id': self.id})

    def get_delete_url(self):
        return reverse('post_delete_url', kwargs={'id': self.id})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_pub']

    def __str__(self):
        return f'{self.title}'


class Support(models.Model):
    title = models.CharField(max_length=150, db_index=True, verbose_name="Заголовок уведомления")
    body = models.TextField(blank=True, db_index=True, verbose_name="Текст уведомления")
    date_pub = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse('support_post_detail_url', kwargs={'id': self.id})

    def get_update_url(self):
        return reverse('support_post_update_url', kwargs={'id': self.id})

    def get_delete_url(self):
        return reverse('support_post_delete_url', kwargs={'id': self.id})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-date_pub']

    def __str__(self):
        return f'{self.title}'


class Tag(models.Model):
    title = models.CharField(max_length=150, db_index=True, verbose_name="Заголовок тега")

    def __str__(self):
        return f'{self.title}'

    def get_absolute_url(self):
        return reverse('tag_detail_url', kwargs={'id': self.id})

    def get_update_url(self):
        return reverse('tag_update_url', kwargs={'id': self.id})

    def get_delete_url(self):
        return reverse('tag_delete_url', kwargs={'id': self.id})


class Spectrum(models.Model):
    name = models.CharField(max_length=50, default="", verbose_name="Название масс-спектра")
    author = models.ForeignKey(CustomUser, default=1, on_delete=models.PROTECT, related_name="author", verbose_name="Автор")
    spectrum_json = models.JSONField(db_index=True, default=dict, verbose_name="Спектр JSON")
    spectrum = models.TextField(db_index=True, verbose_name="Спектр")
    date_updated = models.DateTimeField(blank=True, null=True, verbose_name="Дата обновления")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    date_curated = models.DateTimeField(blank=True, null=True, verbose_name="Дата последней проверки")
    date_prepare = models.DateField(blank=True, null=True, verbose_name="Дата исследования")
    draft = models.BooleanField(default=True, verbose_name="Черновик")
    reject_reason = models.CharField(max_length=255, blank=True, verbose_name="Причина отклонения записи")
    library = models.ManyToManyField('Library', blank=True, db_index=True, related_name='spectrums', verbose_name="Библиотека")
    tags = models.ManyToManyField('SpectrumTag', blank=True, related_name='spectrums', verbose_name="Теги")
    field = models.CharField(max_length=255, blank=True, db_index=True, verbose_name="any_field")
    reg_num = models.CharField(max_length=64, blank=True, db_index=True, verbose_name="Регистрационный номер")
    is_etalon = models.BooleanField(default=False, verbose_name="Аттестованный масс-спектр")
    metaDataMap = models.JSONField(db_index=True, default=dict, verbose_name="Метаданные")
    formula = models.CharField(max_length=64, db_index=True, verbose_name="Формула")
    cas = models.CharField(max_length=64, db_index=True, verbose_name="CAS номер")

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return f'Масс-спектр "{self.name}"'

    def get_absolute_url(self):
        return reverse('spectrum_detail_url', kwargs={'id': self.id})

    def get_update_url(self):
        return reverse('spectrum_update_url', kwargs={'id': self.id})

    def get_delete_url(self):
        return reverse('spectrum_delete_url', kwargs={'id': self.id})


class SpectrumMeasurement(models.Model):
    spectrum = models.ForeignKey('Spectrum', on_delete=models.CASCADE)
    source = models.IntegerField(blank=True, null=True, verbose_name="Источник")
    level = models.IntegerField(blank=True, null=True, verbose_name="Уровень")
    ionization = models.IntegerField(blank=True, null=True, verbose_name="Ионизация")
    polarity = models.IntegerField(blank=True, null=True, verbose_name="Полярность")


class Metadata(models.Model):
    spectrum = models.ForeignKey('Spectrum', on_delete=models.CASCADE, related_name="metaData")
    url = models.CharField(max_length=255, blank=True, null=True, verbose_name="url")
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="name")
    value = models.CharField(max_length=255, blank=True, null=True, verbose_name="value")
    # hidden = models.BooleanField(default=False, verbose_name="hidden")
    # category = models.CharField(max_length=64, blank=True, null=True, verbose_name="category")
    # computed = models.BooleanField(default=False, verbose_name="computed")

    def __str__(self):
        return f'{self.name}: {self.value}'


class SpectrumTag(models.Model):
    title = models.CharField(max_length=64, db_index=True, verbose_name="Тег")


class Library(models.Model):
    title = models.CharField(max_length=64, db_index=True, verbose_name="Библиотека")
    description = models.CharField(max_length=255, blank=True, null=True, db_index=True, verbose_name="Описание библиотеки")
    link = models.CharField(max_length=64, blank=True, null=True, db_index=True, verbose_name="Ссылка")
