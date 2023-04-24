from rest_framework.views import APIView
from rest_framework.response import Response
from .models import *
from CompanyApi.models import companyProgram,submission
from django.db.models import Q
from CompanyApi.serializers import CompanyProgramSerializer,CompanySubmissionSerializer 
from django.contrib.auth.models import User
from .serializers import *
from django.contrib.auth import authenticate, login, logout
import re
import uuid
from MainApi.models import ExtendUser,ValidateNumber
from .helpers import send_email_verification_mail,send_optional_email_verification_mail
import base64, secrets
from django.core.files.base import ContentFile
import os
from twilio.rest import Client
from django.conf import settings
from datetime import date
import requests
import json
from CompanyApi.models import payments
from django.db.models import Sum
from .renderers import UserRender
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
# Create your views here.
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class ProfessionalRegisterAPIView(APIView):
     renderer_classes=[UserRender]
     def post(self,request,format=None):
        serializer=ProfessionalRegisterSdrializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email_token = str(uuid.uuid4())
            user=serializer.save()
            professional_obj = professional.objects.create(professional_user=user,email_verification_token=email_token,terms_and_policy=True)
            token=get_tokens_for_user(user)
            if professional_obj:
                professional_wallet.objects.create(professional=professional_obj)
                send_email_verification_mail(request,user.email,email_token )
                message='Account created Successfully ! verify your email'
            else:
                message='Account not created retry again'
            return Response({"token":token,"message":message})
            
        else:
            print("elsereached")
            return Response({"message":"Try again later"})  

class ProfessionalDashboardAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            submission_today=submission.objects.filter(user=request.user.id,created_at__date=date.today()).count()
            submission_this_month=submission.objects.filter(user=request.user.id,created_at__month=date.today().month).count()
            leaderboard= professional.objects.filter(reward__gte=1).order_by('-reward')[:5]
            program=companyProgram.objects.filter(created_at=date.today())[:5]
            payment_today = payments.objects.filter(transfer_to=request.user.id,created_at__date=date.today()).aggregate(Sum('amount'))
            payment_this_month=payments.objects.filter(transfer_to =request.user.id,created_at__month=date.today().month).aggregate(Sum('amount'))

            response={
                "message":'success',
                "data":{'user':request.user.username,
            "submission_today":submission_today,
            "submission_this_month":submission_this_month,
            "top_hunter":ProfessionalDashbordserializer(leaderboard,many=True).data,
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
class ProfessionalProgramAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
            professional_obj=professional.objects.get(professional_user=request.user)
            professional_information_obj=professional_information.objects.get(professional=professional_obj.id)
            region=professional_information_obj.country_names
            data=companyProgram.objects.all().filter((Q(region ='all') | Q(region = region) )) # & ~Q(visibility='P')
            # invited_program=private_invitation.objects.filter(hunter=professional_obj.id)
            response={
                "message":"success",
                "data":{
                    "programs":CompanyProgramSerializer(data,many=True).data
                }
            }
            return Response(response)


class ProfessionalProgramDetailsAPIView(APIView):
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
    
class ProfessionalSubmissionAPIView(APIView):
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
        serializer=ProfessionalprogramSubmissionSerializer(data=request.data)
        if  serializer.is_valid(raise_exception=True):
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
            message="failed"
       
        return Response({"message":message})

class ProfessionalSubmissionDetailsAPIView(APIView):
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

class ProfessionalLearderAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            data = professional.objects.filter(reward__gte=1).order_by('-reward')
            serialzer=ProfessionalDashbordserializer(data,many=True).data
            message="Success"
        except :
            serialzer=None
            message="Failed"
        
        response={
            "message":message,
            "data":{
                "professional_obj":serialzer
            }
        }

        return Response(response)

class ProfessionalLeaderDetailsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            data=professional.objects.get(id=pk)
            serialzer=ProfessionalDashbordserializer(data).data
            message="Success"
        except :
            serialzer=None
            message="Failed"
        response={
            "message":message,
            "data":{
                "professional_obj":serialzer
            }
        }
        return Response(response)


class ProfessionalSettingsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            program_count=submission.objects.filter(program__company=request.user.id).count()
            profesional_obj=professional.objects.get(professional_user=request.user.id)
            total_payment=payments.objects.filter(transfer_from = profesional_obj.id).aggregate(Sum('amount'))
            professional_login_details_obj=professional_login_details.objects.get(professional=profesional_obj)
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
                "details":ProfessionalSettingsSerializer( profesional_obj).data,
                "program_count":program_count,
                "total_payment":total_payment,
                "login_details":ProfessionalLoginDetailsSerializer(professional_login_details_obj).data,
                "ExtendUser":ProfessionalExtendedUserSerializer(ExtendUser_obj).data,
                "ValidateNumber":ValidateNumber_obj,}
            

                }
        except Exception as e:
            response={
                "message":"failed",
                "data":None
            }
            print(e)
        return Response(response)


class ProfessionalSettingsNameDescriptionAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=ProfessionalChangeNameSerialzer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                first_name=request.data['first_name']
                last_name=request.data['last_name']
                profile_description=request.data['description']
                if not first_name.isalpha() or not last_name.isalpha():
                    message="first name or last name is invalid , only alphabet"
                    return Response({"message":message})
                User.objects.filter(id=request.user.id).update(first_name=first_name,last_name=last_name)
                professional.objects.filter(professional_user = request.user).update(profile_description=profile_description)
                message='Successfully updated !'
            except Exception as e:
                message="Failed"
                print(e)
        else:
            message="Retry once again"

        response={
            "message":message
        }
        return Response(response)


class ProfessionalSettingsUserEmailAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=ProfessionalChangeUserNameSerializer(data=request.data)
        message=[]
        if serializer.is_valid(raise_exception=True):
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
            response={
                "message":"something went wrong",
                "data":None
            }
        
        return Response(response)



class ProfessionalSettingsUpdatePasswordAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        serializer=ProfessionalUpdatePasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
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
            message="failed"
            print('else')
        
        response={
            "data":None,
            "message":message
        }
        return Response(response)


class ProfessionalSettingsSkillsAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,format=None):
        try:
            profe_user=professional.objects.get(professional_user=request.user.id)
            professional_obj=professional_skills.objects.filter(user=profe_user.id)
            response={
                "message":"Success",
                "data":{
                    "skills":ProfessionalSkillsSerializer(professional_obj,many=True).data
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
        serializer=ProfessionalSkillsAddSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            print("reached")
            profe_user=professional.objects.get(professional_user=request.user.id)
            skill=request.data['skill']
            sample_skills = ["A# .NET","A# (Axiom)","A-0 System","A+","A++","ABAP","ABC","ABC ALGOL","ABLE","ABSET","ABSYS","ACC","Accent","Ace DASL","ACL2","ACT-III","Action!","ActionScript","Ada","Adenine","Agda","Agilent VEE","Agora","AIMMS","Alef","ALF","ALGOL 58","ALGOL 60","ALGOL 68","ALGOL W","Alice","Alma-0","AmbientTalk","Amiga E","AMOS","AMPL","APL","App Inventor for Android's visual block language","AppleScript","Arc","ARexx","Argus","AspectJ","Assembly language","ATS","Ateji PX","AutoHotkey","Autocoder","AutoIt","AutoLISP / Visual LISP","Averest","AWK","Axum","B","Babbage","Bash","BASIC","bc","BCPL","BeanShell","Batch (Windows/Dos)","Bertrand","BETA","Bigwig","Bistro","BitC","BLISS","Blue","Bon","Boo","Boomerang","Bourne shell","bash","ksh","BREW","BPEL","C","C--","C++","C#","C/AL","Caché ObjectScript","C Shell","Caml","Candle","Cayenne","CDuce","Cecil","Cel","Cesil","Ceylon","CFEngine","CFML","Cg","Ch","Chapel","CHAIN","Charity","Charm","Chef","CHILL","CHIP-8","chomski","ChucK","CICS","Cilk","CL","Claire","Clarion","Clean","Clipper","CLIST","Clojure","CLU","CMS-2","COBOL","Cobra","CODE","CoffeeScript","Cola","ColdC","ColdFusion","COMAL","Combined Programming Language","COMIT","Common Intermediate Language","Common Lisp","COMPASS","Component Pascal","Constraint Handling Rules","Converge","Cool","Coq","Coral 66","Corn","CorVision","COWSEL","CPL","csh","CSP","Csound","CUDA","Curl","Curry","Cyclone","Cython","D","DASL","DASL","Dart","DataFlex","Datalog","DATATRIEVE","dBase","dc","DCL","Deesel","Delphi","DinkC","DIBOL","Dog","Draco","DRAKON","Dylan","DYNAMO","E","E#","Ease","Easy PL/I","Easy Programming Language","EASYTRIEVE PLUS","ECMAScript","Edinburgh IMP","EGL","Eiffel","ELAN","Elixir","Elm","Emacs Lisp","Emerald","Epigram","EPL","Erlang","es","Escapade","Escher","ESPOL","Esterel","Etoys","Euclid","Euler","Euphoria","EusLisp Robot Programming Language","CMS EXEC","EXEC 2","Executable UML","F","F#","Factor","Falcon","Fancy","Fantom","FAUST","Felix","Ferite","FFP","Fjölnir","FL","Flavors","Flex","FLOW-MATIC","FOCAL","FOCUS","FOIL","FORMAC","@Formula","Forth","Fortran","Fortress","FoxBase","FoxPro","FP","FPr","Franz Lisp","Frege","F-Script","FSProg","G","Google Apps Script","Game Maker Language","GameMonkey Script","GAMS","GAP","G-code","Genie","GDL","Gibiane","GJ","GEORGE","GLSL","GNU E","GM","Go","Go!","GOAL","Gödel","Godiva","GOM (Good Old Mad)","Goo","Gosu","GOTRAN","GPSS","GraphTalk","GRASS","Groovy","Hack (programming language)","HAL/S","Hamilton C shell","Harbour","Hartmann pipelines","Haskell","Haxe","High Level Assembly","HLSL","Hop","Hope","Hugo","Hume","HyperTalk","IBM Basic assembly language","IBM HAScript","IBM Informix-4GL","IBM RPG","ICI","Icon","Id","IDL","Idris","IMP","Inform","Io","Ioke","IPL","IPTSCRAE","ISLISP","ISPF","ISWIM","J","J#","J++","JADE","Jako","JAL","Janus","JASS","Java","JavaScript","JCL","JEAN","Join Java","JOSS","Joule","JOVIAL","Joy","JScript","JScript .NET","JavaFX Script","Julia","Jython","K","Kaleidoscope","Karel","Karel++","KEE","Kixtart","KIF","Kojo","Kotlin","KRC","KRL","KUKA","KRYPTON","ksh","L","L# .NET","LabVIEW","Ladder","Lagoona","LANSA","Lasso","LaTeX","Lava","LC-3","Leda","Legoscript","LIL","LilyPond","Limbo","Limnor","LINC","Lingo","Linoleum","LIS","LISA","Lisaac","Lisp","Lite-C","Lithe","Little b","Logo","Logtalk","LPC","LSE","LSL","LiveCode","LiveScript","Lua","Lucid","Lustre","LYaPAS","Lynx","M2001","M4","Machine code","MAD","MAD/I","Magik","Magma","make","Maple","MAPPER","MARK-IV","Mary","MASM Microsoft Assembly x86","Mathematica","MATLAB","Maxima","Macsyma","Max","MaxScript","Maya (MEL)","MDL","Mercury","Mesa","Metacard","Metafont","MetaL","Microcode","MicroScript","MIIS","MillScript","MIMIC","Mirah","Miranda","MIVA Script","ML","Moby","Model 204","Modelica","Modula","Modula-2","Modula-3","Mohol","MOO","Mortran","Mouse","MPD","CIL","MSL","MUMPS","NASM","NATURAL","Napier88","Neko","Nemerle","nesC","NESL","Net.Data","NetLogo","NetRexx","NewLISP","NEWP","Newspeak","NewtonScript","NGL","Nial","Nice","Nickle","Nim","NPL","Not eXactly C","Not Quite C","NSIS","Nu","NWScript","NXT-G","o:XML","Oak","Oberon","Obix","OBJ2","Object Lisp","ObjectLOGO","Object REXX","Object Pascal","Objective-C","Objective-J","Obliq","Obol","OCaml","occam","occam-π","Octave","OmniMark","Onyx","Opa","Opal","OpenCL","OpenEdge ABL","OPL","OPS5","OptimJ","Orc","ORCA/Modula-2","Oriel","Orwell","Oxygene","Oz","P#","ParaSail (programming language)","PARI/GP","Pascal","Pawn","PCASTL","PCF","PEARL","PeopleCode","Perl","PDL","PHP","Phrogram","Pico","Picolisp","Pict","Pike","PIKT","PILOT","Pipelines","Pizza","PL-11","PL/0","PL/B","PL/C","PL/I","PL/M","PL/P","PL/SQL","PL360","PLANC","Plankalkül","Planner","PLEX","PLEXIL","Plus","POP-11","PostScript","PortablE","Powerhouse","PowerBuilder","PowerShell","PPL","Processing","Processing.js","Prograph","PROIV","Prolog","PROMAL","Promela","PROSE modeling language","PROTEL","ProvideX","Pro*C","Pure","Python","Q (equational programming language)","Q (programming language from Kx Systems)","Qalb","QtScript","QuakeC","QPL","R","R++","Racket","RAPID","Rapira","Ratfiv","Ratfor","rc","REBOL","Red","Redcode","REFAL","Reia","Revolution","rex","REXX","Rlab","RobotC","ROOP","RPG","RPL","RSL","RTL/2","Ruby","RuneScript","Rust","S","S2","S3","S-Lang","S-PLUS","SA-C","SabreTalk","SAIL","SALSA","SAM76","SAS","SASL","Sather","Sawzall","SBL","Scala","Scheme","Scilab","Scratch","Script.NET","Sed","Seed7","Self","SenseTalk","SequenceL","SETL","Shift Script","SIMPOL","SIGNAL","SiMPLE","SIMSCRIPT","Simula","Simulink","SISAL","SLIP","SMALL","Smalltalk","Small Basic","SML","Snap!","SNOBOL","SPITBOL","Snowball","SOL","Span","SPARK","Speedcode","SPIN","SP/k","SPS","Squeak","Squirrel","SR","S/SL","Stackless Python","Starlogo","Strand","Stata","Stateflow","Subtext","SuperCollider","SuperTalk","Swift (Apple programming language)","Swift (parallel scripting language)","SYMPL","SyncCharts","SystemVerilog","T","TACL","TACPOL","TADS","TAL","Tcl","Tea","TECO","TELCOMP","TeX","TEX","TIE","Timber","TMG","Tom","TOM","Topspeed","TPU","Trac","TTM","T-SQL","TTCN","Turing","TUTOR","TXL","TypeScript","Turbo C++","Ubercode","UCSD Pascal","Umple","Unicon","Uniface","UNITY","Unix shell","UnrealScript","Vala","VBA","VBScript","Verilog","VHDL","Visual Basic","Visual Basic .NET","Visual DataFlex","Visual DialogScript","Visual Fortran","Visual FoxPro","Visual J++","Visual J#","Visual Objects","Visual Prolog","VSXu","Vvvv","WATFIV, WATFOR","WebDNA","WebQL","Windows PowerShell","Winbatch","Wolfram","Wyvern","X++","X#","X10","XBL","XC","XMOS architecture","xHarbour","XL","Xojo","XOTcl","XPL","XPL0","XQuery","XSB","XSLT","XPath","Xtend","Yorick","YQL","Z notation","Zeno","ZOPL","ZPL"]
        
            if not skill:
                message="Skill is empty"
                return Response({"message":message})
            if skill not in sample_skills:
                message="Select Skill from given"
                return Response({"message":message})
            if professional_skills.objects.filter(user=profe_user.id,skill=skill).exists():
                message="Skill is already there"
                return Response({"message":message})
            else:
                professional_skills.objects.create(user=profe_user,skill=skill)
                message="Skill added successfully"
                return Response({"message":message})      


class ProfessionalDeleteSkillAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            professional_obj=professional.objects.get(professional_user=request.user.id)
            skill = professional_skills.objects.get(user=professional_obj.id,id=pk)
            skill.delete()
            message="Deleted Success"
           
        except Exception as e:
            print(e)
            message="Failed"
       

        response={
            "message":message,
            "data":None
        }

        return Response(response)


class ProfessionalSettingsUploadPictureAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        data = professional.objects.get( professional_user=request.user.id)
        serializer =ProfessionalUpdateimageSerializer(data ,data=request.data,partial=True)
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


       
            # data = professional.objects.get(professional_user=request.user.id)
            # try:
            #     profile_image=request.data['profile_image']
            #     _format, _dataurl =profile_image.split(';base64,')
            #     _filename, _extension   = secrets.token_hex(20), _format.split('/')[-1]
            #     try:
            #         file = ContentFile( base64.b64decode(_dataurl), name=f"{_filename}.{_extension}")
            #         if data.profile_picture == 'Null':
            #             data.profile_picture=file
            #             data.save()
            #         else:
            #             file_exists=os.path.exists(data.profile_picture.path)
            #             if file_exists == True:
            #                 os.remove(data.profile_picture.path)
            #             data.profile_picture=file
            #             data.save()
            #         message="Image successfully added"
            #     except:
            #         message="Image not added , please retry later"
            #     return Response({"message":message})
            # except:
                
class ProfessionalSettingsUploadResumeAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        data = professional.objects.get( professional_user=request.user.id)
        serializer =ProfessionalUpdateResumeSerializer(data ,data=request.data,partial=True)
        if serializer.is_valid(raise_exception=True):
            if data.resume == 'Null':
                serializer.save()
                message="Successfully updated... !"
            else:
                file_exists=os.path.exists(data.resume.path)
                if file_exists == True:
                    os.remove(data.resume.path)
                serializer.save()
            message="Successfully updated... !"
            return Response({"message":message})
        else:
            return Response({"message":"Failed"})
            
class ProfessionalFavouriteListAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        try:
            professional_data=professional.objects.get(professional_user=request.user.id)
            professional_favourite_program_data=professional_favourite_program.objects.filter(professional=professional_data.id)
            serializer=ProfessionalFavouriteProgramSerializer(professional_favourite_program_data,many=True).data
            
            message="Success"
        except:
            message="Failed"
            serializer=None
        

        response={
            "message":message,
            "data":serializer
        }
        return Response(response)

       


class PrefessionalFavouritePorgramAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        try:
            program_data=companyProgram.objects.get(id=pk)
            professional_data=professional.objects.get(professional_user=request.user.id)
            if professional_favourite_program.objects.filter(professional=professional_data,program_id=program_data).exists():
                professional_favourite_program.objects.filter(professional=professional_data,program_id=program_data).delete()
                message="Deleted from favourite"
            else:
                professional_data=professional.objects.get(professional_user=request.user.id)
                professional_favourite_program_data=professional_favourite_program.objects.create(professional=professional_data,program_id=program_data)
                message="added to favourite"

        except:
            message="Falied"

            
        response={
            "message":message,
            "data":None,
        }
        return Response(response)

class ProfessionalInformationAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def get(self,request):
        professional_obj=professional.objects.get(professional_user=request.user.id)
        try:
            professional_information_obj=professional_information.objects.get(professional=professional_obj.id)
            status=True
            message="success"
        except:
            message="failed"
            status=False
        return Response({"message":message,"status":status})

    def post(self,request,format=None):
        professional_obj=professional.objects.get(professional_user=request.user.id)
        serializer=professionalInformationSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            professional_information.objects.create(status=True,professional=professional_obj,country_names=serializer.data['country_names'])
            message="success"
        else:
            message="failed"
        return Response({"message":message})
class ProfessionalPaymentAPIView(APIView):
    renderer_classes=[UserRender]
    permission_classes=[IsAuthenticated]
    def post(self,request,format=None):
        print("reached")
        professional_data=professional.objects.get(professional_user=request.user.id)
        serializer = ProfessionalPaymentSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            wallet_object=professional_wallet.objects.get(professional=professional_data)
            amount=serializer.data['withdraw_amount']
            if wallet_object.amount > amount:
                total=wallet_object.amount-amount
                professional_wallet.objects.filter(professional=professional_data).update(amount=total)
                message="success"
            else:
                message="Don't have enough wallet balance"
        else:
            message="failed"
        return Response({"message":message})
# class ProfessionalSettingsOptionalEmailAPIView(APIView):
#     def post(self,request,format=None):
#         user=User.objects.get(id=2)
#         ExtendUser_obj=ExtendUser.objects.get(user=user.id)
#         print(ExtendUser_obj.optional_email_token)
#         token=request.data['token']
#         if ExtendUser_obj.optional_email_token == token:
#             message="email successfully verified"
#             ExtendUser.objects.filter(user=user.id).update(optional_email_status=True)
#         else:
#             message="Enter the right token"
#         response={
#             "message":message,
#         }
#         return Response(response)


# class ProfessionalSettingsPhoneNumberVerificationAPIView(APIView):
#     def post(self,request,format=None):
#         print("reached1")
#         country=request.POST.get('country')
#         phone_number=request.POST.get('phone_number')
#         code=request.POST.get('code')
#         ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
#         if code :
#             try:
#                 ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)
#                 if code == ValidateNumber_obj.code:
#                     ValidateNumber.objects.filter(user=ExtendUser_obj.id).update(status=True)
#                     message="Your phone number successfully validated"
#                 else:
#                     message="Security code doesnot match"
#             except:
#                 pass

#         else:
#             try:
#                 ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)

#             except:
#                 ValidateNumber_obj=None
#                 number=f'{country}{phone_number}'
#                 account_sid =settings.TWILIO_ACCOUNT_SID 
#                 auth_token = settings.TWILIO_AUTH_TOKEN
#                 client = Client(account_sid, auth_token)
#                 validation_code=9023456
#                 try:
#                         message_obj = client.messages.create(
#                                                 body=f'Your Vulnbounty security code {validation_code}',
#                                                 from_='+13862303382',
#                                                 to=number
#                                             )
#                         ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
#                         ValidateNumber.objects.create(user=ExtendUser_obj,message_id=message_obj.sid,phone_number=number,code=validation_code)
#                         message="Security code send to given number"
#                 except:
#                     message="Something went Wrong retry again"

