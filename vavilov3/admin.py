from django.contrib import admin
from .models import ScaleDataType


@admin.register(ScaleDataType)
class ScaleDataTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
