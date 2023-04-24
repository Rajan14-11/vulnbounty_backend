from django.contrib import admin
from .models import company,companyProgram,in_scope,out_scope,rewards,submission,company_wallet_history
# Register your models here.
admin.site.register(company)
admin.site.register(companyProgram)
admin.site.register(in_scope)
admin.site.register(out_scope)
admin.site.register(rewards)
admin.site.register(submission)
admin.site.register(company_wallet_history)