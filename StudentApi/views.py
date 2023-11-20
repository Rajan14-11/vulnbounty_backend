

# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from StudentApi.models import *
# from SubmissionApi.models import *
# from ProgramsApi.models import *
from CompanyApi.models import *
from datetime import date
from django.db.models import Sum
from StudentApi.serializers import *
# from ProgramsApi.serializers import *
# from SubmissionApi.serializers import *
from CompanyApi.serializers import *


# from SubmissionApi.forms import *
# from ChatApi.models import *
# from ChatApi.serializers import *
import stripe
from django.contrib import messages as message
# from ExtendUserApi.models import ExtendUser,ValidateNumber
from django.contrib.auth import authenticate, login, logout
import uuid
import os
from django.core.files.base import ContentFile
# from CompanyApi.forms import *
from django.contrib import messages as message
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from django.contrib.auth.hashers import make_password
import re
from django.db.models import Q
from twilio.rest import Client
from django.core.files.base import ContentFile
import base64
import secrets
from StudentApi.helpers import send_email_verification_mail, send_optional_email_verification_mail
from MainApi.helpers import error_handle

import uuid
from .serializers import *

# from ProfessionalApi.forms import *
# from ExtendUserApi.serializers import *

from CompanyApi.models import *
from CompanyApi.serializers import CompanyProgramSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .renderers import UserRender
from rest_framework.permissions import IsAuthenticated
# Create your views here.
 # --------------------- DASHBOARD ------------------------------


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class StudentRegisterAPIView(APIView):
    renderer_classes = [UserRender]

    def post(self, request, format=None):
        serializer = StudentRegisterSdrializer(data=request.data)
        if serializer.is_valid():
            email_token = str(uuid.uuid4())
            user = serializer.save()
            student_obj = Student.objects.create(
                student_user=user, email_verification_token=email_token, terms_and_policy=True)
            token = get_tokens_for_user(user)
            if student_obj:
                student_wallet.objects.create(student=student_obj)
                send_email_verification_mail(request, user.email, email_token)
                message = 'Account created Successfully ! verify your email'
            else:
                message = 'Account not created retry again'
            return Response({"token": token, "message": message})

        else:
            message = error_handle(serializer.errors)
            print("message",message)


            return Response(message)


class StudentDashboardAPIView(APIView):
        renderer_classes=[UserRender]
        permission_classes=[IsAuthenticated]
        def get(self,request):
            try:
                submission_today=submission.objects.filter(user=request.user.id,created_at__date=date.today()).count()
                submission_this_month=submission.objects.filter(user=request.user.id,created_at__month=date.today().month).count()
                leaderboard= Student.objects.filter(reward__gte=1).order_by('-reward')[:5]
                program=companyProgram.objects.filter(created_at=date.today())[:5]
                payment_today = payments.objects.filter(transfer_to=request.user.id,created_at__date=date.today()).aggregate(Sum('amount'))
                payment_this_month=payments.objects.filter(transfer_to =request.user.id,created_at__month=date.today().month).aggregate(Sum('amount'))

                response={
                    "message":'success',
                    "data":{'user':request.user.username,
                "submission_today":submission_today,
                "submission_this_month":submission_this_month,
                "top_hunter":StudentDashbordserializer(leaderboard,many=True).data,
                "program":CompanyProgramSerializer(program,many=True).data,
                "payment_today":payment_today,
                "payment_this_month":payment_this_month
                }}
            except Exception as e:
                print(e)
                response={
                    "message":"Failed",
                    "data":None
                }
            return Response(response)

class StudentPrgramAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
            # professional_obj=Student.objects.get(student_user=request.user)
            # professional_information_obj=student_information.objects.get(student=professional_obj.id)
            # region=professional_information_obj.country_names
            data=companyProgram.objects.all().filter((Q(region ='all') )) # & ~Q(visibility='P')
            # data=companyProgram.objects.all().filter((Q(region ='all') | Q(region = region) )) # & ~Q(visibility='P')
            # invited_program=private_invitation.objects.filter(hunter=professional_obj.id)
            response={
                "message":"success",
                "data":{
                    "programs":CompanyProgramSerializer(data,many=True).data
                }
            }
            return Response(response)


class StudentProgramDetailsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        # if submission.objects.filter(program=id,user=request.user.id).exists():
        try:
            data=companyProgram.objects.get(id=pk)
            message="Success"
            serializer=CompanyProgramSerializer(data).data
        except:
            serializer=None
            message="Failed"
        response={
            "message":message,
            "data":{
                "program_obj":serializer
            }
        }
        return Response(response)


class StudentSubmissionAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        all_submission=submission.objects.filter(user=request.user.id)
        response={
            "message":"success",
            "data":{
                "all_submission":CompanySubmissionSerializer(all_submission,many=True).data,
            }
        }

        return Response(response)
    def post(self,request):
        serializer=StudentprogramSubmissionSerializer(data=request.data)
        if  serializer.is_valid():
            program_obj=companyProgram.objects.get(id=serializer.data['program_id'])
            if submission.objects.filter(program=program_obj,user=request.user).exists():
                return Response({"message":"already done"})
            else:
                user = submission.objects.create(
                title=serializer.data['title'],
                report=serializer.data['report'],
                program=program_obj,
                user=request.user)
                message="success"
        else:
            message=error_handle(serializer.errors)
            print("message",message)
            return Response(message)


class StudentSubmissionDetailsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            data=submission.objects.get(program=pk,user=request.user.id)
            response={
            "message":"Success",
            "data":{
                "submission_details_obj":CompanySubmissionSerializer(data).data
            }
            }
        except:
            response={
            "message":"Failed",
            "data":None
        }
        return Response(response)
class StudentLearderAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            data = Student.objects.filter(reward__gte=1).order_by('-reward')
            serialzer=StudentDashbordserializer(data,many=True).data
            message="Success"
        except :
            serialzer=None
            message="Failed"

        response={
            "message":message,
            "data":{
                "student_obj":serialzer
            }
        }

        return Response(response)


class StudentLeaderDetailsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            data=Student.objects.get(id=pk)
            serialzer=StudentDashbordserializer(data).data
            message="Success"
        except :
            serialzer=None
            message="Failed"
        response={
            "message":message,
            "data":{
                "student_obj":serialzer
            }
        }
        return Response(response)

class StudentSettingsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            program_count=submission.objects.filter(program__company=request.user.id).count()
            profesional_obj=Student.objects.get(student_user=request.user.id)
            total_payment=payments.objects.filter(transfer_from = profesional_obj.id).aggregate(Sum('amount'))
            professional_login_details_obj=student_login_details.objects.get(student=profesional_obj)
            try:
                ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)

            except:
                ExtendUser.objects.create(user=request.user)
                ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)

            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)
                if ValidateNumber_obj.status == True:
                    ValidateNumber_status="True"
                else:
                    ValidateNumber_status="False"
            except:
                ValidateNumber_obj=None
                ValidateNumber_status="False"

            response={
                "message":"success",
                "data":{
                "details":StudentSettingsSerializer( profesional_obj).data,
                "program_count":program_count,
                "total_payment":total_payment,
                "login_details":StudentLoginDetailsSerializer(professional_login_details_obj).data,
                "ExtendUser":StudentExtendedUserSerializer(ExtendUser_obj).data,
                "ValidateNumber":ValidateNumber_obj,}


                }
        except Exception as e:
            response={
                "message":"failed",
                "data":None
            }
            print(e)
        return Response(response)


class StudentSettingNameDescriptionAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=StudentChangeNameSerialzer(data=request.data)
        if serializer.is_valid():
            try:
                first_name=request.data['first_name']
                last_name=request.data['last_name']
                profile_description=request.data['description']
                if not first_name.isalpha() or not last_name.isalpha():
                    message="first name or last name is invalid , only alphabet"
                    return Response({"message":message})
                User.objects.filter(id=request.user.id).update(first_name=first_name,last_name=last_name)
                Student.objects.filter(student_user = request.user).update(profile_description=profile_description)
                message='Successfully updated !'
            except Exception as e:
                message="Failed"
                print(e)
        else:
            message=error_handle(serializer.errors)
            print("message",message)


            return Response(message)

        response={
            "message":message
        }
        return Response(response)


class StudentSettingsUploadPictureAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        data = Student.objects.get( student_user=request.user.id)
        serializer =StudentUpdateimageSerializer(data ,data=request.data,partial=True)
        if serializer.is_valid(raise_exception=True):
            if data.profile_picture == 'Null':
                serializer.save()
                message="Successfully updated !"
            else:
                file_exists=os.path.exists(data.profile_picture.path)
                if file_exists == True:
                    os.remove(data.profile_picture.path)
                serializer.save()
            message="Successfully updated !"
            return Response({"message":message})
        else:
            return Response({"message":"Failed"})


class StudentSettingsUserEmailAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=StudentChangeUserNameSerializer(data=request.data)
        message=[]
        if serializer.is_valid():
            try:
                regex  = "^([a-z]+('[a-z])?[0-9a-z]*)$"
                print("reached_up")
                username = request.data['username']
                email = request.data['email']
                password = request.data['password']
                if not username or not email or not password:
                    message="Fields should not be empty"
                else:
                    if not re.search(regex, username):
                        message="Allowed are alphabet,number and apostrophe"
                    else:
                        pass

                user = authenticate(
                    request, username=request.user.username, password=password)
                if user is not None:
                    if request.user.username != username:

                        if User.objects.filter(username=username).exists():
                            message='Username already taken'

                        else:
                            User.objects.filter(id=user.id).update(username=username)
                            message=' Username successfully updated !'
                    if user.email != email:

                        if User.objects.filter(email=email).exists() or ExtendUser.objects.filter(optional_email=email).exists():
                            print("reached in email2")
                            message='Email already taken'
                        else:
                            token = str(uuid.uuid4())

                            try:
                                ExtendUser_obj= ExtendUser.objects.get(user=user.id)
                                if user.email != email!=ExtendUser_obj.optional_email:
                                    print("update")
                                    ExtendUser.objects.filter(user=request.user.id).update(optional_email=email,optional_email_token =token,optional_email_status=False)
                                    send_optional_email_verification_mail(email,token)
                                    message='Email successfully updated, Now Verify the email'

                                else:
                                    message='You already added this Email'

                            except:
                                print("create")
                                ExtendUser.objects.create(user=user,optional_email=email,optional_email_token=token)
                                send_email_verification_mail(request,email,token)
                                message='Email successfully Added, Now Verify the email'


                else:
                    message='Password doesnot match'

            except Exception as e:
                message="failed"
                print(e)
            response={
                "message":message,
                "data":None
            }

        else:
            message=error_handle(serializer.errors)
            print("message",message)
            return Response(message)

        return Response(response)


class StudentSettingsUpdatePasswordAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=StudentUpdatePasswordSerializer(data=request.data)
        if serializer.is_valid():
            password_1=request.data['password1']
            password_2=request.data['password2']
            password_3=request.data['password3']
            if not password_1 or not password_2 or not password_3:
                message="Fields should not be empty"
            user_obj = authenticate(request, username=request.user.username, password=password_1)
            if user_obj is not None:
                if not password_2 and not password_3:
                    message="New password confirm password should not be empty and length more than 9"
                if password_2==password_3:
                    print("reached")
                    password=make_password(password_2)
                    User.objects.filter(id=request.user.id).update(password=password)
                    user_obj =authenticate(username=request.user.username, password=password)
                    login(request,user_obj)
                    message="New password updated successfully"
                else:
                    message="New password and confirm password not match"
            else:
                message="Old password not match"

            print('if')
        else:
            message=error_handle(serializer.errors)
            print("message",message)
            return Response(message)
        response={
            "data":None,
            "message":message
        }
        return Response(response)

class StudentSettingsSkillsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        try:
            profe_user=Student.objects.get(student_user=request.user.id)
            professional_obj=skills.objects.filter(user=profe_user.id)
            response={
                "message":"Success",
                "data":{
                    "skills":StudentSkillsSerializer(professional_obj,many=True).data
                }
            }
        except Exception as e:
            response={
                "message":"Failed",
                "data":None
            }
            print(e)
        return Response(response)
    def post(self,request,format=None):
        serializer=StudentSkillsAddSerializer(data=request.data)
        if serializer.is_valid():
            print("reached")
            profe_user=Student.objects.get(student_user=request.user.id)
            skill=request.data['skill']
            sample_skills = ["A# .NET","A# (Axiom)","A-0 System","A+","A++","ABAP","ABC","ABC ALGOL","ABLE","ABSET","ABSYS","ACC","Accent","Ace DASL","ACL2","ACT-III","Action!","ActionScript","Ada","Adenine","Agda","Agilent VEE","Agora","AIMMS","Alef","ALF","ALGOL 58","ALGOL 60","ALGOL 68","ALGOL W","Alice","Alma-0","AmbientTalk","Amiga E","AMOS","AMPL","APL","App Inventor for Android's visual block language","AppleScript","Arc","ARexx","Argus","AspectJ","Assembly language","ATS","Ateji PX","AutoHotkey","Autocoder","AutoIt","AutoLISP / Visual LISP","Averest","AWK","Axum","B","Babbage","Bash","BASIC","bc","BCPL","BeanShell","Batch (Windows/Dos)","Bertrand","BETA","Bigwig","Bistro","BitC","BLISS","Blue","Bon","Boo","Boomerang","Bourne shell","bash","ksh","BREW","BPEL","C","C--","C++","C#","C/AL","Caché ObjectScript","C Shell","Caml","Candle","Cayenne","CDuce","Cecil","Cel","Cesil","Ceylon","CFEngine","CFML","Cg","Ch","Chapel","CHAIN","Charity","Charm","Chef","CHILL","CHIP-8","chomski","ChucK","CICS","Cilk","CL","Claire","Clarion","Clean","Clipper","CLIST","Clojure","CLU","CMS-2","COBOL","Cobra","CODE","CoffeeScript","Cola","ColdC","ColdFusion","COMAL","Combined Programming Language","COMIT","Common Intermediate Language","Common Lisp","COMPASS","Component Pascal","Constraint Handling Rules","Converge","Cool","Coq","Coral 66","Corn","CorVision","COWSEL","CPL","csh","CSP","Csound","CUDA","Curl","Curry","Cyclone","Cython","D","DASL","DASL","Dart","DataFlex","Datalog","DATATRIEVE","dBase","dc","DCL","Deesel","Delphi","DinkC","DIBOL","Dog","Draco","DRAKON","Dylan","DYNAMO","E","E#","Ease","Easy PL/I","Easy Programming Language","EASYTRIEVE PLUS","ECMAScript","Edinburgh IMP","EGL","Eiffel","ELAN","Elixir","Elm","Emacs Lisp","Emerald","Epigram","EPL","Erlang","es","Escapade","Escher","ESPOL","Esterel","Etoys","Euclid","Euler","Euphoria","EusLisp Robot Programming Language","CMS EXEC","EXEC 2","Executable UML","F","F#","Factor","Falcon","Fancy","Fantom","FAUST","Felix","Ferite","FFP","Fjölnir","FL","Flavors","Flex","FLOW-MATIC","FOCAL","FOCUS","FOIL","FORMAC","@Formula","Forth","Fortran","Fortress","FoxBase","FoxPro","FP","FPr","Franz Lisp","Frege","F-Script","FSProg","G","Google Apps Script","Game Maker Language","GameMonkey Script","GAMS","GAP","G-code","Genie","GDL","Gibiane","GJ","GEORGE","GLSL","GNU E","GM","Go","Go!","GOAL","Gödel","Godiva","GOM (Good Old Mad)","Goo","Gosu","GOTRAN","GPSS","GraphTalk","GRASS","Groovy","Hack (programming language)","HAL/S","Hamilton C shell","Harbour","Hartmann pipelines","Haskell","Haxe","High Level Assembly","HLSL","Hop","Hope","Hugo","Hume","HyperTalk","IBM Basic assembly language","IBM HAScript","IBM Informix-4GL","IBM RPG","ICI","Icon","Id","IDL","Idris","IMP","Inform","Io","Ioke","IPL","IPTSCRAE","ISLISP","ISPF","ISWIM","J","J#","J++","JADE","Jako","JAL","Janus","JASS","Java","JavaScript","JCL","JEAN","Join Java","JOSS","Joule","JOVIAL","Joy","JScript","JScript .NET","JavaFX Script","Julia","Jython","K","Kaleidoscope","Karel","Karel++","KEE","Kixtart","KIF","Kojo","Kotlin","KRC","KRL","KUKA","KRYPTON","ksh","L","L# .NET","LabVIEW","Ladder","Lagoona","LANSA","Lasso","LaTeX","Lava","LC-3","Leda","Legoscript","LIL","LilyPond","Limbo","Limnor","LINC","Lingo","Linoleum","LIS","LISA","Lisaac","Lisp","Lite-C","Lithe","Little b","Logo","Logtalk","LPC","LSE","LSL","LiveCode","LiveScript","Lua","Lucid","Lustre","LYaPAS","Lynx","M2001","M4","Machine code","MAD","MAD/I","Magik","Magma","make","Maple","MAPPER","MARK-IV","Mary","MASM Microsoft Assembly x86","Mathematica","MATLAB","Maxima","Macsyma","Max","MaxScript","Maya (MEL)","MDL","Mercury","Mesa","Metacard","Metafont","MetaL","Microcode","MicroScript","MIIS","MillScript","MIMIC","Mirah","Miranda","MIVA Script","ML","Moby","Model 204","Modelica","Modula","Modula-2","Modula-3","Mohol","MOO","Mortran","Mouse","MPD","CIL","MSL","MUMPS","NASM","NATURAL","Napier88","Neko","Nemerle","nesC","NESL","Net.Data","NetLogo","NetRexx","NewLISP","NEWP","Newspeak","NewtonScript","NGL","Nial","Nice","Nickle","Nim","NPL","Not eXactly C","Not Quite C","NSIS","Nu","NWScript","NXT-G","o:XML","Oak","Oberon","Obix","OBJ2","Object Lisp","ObjectLOGO","Object REXX","Object Pascal","Objective-C","Objective-J","Obliq","Obol","OCaml","occam","occam-π","Octave","OmniMark","Onyx","Opa","Opal","OpenCL","OpenEdge ABL","OPL","OPS5","OptimJ","Orc","ORCA/Modula-2","Oriel","Orwell","Oxygene","Oz","P#","ParaSail (programming language)","PARI/GP","Pascal","Pawn","PCASTL","PCF","PEARL","PeopleCode","Perl","PDL","PHP","Phrogram","Pico","Picolisp","Pict","Pike","PIKT","PILOT","Pipelines","Pizza","PL-11","PL/0","PL/B","PL/C","PL/I","PL/M","PL/P","PL/SQL","PL360","PLANC","Plankalkül","Planner","PLEX","PLEXIL","Plus","POP-11","PostScript","PortablE","Powerhouse","PowerBuilder","PowerShell","PPL","Processing","Processing.js","Prograph","PROIV","Prolog","PROMAL","Promela","PROSE modeling language","PROTEL","ProvideX","Pro*C","Pure","Python","Q (equational programming language)","Q (programming language from Kx Systems)","Qalb","QtScript","QuakeC","QPL","R","R++","Racket","RAPID","Rapira","Ratfiv","Ratfor","rc","REBOL","Red","Redcode","REFAL","Reia","Revolution","rex","REXX","Rlab","RobotC","ROOP","RPG","RPL","RSL","RTL/2","Ruby","RuneScript","Rust","S","S2","S3","S-Lang","S-PLUS","SA-C","SabreTalk","SAIL","SALSA","SAM76","SAS","SASL","Sather","Sawzall","SBL","Scala","Scheme","Scilab","Scratch","Script.NET","Sed","Seed7","Self","SenseTalk","SequenceL","SETL","Shift Script","SIMPOL","SIGNAL","SiMPLE","SIMSCRIPT","Simula","Simulink","SISAL","SLIP","SMALL","Smalltalk","Small Basic","SML","Snap!","SNOBOL","SPITBOL","Snowball","SOL","Span","SPARK","Speedcode","SPIN","SP/k","SPS","Squeak","Squirrel","SR","S/SL","Stackless Python","Starlogo","Strand","Stata","Stateflow","Subtext","SuperCollider","SuperTalk","Swift (Apple programming language)","Swift (parallel scripting language)","SYMPL","SyncCharts","SystemVerilog","T","TACL","TACPOL","TADS","TAL","Tcl","Tea","TECO","TELCOMP","TeX","TEX","TIE","Timber","TMG","Tom","TOM","Topspeed","TPU","Trac","TTM","T-SQL","TTCN","Turing","TUTOR","TXL","TypeScript","Turbo C++","Ubercode","UCSD Pascal","Umple","Unicon","Uniface","UNITY","Unix shell","UnrealScript","Vala","VBA","VBScript","Verilog","VHDL","Visual Basic","Visual Basic .NET","Visual DataFlex","Visual DialogScript","Visual Fortran","Visual FoxPro","Visual J++","Visual J#","Visual Objects","Visual Prolog","VSXu","Vvvv","WATFIV, WATFOR","WebDNA","WebQL","Windows PowerShell","Winbatch","Wolfram","Wyvern","X++","X#","X10","XBL","XC","XMOS architecture","xHarbour","XL","Xojo","XOTcl","XPL","XPL0","XQuery","XSB","XSLT","XPath","Xtend","Yorick","YQL","Z notation","Zeno","ZOPL","ZPL"]

            if not skill:
                message="Skill is empty"
                return Response({"message":message})
            if skill not in sample_skills:
                message="Select Skill from given"
                return Response({"message":message})
            if skills.objects.filter(user=profe_user.id,skill=skill).exists():
                message="Skill is already there"
                return Response({"message":message})
            else:
                skills.objects.create(user=profe_user,skill=skill)
                message="Skill added successfully"
                return Response({"message":message})
        else:
            message=error_handle(serializer.errors)
            print("message",message)
            return Response(message)


class StudentFavouriteListAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            student_data=Student.objects.get(student_user=request.user.id)
            student_favourite_program_data=student_favourite_program.objects.filter(student=student_data.id)
            serializer=StudentFavouriteProgramSerializer(student_favourite_program_data,many=True).data

            message="Success"
        except:
            message="Failed"
            serializer=None


        response={
            "message":message,
            "data":serializer
        }
        return Response(response)
# --------------------- PROGRAM --------------------------------


# --------------------- SUBMISSION -----------------------------

class  SubmissionView(APIView):
    def get(self,request,format=None):
        user=User.objects.get(id=2)
        all_submission=submission.objects.filter(user=user)
        serializers=submissionSerializer(all_submission,many=True)
        data=serializers.data
        pending_submission=submission.objects.filter(user=user,status="pending")
        serializers=submissionSerializer(pending_submission,many=True)
        data1=serializers.data
        rejected_submission=submission.objects.filter(user=user,status="rejected")
        serializers=submissionSerializer(rejected_submission,many=True)
        data2=serializers.data
        accepted_submission=submission.objects.filter(user=user,status="accepted")
        serializers=submissionSerializer(accepted_submission,many=True)
        data3=serializers.data
        completed_submission = submission.objects.filter(user=user,status="completed")
        serializers=submissionSerializer(completed_submission,many=True)
        data4=serializers.data
        response={
            "all_submission":data,
            "pending_submission":data1,
            "accepted_submission":data2,
            "rejected_submission":data3,
            'completed_submission':data4
            }
        return Response(response)

