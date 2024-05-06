from rest_framework.views import APIView
from rest_framework import status
from .razorpay_serializers import RazorpayOrderSerializer, TranscationModelSerializer
from CompanyApi.api.razorpay.main import RazorpayClient
from CompanyApi.models import company, company_wallet, company_wallet_history, company_razorpay_account
from rest_framework.response import Response
from .razorpay import client
import http.client
import json
import requests
from django.conf import settings

rz_client = RazorpayClient()


class RazorpayOrderAPIView(APIView):
    """This API will create an order"""

    def post(self, request):
        razorpay_order_serializer = RazorpayOrderSerializer(data=request.data)
        if razorpay_order_serializer.is_valid():

            order_response = rz_client.create_order(
                amount=razorpay_order_serializer.validated_data.get("amount"),
                currency=razorpay_order_serializer.validated_data.get(
                    "currency"),
            )
            response = {
                "status_code": status.HTTP_201_CREATED,
                "message": "order created",
                "data": order_response,
            }
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            response = {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "bad request",
                "error": razorpay_order_serializer.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class TransactionAPIView(APIView):
    """This API will complete order and save the
    transaction"""

    def post(self, request):
        transaction_serializer = TranscationModelSerializer(data=request.data)
        if transaction_serializer.is_valid():
            rz_client.verify_payment_signature(
                razorpay_payment_id=transaction_serializer.validated_data.get(
                    "payment_id"
                ),
                razorpay_order_id=transaction_serializer.validated_data.get(
                    "order_id"),
                razorpay_signature=transaction_serializer.validated_data.get(
                    "signature"
                ),
            )

            company_obj = company.objects.get(
                company_user=request.user)

            wallet = company_wallet.objects.filter(company=company_obj.id)
            walletobj = wallet.get()

            amount = walletobj.amount + \
                transaction_serializer.validated_data.get('amount')

            wallet.update(
                amount=amount
            )
            company_wallet_history.objects.create(company=company_obj,
                                                  amount=(
                                                      transaction_serializer.validated_data.get('amount')),
                                                  description='Money added to wallet via razorpay',
                                                  status='cr')

            response = {
                "status_code": status.HTTP_201_CREATED,
                "message": "Amount added to wallet",
            }
            return Response(response, status=status.HTTP_201_CREATED)
        else:
            response = {
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "bad request",
                "error": transaction_serializer.errors,
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)





class CreateAccount(APIView):
    def post(self, request):
        contact_url = 'https://api.razorpay.com/v1/contacts'
        fund_url = 'https://api.razorpay.com/v1/payouts'

        company_obj = company.objects.get(
            company_user=request.user)
        amount = int((request.data.get('amount')))
        print(amount*100)
        data = {
            "account_number": '2323230029804267',
            "amount": amount*100,
            "currency": "INR",
            "mode": "NEFT",
            "purpose": "refund",
            "fund_account": {
                "account_type": "bank_account",
                "bank_account": {
                    "name": request.data.get('name'),
                    "ifsc": request.data.get('IFSC_code'),
                    "account_number": request.data.get('account_number')
                },
                "contact": {
                    "name": company_obj.company_user.first_name + company_obj.company_user.last_name,
                    "email": company_obj.company_user.email,
                    "type": "self",
                    "reference_id": str(company_obj.company_user.id),
                    "notes": {
                        "company_username": company_obj.company_user.username,
                    }
                }
            },
            "queue_if_low_balance": True,
            "reference_id": str(company_obj.company_user.id),
            "narration": "Withdraw from VulnBounty",
            "notes": {
                "company_username": company_obj.company_user.username,
            }
        }

        response = requests.post(fund_url, auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ), json=data)

        if (response.status_code == 200):
            fundAccObj = response.json().get('fund_account')
            contactsObj = fundAccObj.get('contact')
            acc_id = contactsObj.get('id')

            details = company_razorpay_account.objects.filter(
                company=company_obj)
            if not details:
                print('inside')
                company_razorpay_account.objects.create(
                    company=company_obj, acc_id=acc_id)

            wallet = company_wallet.objects.filter(company=company_obj.id)
            walletobj = wallet.get()

            amount = walletobj.amount - float(request.data.get('amount'))
            wallet.update(
                amount=amount
            )
            company_wallet_history.objects.create(company=company_obj,
                                                  amount=float(
                                                      request.data.get('amount')),
                                                  description='Withdraw from wallet',
                                                  status='db')


            return Response({'message': "Money will be added to bank account in sometime.", 'data': response.json()}, status=200)

        else:

            return Response({'message': 'Failed', 'data': response.text}, status=500)


class FundAccounts(APIView):
    def get(self, request):
        url = 'https://api.razorpay.com/v1/fund_accounts'
        company_obj = company.objects.get(
            company_user=request.user)
        razorpay_obj = company_razorpay_account.objects.filter(
            company=company_obj).get()
        acc_id = razorpay_obj.acc_id
        print(acc_id)

        response = requests.get(url, auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))

        items = response.json().get('items')

        accounts = []
        for acc in items:
            if acc_id in acc['contact_id']:
                accounts.append(acc)

        return Response({'data': accounts})
