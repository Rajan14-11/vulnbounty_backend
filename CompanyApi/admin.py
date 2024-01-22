from django.contrib import admin
from .models import company,companyProgram,submission,company_wallet_history,Transaction
# Register your models here.
admin.site.register(company)
admin.site.register(companyProgram)
admin.site.register(submission)
admin.site.register(company_wallet_history)

admin.site.register(Transaction)