class  Student_submission_details_view(APIView):
    def get(self,request,format=None):
        user=User.objects.get(id=2)
        program_id=programs.objects.get(id=1)
        data=submission.objects.get(program=program_id,user=user)
        serializers=submissionSerializer(data)
        response=serializers.data
        return Response(response)

class Submit_program_view(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        submit_program=programs.objects.get(id=1)
        serializers=programsSerializer(submit_program)
        serializers_data=serializers.data
        if serializers.is_valid():
            serializers.save()
        else:
            message=error_handle(serializers.errors)
            print("message",message)
            return Response(message)
        return Response({"message":"progem submitted successfully !"})


class Chat_view(APIView):
    def post(self,request,format=None):
        user=submission.objects.get(id=1)
        if request.method=='POST' and 'chat_send' in request.POST:
            text=request.POST.get('text')

            sender_id=request.user.id
            data=submission.objects.get(id=user)
            serializers=submissionSerializer(data)
            response=serializers.data
            receiver_id=data.program.company.id
            message=messages.objects.create(submission_id=user,sender_id=sender_id,receiver_id=receiver_id,text=text)
            serializers=messagesSerializer(message)
            msg=serializers.data
            response_data={
                'response':response,
                'msg':msg
            }
            return Response(response_data)
        data=messages.objects.filter(submission_id=user).order_by('created_at')
        serializers=messagesSerializer(data,many=True)
        data1=serializers.data
        receiver_data=submission.objects.get(id=user)
        serializers=submissionSerializer(receiver_data)
        data2=serializers.data
        context={
            "data":response,
            "submission_id":data1,
            "receiver_data":data2
        }
        return Response(context)

# stripe.api_key=settings.STRIPE_SECRET_KEY
class Payment_view(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        if request.method=="POST" and 'student_withdraw' in request.POST:
            print("reached")
            host = request.get_host()
            student_data=Student.objects.get(student_user=user)
            serializers=StudentSerializer(student_data)
            stud_data=serializers.data
            stud_id=student_data.id
            student_wallet_data=student_wallet.objects.get(student=stud_id)
            serializers=student_walletSerializer(student_wallet_data)
            stud_wallet_data=serializers.data
            try:
                amount=int(request.POST.get('amount'))
            except:
                return Response({"message":"enter a valid amount"})
            if not (10 < amount <1000 ) :
                return Response({"message":"The amount should be in between 10 and 1000 "})
            if not student_wallet_data.amount >= amount:
                return Response({"message":"Don't have this much amount in your wallet"})

            checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data':{
                        'currency':'inr',
                        'unit_amount':amount*100,
                        'product_data':{
                            "name":"sarath"
                        }
                    },
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url="http://{}/student/payment_success/{}".format(host,amount),
            cancel_url="http://"+host+'/student/payment_cancel',
            )

            # return redirect(checkout_session.url, code=303)
        student_data=Student.objects.get(student_user=user)
        serializers=StudentSerializer(student_data)
        data=serializers.data
        student_wallet_data=student_wallet.objects.get(student=stud_id)
        serializers=student_walletSerializer(student_wallet_data)
        data1=serializers.data
        transaction=payments.objects.filter(transfer_to=user)
        serializers=paymentsSerializer(transaction,many=True)
        transaction_data=serializers.data
        wallet_tranaction=student_wallet_history.objects.filter(student=stud_id)
        serializers=student_wallet_historySerializer(wallet_tranaction,many=True)
        wallet_tranaction_data=serializers.data

        print(wallet_tranaction)
        context={
            "student_wallet_data": data1,
            "transaction":transaction_data,
            "wallet_tranaction":wallet_tranaction_data
        }

        return Response(context)


