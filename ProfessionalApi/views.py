from rest_framework.views import APIView
from rest_framework.response import Response
from .models import professional,professional_information,professional_skills,professional_favourite_program,professional_skills
from CompanyApi.models import companyProgram,submission
from django.db.models import Q
from CompanyApi.serializers import CompanyProgramSerializer,CompanySubmissionSerializer 
from django.contrib.auth.models import User
from .serializers import ProfessionalRegisterSdrializer,ProfessionalDashbordserializer,ProfessionalFavouriteProgramSerializer,ProfessionalChangeNameSerialzer,ProfessionalUpdateimageSerializer,ProfessionalUpdateResumeSerializer,ProfessionalSkillsAddSerializer,ProfessionalSkillsSerializer
from django.contrib.auth import authenticate, login, logout
import re
import uuid
from MainApi.models import ExtendUser,ValidateNumber
from .helpers import send_email_verification_mail
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
# Create your views here.

user_id=2

user=User.objects.get(id=user_id)
class ProfessionalRegisterAPIView(APIView):
     def post(self,request):
        serializer=ProfessionalRegisterSdrializer(data=request.data)
        print(request.data)
        client_key=request.data('g-recaptcha-response')
        secret_key=settings.RECAPTCHA_SECRET_KEY
        captcha_data={
                "secret":secret_key,
                "response":client_key
            }
        response_data=requests.post('https://www.google.com/recaptcha/api/siteverify',captcha_data)
        response=json.loads(response_data.text)
        verify=response['success']
        print(f'verify is = {verify}')
        if verify == True:
            terms_and_policy=request.data('terms_and_policy')
            if not terms_and_policy == 'checked':
                message="please tick the privacy policy and terms"
            else:
                if serializer.is_valid(raise_exception=True):
                    password=serializer.cleaned_data.get('password')
                    confirm_password=serializer.cleaned_data.get('confirm_password')
                    if password != confirm_password:
                        message="password and confirm pasword didn't match"
                        return Response({"message":message})
                    token = str(uuid.uuid4())
                    user=serializer.save(commit=False)
                    user.password=make_password(request.POST['password'])
                    user.username=serializer.cleaned_data['username']
                    user.email_verification_token=  token
                    user.save()
                    company_obj = company.objects.create(company_user=user,email_verification_token= token,terms_and_policy=True)
                    if company_obj:
                        company_wallet.objects.create(company=company_obj)
                        send_email_verification_mail(request,user.email,token)
                        messsage='Account created Successfully ! verify your email'
                    else:
                        message='Account not created retry again'
                    return Response({"path":"ifreached"})
                    
                else:
                    print("elsereached")
                    return Response({"path":"elsereached"})
        else:
            message="reCAPTCHA not verifyied"
        return Response({"message":messsage}) 
    

