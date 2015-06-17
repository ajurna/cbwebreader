from django.contrib import admin
from comic.models import Setting

# Register your models here.
@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')