class Payment_success_view(APIView):
    def get(self,request,amount):
        user=User.objects.get(id=2)
        student_obj=Student.objects.get(student_user=user)
        serializers=StudentSerializer(student_obj)
        student_obj_data=serializers.data
        print(student_obj.id)
        student_wallet_obj=student_wallet.objects.get(student=student_obj)
        serializers=student_walletSerializer(student_wallet_obj)
        student_wallet_obj_data=serializers.data
        total_amount=student_wallet_obj.amount - int(amount)
        wallet_history=student_wallet_history.objects.create(student=student_obj,amount=int(amount),description="withdraw from wallet",status='db')
        data={
            'student_obj_data':student_obj_data,
            'student_wallet_obj_data' :student_wallet_obj_data,
        }
        return Response(data)

# --------------------- LEADERBOARD ----------------------------

class Leader_board_view(APIView):
    def get(self,request,format=None):
        data = Student.objects.filter(reward__gte=1).order_by('-reward')
        serializers=StudentSerializer(data,many=True)
        serializers_data=serializers.data
        return Response(serializers_data)

class  Leaderboard_detail_view(APIView):
    def get(self,request,id):
        user=User.objects.get(id=2)
        data=Student.objects.get(id=id)
        serializers=StudentSerializer(data)
        response=serializers.data
        return Response(response)

# --------------------- PROFILE --------------------------------


    #
    #CHANGING FIRST_NAME AND LAST_NAME AND PROFILE DESCRIPTION
