from django.urls import path
from .api_razorpay import RazorpayOrderAPIView, TransactionAPIView,CreateAccount,FundAccounts

urlpatterns = [
    path("order/create/",
        RazorpayOrderAPIView.as_view(),
        name="razorpay-create-order-api"
    ),
    path("order/complete/",
        TransactionAPIView.as_view(),
        name="razorpay-complete-order-api"
    ),
    path("account/create",
        CreateAccount.as_view(),
        name="razorpay-create-account-api"
    ),

    path("accounts/",
        FundAccounts.as_view(),
        name="razorpay-fund-account-api"
    ),
]