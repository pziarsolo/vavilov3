from django.contrib import admin
from .models import ObservationDataType


@admin.register(ObservationDataType)
class ObservationDataTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
