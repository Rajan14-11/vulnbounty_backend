from django.contrib.auth import decorators
from django.http import HttpResponse
from django.shortcuts import redirect
from.models import company
from django.contrib import messages as message
from rest_framework.response import Response
#unauthenicated user

def unauthenticated_user(views_func):
    def wrapper_fun(request, *args,**kwargs):
        if request.session.modified ==True:
            return redirect('company_dashboard')
        return views_func(request,*args,**kwargs)
    return wrapper_fun

# allowed user
def allowed_users():
    def decorator(view_func):
        def wrapper_func(request, *args,**kwargs):
            if request.user.id:
                if company.objects.filter(company_user=request.user.id,email_status=True).exists():
                  return view_func(request, *args,**kwargs)
                else:
                    if not company.objects.filter(company_user=request.user.id).exists():
                        return Response({"message":"you are not authorized","status":"unauthorized"})
                    elif  not company.objects.filter(company_user=request.user.id,email_status=True).exists():
                        return Response({"message":"email is not verified","status":"unauthorized"})
            else:
                return Response({"message":"unauthorized","status":"unauthorized"})
            return Response({"message":"unauthorized","status":"unauthorized"})
        return wrapper_func
    return decorator

