from django.contrib import admin
from .models import professional,professional_information,professional_wallet,professional_favourite_program,professional_test
# Register your models here.
admin.site.register(professional)
admin.site.register(professional_information)
admin.site.register(professional_wallet)
admin.site.register(professional_favourite_program)
admin.site.register(professional_test)