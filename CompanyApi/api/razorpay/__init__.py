import razorpay
from django.conf import settings


client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_KEY_SECRET
    # "rzp_test_j4mCniIQP4n8bv",
    # "KACx5kr8XHt1Xno1e1jYIXRd"
)
)
