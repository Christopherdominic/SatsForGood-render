from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Donation
from .serializers import DonationSerializer
import requests
import os
from datetime import datetime
from django.db import models
from django.http import JsonResponse

# Load LNBits config
LNBits_API_KEY = os.getenv("LNBITS_API_KEY")
LNBits_BASE_URL = os.getenv("LNBITS_BASE_URL", "https://demo.lnbits.com")


# CREATE DONATION + INVOICE (PENDING)
@api_view(['POST'])
def create_invoice(request):
    amount = int(request.data.get('amount_sats'))
    donor_name = request.data.get('donor_name', '')

    headers = {
        "X-Api-Key": LNBits_API_KEY,
        "Content-type": "application/json"
    }

    payload = {
        "out": False,
        "amount": amount,
        "memo": f"Donation from {donor_name}"
    }

    response = requests.post(
        f"{LNBits_BASE_URL}/api/v1/payments",
        json=payload,
        headers=headers
    ).json()

    donation = Donation.objects.create(
        donor_name=donor_name,
        amount_sats=amount,
        invoice=response.get('payment_request'),
        payment_hash=response.get('payment_hash'),
        status="PENDING"
    )

    return Response({
        "invoice": donation.invoice,
        "payment_hash": donation.payment_hash,
        "status": donation.status
    })


#  CHECK PAYMENT STATUS (AUTO UPDATES TO PAID)
@api_view(['GET'])
def invoice_status(request, payment_hash):
    headers = {"X-Api-Key": LNBits_API_KEY}

    response = requests.get(
        f"{LNBits_BASE_URL}/api/v1/payments/{payment_hash}",
        headers=headers
    ).json()

    paid = response.get("paid", False)
    donation = Donation.objects.filter(payment_hash=payment_hash).first()

    if donation and paid and donation.status == "PENDING":
        donation.status = "PAID"
        donation.paid_at = datetime.now()
        donation.save()

    return Response({
        "status": donation.status if donation else "UNKNOWN",
        "paid_at": donation.paid_at if donation else None
    })


# SHOW BOTH PAID + PENDING (FOR UI TABLE)
@api_view(['GET'])
def recent_donations(request):
    donations = Donation.objects.all().order_by('-created_at')[:15]
    serializer = DonationSerializer(donations, many=True)
    return Response(serializer.data)


# STATS SHOULD COUNT ONLY PAID DONATIONS
def donation_stats(request):
    total_sats = Donation.objects.filter(status="PAID").aggregate(
        total=models.Sum("amount_sats")
    )["total"] or 0

    donor_count = Donation.objects.filter(status="PAID").count()

    return JsonResponse({
        "totalSats": total_sats,
        "donorCount": donor_count
    })