class ProfessionalDashboardAPIView(APIView):
    def get(self,request):
        print("reached")
        try:
            submission_today=submission.objects.filter(user=user.id,created_at__date=date.today()).count()
            submission_this_month=submission.objects.filter(user=user.id,created_at__month=date.today().month).count()
            leaderboard= professional.objects.filter(reward__gte=1).order_by('-reward')[:5]
            program=companyProgram.objects.filter(created_at=date.today())[:5]
            payment_today = payments.objects.filter(transfer_to=user.id,created_at__date=date.today()).aggregate(Sum('amount'))
            payment_this_month=payments.objects.filter(transfer_to = user.id,created_at__month=date.today().month).aggregate(Sum('amount'))

            response={
                "message":'success',
                "data":{'user':user.username,
            "submission_today":submission_today,
            "submission_this_month":submission_this_month,
            "leaderboard":ProfessionalDashbordserializer(leaderboard,many=True).data,
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
    def get(self,request):
            professional_obj=professional.objects.get(professional_user=user)
            professional_information_obj=professional_information.objects.get(professional=professional_obj.id)
            region=professional_information_obj.country_names
            data=companyProgram.objects.all().filter((Q(region ='all') | Q(region = region) )) # & ~Q(visibility='P')
            # invited_program=private_invitation.objects.filter(hunter=professional_obj.id)
            response={
                "data":{
                    "programs_obj":CompanyProgramSerializer(data,many=True).data
                }
            }
            return Response(response)


class ProfessionalProgramDetailsAPIView(APIView):
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

class ProfessionalProgramSubmissionAPIView(APIView):
    def post(self,request):
        try:
            serializer=ProfessionalprogramSubmissionSerializer(request.data)
            if  serializer.is_valid():
                serializer.save()
        except Exception as e:
            print(e)
      
class ProfessionalSubmissionAPIView(APIView):
    def get(self,request):
        user=User.objects.get(id=2)
       
        all_submission=submission.objects.filter(user=user.id)
        pending_submission=submission.objects.filter(user=user.id,status="pending")
        rejected_submission=submission.objects.filter(user=user.id,status="rejected")
        accepted_submission=submission.objects.filter(user=user.id,status="accepted")
        completed_submission=submission.objects.filter(user=user.id,status="completed")

        response={
            "data":{
                "all_submission":CompanySubmissionSerializer(all_submission,many=True).data,
                "pending_submission":CompanySubmissionSerializer(pending_submission,many=True).data,
                "rejected_submission":CompanySubmissionSerializer(rejected_submission,many=True).data,
                "accepted_submission":CompanySubmissionSerializer(accepted_submission,many=True).data,
                "completed_submission":CompanySubmissionSerializer(completed_submission,many=True).data
            }
        }

        return Response(response)

class ProfessionalSubmissionDetailsAPIView(APIView):
    def get(self,request,pk):
        try:
            data=submission.objects.get(program=pk,user=user.id)
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
class ProfessionalDeleteSkillAPIView(APIView):
    def get(self,request,pk):
        user=User.objects.get(id=2)
        try:
            professional_obj=professional.objects.get(professional_user=user.id)
            skill = professional_skills.objects.get(user=professional_obj.id,id=pk)
            skill.delete()
            message="Success"
           
        except Exception as e:
            print(e)
            message="Failed"
       

        response={
            "message":message,
            "data":None
        }

        return Response(response)

class PrefessionalFavouritePorgramAPIView(APIView):
    def get(self,request,pk):
        try:
            program_data=companyProgram.objects.get(id=pk)
            professional_data=professional.objects.get(professional_user=user.id)
            if professional_favourite_program.objects.filter(professional=professional_data,program_id=program_data).exists():
                professional_favourite_program.objects.filter(professional=professional_data,program_id=program_data).delete()
                message="Deleted from favourite"
            else:
                professional_data=professional.objects.get(professional_user=user.id)
                professional_favourite_program_data=professional_favourite_program.objects.create(professional=professional_data,program_id=program_data)
                message="added to favourite"

        except:
            message="Falied"

            
        response={
            "message":message,
            "data":None,
        }
        return Response(response)


class ProfessionalFavouriteListAPIView(APIView):
    def get(self,request):
        try:
            user=User.objects.get(id=2)
            professional_data=professional.objects.get(professional_user=user.id)
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


class ProfessionalSettingsNameDescriptionAPIView(APIView):
    def post(self,request,format=None):
        serializer=ProfessionalChangeNameSerialzer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            first_name=request.data['first_name']
            last_name=request.data['last_name']
            profile_description=request.data['description']
            print(first_name,last_name,profile_description)
            
            if not first_name or not last_name or not profile_description:
                message='profile field should not empty!'
            else:
                if not first_name.isalpha() or not last_name.isalpha():
                    message="first name or last name is invalid , only alphabet"
                else:
                    User.objects.filter(id=user.id).update(first_name=first_name,last_name=last_name)
                    p = professional.objects.filter(professional_user = user.id).update(profile_description=profile_description)
                    message="Successfully updated !"
            print("reached")
        else:
            message="Failed"
            print("else")
        response={
            "message":message,
            "data":None
        }
        return Response(response)

class ProfessionalSettingsUserEmailAPIView(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        try:
                regex = "^([a-z]+('[a-z])?[0-9a-z]*)$"
                username = request.data['username']
                email = request.data['email']
                password = request.data['password']
                print(username,email,password)
                user = authenticate(
                    request, username=user.username, password=password)
                if not username or not email or not password:
                    message='Field not to be empty.username,email,password required'
                    return Response(message)
                else:
                    if not re.search(regex, username):
                        message="Allowed are alphabet,number and apostrophe"
                if user is not None:
                    if user.username != username:
                        if User.objects.filter(username=username).exists():
                            message='Username already taken'
                        else:
                            User.objects.filter(id=user.id).update(username=username)
                            message='Username successfully updated !'
                    if User.objects.filter(email=email).exists() or ExtendUser.objects.filter(optional_email=email).exists() :
                        message='Email already taken'
                    else:
                        token = str(uuid.uuid4())
                        try:
                            print("reached in try")
                            ExtendUser_obj= ExtendUser.objects.get(user=request.user.id)
                            if request.user.email != email!=ExtendUser_obj.optional_email:
                                ExtendUser.objects.filter(user=user.id).update(optional_email=email,optional_email_token =token,optional_email_status=False)
                                send_email_verification_mail(email,token)
                                message='Email successfully updated !'
                            else:
                                message='You already added this Email'
                        except:
                            ExtendUser.objects.create(user=user,optional_email=email,optional_email_token=token)
                            send_email_verification_mail(email,token)
                            message='Email successfully Added !'
            
                else:
                    message='Password doesnot match'
                response={
                    "message":message
                }
                return Response(response)
        except Exception as e:
            message="failed"
            print(e)
            response={
                "message":message
            }
            return Response(response)
    
class ProfessionalSettingsSkillsAPIView(APIView):
    def get(self,request,format=None):
        try:
            profe_user=professional.objects.get(professional_user=user.id)
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
            profe_user=professional.objects.get(professional_user=user.id)
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

class ProfessionalSettingsUploadPictureAPIView(APIView):
    def post(self,request,format=None):
            user=User.objects.get(id=2)
            data = professional.objects.get(professional_user=user.id)
            try:
                profile_image=request.POST.get('profile_image')
                _format, _dataurl =profile_image.split(';base64,')
                _filename, _extension   = secrets.token_hex(20), _format.split('/')[-1]
                try:
                    file = ContentFile( base64.b64decode(_dataurl), name=f"{_filename}.{_extension}")
                    if data.profile_picture == 'Null':
                        data.profile_picture=file
                        data.save()
                    else:
                        file_exists=os.path.exists(data.profile_picture.path)
                        if file_exists == True:
                            os.remove(data.profile_picture.path)
                        data.profile_picture=file
                        data.save()
                    message="Image successfully added"
                except:
                    message="Image not added , please retry later"
                return Response({"message":message})
            except:
                serializer =ProfessionalUpdateimageSerializer(request.body,request.FILES)
                if not request.FILES:
                    message="Image is empty"
                if serializer.is_valid():
                    data = professional.objects.get(professional_user=request.user.id)
                    if data.profile_picture == 'Null':
                        serializer.save()
                    else:
                        file_exists=os.path.exists(data.profile_picture.path)
                        if file_exists == True:
                            os.remove(data.profile_picture.path)
                        serializer.save()
                    message="Successfully updated !"
                else:
                    message="Please select a valid image file"
                return Response({"message":message})
               
class ProfessionalSettingsOptionalEmailAPIView(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        ExtendUser_obj=ExtendUser.objects.get(user=user.id)
        print(ExtendUser_obj.optional_email_token)
        token=request.data['token']
        if ExtendUser_obj.optional_email_token == token:
            message="email successfully verified"
            ExtendUser.objects.filter(user=user.id).update(optional_email_status=True)
        else:
            message="Enter the right token"
        response={
            "message":message,
        }
        return Response(response)

class ProfessionalSettingsUploadResumeAPIView(APIView):
    def post(self,request,format=None):
        user=User.objects.get(id=2)
        data = professional.objects.get(professional_user=user.id)
        serializer = ProfessionalUpdateResumeSerializer(data=request.data)
        if not request.FILES:
            message="FIle is required"
            
        if serializer.is_valid():
            data = professional.objects.get(professional_user=request.user.id)
            if data.profile_picture == 'Null':
                serializer.save()
            else:
                file_exists=os.path.exists(data.profile_picture.path)
                if file_exists == True:
                    os.remove(data.profile_picture.path)
                serializer.save()
          
            message="Resume uploaded !"
        else:
            message="PDF is allowed"

        response={
            "message":message
        }
        return Response(response)

class ProfessionalSettingsPhoneNumberVerificationAPIView(APIView):
    def post(self,request,format=None):
        print("reached1")
        country=request.POST.get('country')
        phone_number=request.POST.get('phone_number')
        code=request.POST.get('code')
        ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
        if code :
            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)
                if code == ValidateNumber_obj.code:
                    ValidateNumber.objects.filter(user=ExtendUser_obj.id).update(status=True)
                    message="Your phone number successfully validated"
                else:
                    message="Security code doesnot match"
            except:
                pass

        else:
            try:
                ValidateNumber_obj=ValidateNumber.objects.get(user=ExtendUser_obj.id)

            except:
                ValidateNumber_obj=None
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
                        ExtendUser_obj=ExtendUser.objects.get(user=request.user.id)
                        ValidateNumber.objects.create(user=ExtendUser_obj,message_id=message_obj.sid,phone_number=number,code=validation_code)
                        message="Security code send to given number"
                except:
                    message="Something went Wrong retry again"