class Profile_setting(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        try:
            first_name=request.POST['first_name']
            last_name=request.POST['last_name']
            profile_description=request.POST.get('profile_description')
            user_obj=User.objects.filter(id=user)
            serializers=UserSerializer(user_obj,many=True)
            user_data=serializers.data
            stud=Student.objects.filter(student_user = request.user).update(profile_description=profile_description)
            serializers=StudentSerializer(stud,many=True)
            stud_data=serializers.data
            message.success(request,'Successfully updated !')
            form=Profile_Setting_Form()
            context={
                "user_data":user_data,
                "stud_data":stud_data,
            }
            return Response(context)
        except Exception as e:
            print(e)
        return Response({"meassge":"Successfully updated !"})


#CHANGINGING USERNAME AND EMAIL USING PASSWORD
class Update_Password(APIView):
    def post(self,request):
            try:
                regex = "^([a-z]+('[a-z])?[0-9a-z]*)$"
                print("reached_up")
                username = request.POST.get('username')
                email = request.POST.get('email')
                password = request.POST.get('password')
                # user_obj=User.objects.filter(id=request.user.id)
                if not username or not email or not password:
                    return Response({"meassge":"Fields should not empty"})
                else:
                    if not re.search(regex, username):
                        return Response({"meassge":"Allowed are alphabet,number and apostrophe"})
                user = authenticate(
                    request, username=request.user.username, password=password)
                if user is not None:
                    print("reached in user is not")
                    if request.user.username != username:
                        print("reached in user is not if")
                        username_query=User.objects.filter(username=username)
                        serializers=UserSerializer(username_query,many=True)
                        username_data=serializers.data
                        if username_data.exists():
                            print("filter")
                        else:
                            user_query=User.objects.filter(id=user) #.update(username=username)
                            serializers=UserSerializer(user_query,many=True)
                            user_query_data=serializers.data
                            message.success(request,'Username successfully updated !')
                    ExtendUser_obj=ExtendUser.objects.get(user=user)
                    serializers=ExtendUserSerializer(ExtendUser_obj)
                    ExtendUser_data=serializers.data
                    if ExtendUser_data.optional_email != email:
                        email= User.objects.filter(email=email)
                        serializers=UserSerializer(email,many=True)
                        email_data=serializers.data
                        Extendemail=ExtendUser.objects.filter(optional_email=email)
                        serializers=ExtendUserSerializer(Extendemail,many=True)
                        Extendemail_data=serializers.data
                        if email_data.exists() or Extendemail_data.exists():
                            print("reached in email2")
                        else:
                            token = str(uuid.uuid4())
                            print("reached in email3")
                            try:
                                ExtendUser_obj= ExtendUser.objects.get(user=user)
                                serializers=ExtendUserSerializer(ExtendUser_obj)
                                ExtendUser_obj_data=serializers.data
                                if email_data != email !=Extendemail_data: #.optional_email
                                    ExUser=ExtendUser.objects.filter(user=user) #.update(optional_email=email,optional_email_token =token,optional_email_status=False)
                                    serializers=ExtendUserSerializer(ExUser,many=True)
                                    ExUser_data=serializers.data
                                    message.success(request,'Email successfully updated !')
                                    send_email_verification_mail(email,token)
                                else:
                                    message.warning(request,'You already added this Email')
                            except Exception as e:
                                print(e)
                                ExUser_create=ExtendUser.objects.create(user=request.user,optional_email=email,optional_email_token=token)
                                serializers=ExtendUserSerializer(ExUser_create)
                                ExUser_create_data=serializers.data
                                send_email_verification_mail(email,token)
                                message.success(request,'Email successfully Added !')
                                pass

                else:
                    message.error(request,'Password doesnot match')
            except Exception as e:
                print(e)

            return Response({"meassage":"Updated Successfully"})


# ADDING SKILLS AND INTSEREST
class Add_Skills(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        skill=request.POST.get('skill')
        if not skill:
            return Response({"message":"skill is empty"})
        data = student_skills.objects.create(user=user,skill=skill)
        serializers=student_skillsSerializer(data)
        skill_response=serializers.data
        message.success(request,"Skill added successfully !")
        return Response(skill_response)

 # CHANGING IMAGES
class Update_img(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        data = Student.objects.get(student_user=user)
        serializers=StudentSerializer(data)
        data_profile=serializers.data
        try:
            profile_image=request.POST.get('profile_image')
            _format, _dataurl =profile_image.split(';base64,')
            _filename, _extension   = secrets.token_hex(20), _format.split('/')[-1]
            try:
                file = ContentFile( base64.b64decode(_dataurl), name=f"{_filename}.{_extension}")
                if data_profile.profile_picture == 'Null':
                    serializers.profile_picture=file
                    serializers.save()
                else:
                    file_exists=os.path.exists(data_profile.profile_picture.path)
                    if file_exists == True:
                        os.remove(data_profile.profile_picture.path)
                    data_profile.profile_picture=file
                    serializers.save()

                message.success(request,"Image successfully added")
                return Response({"message":"Image successfully added"})
            except:
                return Response({"message":"Image not added , please retry later"})
        except:
                print("Image is empty")
        data = Student.objects.get(student_user=user)
        serializers=StudentSerializer(data)
        data_response=serializers.data
        if data.profile_picture == 'Null':
            # form.save()
            # serializers.save()
            print("image is null")
        else:
            file_exists=os.path.exists(data.profile_picture.path)
            if file_exists == True:
                os.remove(data.profile_picture.path)

        return Response({"message":"Image successfully added"})



# ADDING AND  UPDATING  RESUME
class Update_resume(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        data = Student.objects.get(student_user=user)
        serializers=StudentSerializer(data)
        serializers_data=serializers.data
        form = resume_Form(request.POST, request.FILES, instance=data)
        print(data.resume.url)
        if not request.FILES:
            return Response({"message":"Field should not be empty"})
        if form.is_valid():
            data = Student.objects.get(student_user=user)
            if data.profile_picture == 'Null':
                data.save()
            else:
                file_exists=os.path.exists(data.profile_picture.path)
                if file_exists == True:
                    os.remove(data.profile_picture.path)
                serializers.save()
            return Response({"message":"Resume successfully updated !"})

        return Response(serializers_data)

# UPDATE THE PASSWORD USING OLD PASSWORD

class Update_Old_Password(APIView):
    def post(self,request):
        password_1=request.POST.get('password1')
        password_2=request.POST.get('password2')
        password_3=request.POST.get('password3')
        if not password_1 or not password_2 or not password_3:
            return Response({"message":"Field should not be empty"})
        user = authenticate(request, username=request.user.username, password=password_1)
        if user is not None:
            if password_2==password_3:
                password=make_password(password_2)
                userpw=User.objects.filter(id=user).update(password=password)
                user =authenticate(username=request.user.username, password=password)
                login(request, user)
                data={
                    "user password":userpw
                }
                return Response(data)
            else:
                print("New password and confirm password not match")
                return Response({"message":"New password and confirm password not match"})

        else:
            print("Old password not match")
            return Response({"message":"Old password not match"})


# Optional email verification

class Email_verification(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        ExtendUser_obj=ExtendUser.objects.get(user=user,id=1)
        serializers=ExtendUserSerializer(ExtendUser_obj)
        Extend_data=serializers.data
        token=request.POST.get('token')
        return Response(Extend_data)

    # phone number validation
class Phone_validation(APIView):
    def post(self,request):
        user=User.objects.get(id=2)
        print("reached1")
        country=request.POST.get('country')
        phone_number=request.POST.get('phone_number')
        code=request.POST.get('code')
        ExtendUser_obj=ExtendUser.objects.get(user=user,id=1)
        serializers=ExtendUserSerializer(ExtendUser_obj)
        data=serializers.data
        if code :
            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=user,id=1)
                serializers=ValidateNumberSerializer(ValidateNumber_obj)
                ValidateNumber_data=serializers.data
                if code == ValidateNumber_data.code:
                    ValidateNum=ValidateNumber.objects.filter(user=ExtendUser_obj.id) #.update(status=True)
                    serializers=ValidateNumberSerializer(ValidateNum,many=True)
                    ValidateNum_data=serializers.data
                    return Response(ValidateNum_data)
                else:
                    print("Security code doesnot match")
            except:
                pass

        else:
            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=user,id=1)
                serializers=ValidateNumberSerializer(ValidateNumber_obj)
                Valid_data=serializers.data
                return Response(Valid_data)

            except:
                ValidateNumber_obj=NULL
                number=f'{country}{phone_number}'
                account_sid =settings.TWILIO_ACCOUNT_SID
                auth_token = settings.TWILIO_AUTH_TOKEN
                client = Client(account_sid, auth_token)
                validation_code=9023456
                try:
                        message_obj = client.messages.create(
                                                body=f'Your Vulnbounty security code {validation_code}',
                                                from_='+13862303382',
                                                to=number
                                            )
                        ExtendUser_obj=ExtendUser.objects.get(user=user)
                        serializers=ExtendUserSerializer(ExtendUser_obj)
                        Extend_data=serializers.data
                        ValidateNumber.objects.create(user=Extend_data,message_id=message_obj.sid,phone_number=number,code=validation_code)
                        return Response(Extend_data)
                except:
                    print("Something went Wrong retry again")


            print("code is NOne")
        print(code)
        return Response({"message":"phone in validated"})


class Privacy_setting_view(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        data = Student.objects.get(student_user=user)
        serializers=StudentSerializer(data)
        response=serializers.data
        form = Profile_Setting_Form(instance=response)
        form = Profile_Setting_Form(request.POST, instance=data)
        if form.is_valid():
            serializers.save()
            return Response(response)


class Delete_skills_view(APIView):
    def get(self,request,id):
        user=User.objects.get(id=2)
        # skill_id=skills.objects.get(id=1)
        if student_skills.objects.filter(id=id).exists():
            print("id id exists")
            skill = student_skills.objects.get(id=id).delete() # skill_id
            print(id)
            return Response({"message":"deleted successfully"})
        else:
            print("in else condition")
            return Response({"message ": "skill not found "})

# --------------------- LOGOUT ---------------------------------

class Logout_view(APIView):
    def post(self,request):
        try:
            logout(request)
        except:
            pass
        return  Response({"message":"Logout successfully"})
# --------------------- INFORMATION ---------------------------

class Student_infromation_view(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        form= Information_From()
        student_obj=Student.objects.get(student_user=user.id)
        try:
            student_information_obj=student_information.objects.get(student=user)
            serializers=student_informationSerializer(student_information_obj)
            info_data=serializers.data
            status=True
        except:
            status=False
        if request.method == 'POST' and 'Add' in request.POST:
            print('reached')
            form= Information_From(request.POST)
            if form.is_valid():
                print("form valid")
                student_obj=Student.objects.get(student_user=user.id)
                form=form.save(commit=False)
                form.status=True
                form.student=student_obj
                serializers.save()
                return Response(info_data)

# --------------------- END ------------------------------------




# STUDENT SETTING START HERE


# ---------------------------PRIVACY SETTINGS ENDS HERE----------------------------
# ---------------------------LEADER BOARD START HERE ------------------------------

# ---------------------------LEADER BOARD START HERE ------------------------------

# --------------------------PROGRAMS DETAILS -------------------------------------


# ----------------------------------PROGRAM DETAILS END HERE----------------------

# ----------------------------- student_favourite_program_view ------------------------------

class Student_favourite_program_view(APIView):
    def get(self,request,id):
        user=User.objects.get(id=2)
        program_data=programs.objects.get(id=id)
        student_data=Student.objects.get(student_user=user.id)
        if student_favourite_programs.objects.filter(student=student_data,program_id=program_data).exists():
            student_favourite_programs.objects.filter(student=student_data).delete() #,program_id=program_data
            return Response({"message":"student favourite program deleted"})
        else:
            program_data=programs.objects.get(id=id)
            student_data=Student.objects.get(student_user=user.id)
            student_favourite_program_data=student_favourite_programs.objects.create(student=student_data,program_id=program_data)
            return Response({"message":"student favourite program  created "})



class Student_favourite_program_list_view(APIView):
    def get(self,request,format=None):
        user=User.objects.get(id=2)
        student_data=Student.objects.get(student_user=user.id)
        serializers=StudentSerializer(student_data)
        stud_data=serializers.data
        student_favourite_program_data=student_favourite_programs.objects.filter(student=user.id)
        serializers=student_favourite_programSerializer(student_favourite_program_data,many=True)
        data=serializers.data
        context={
            "student_favourite_program_data":data,

        }
        return Response(context)

