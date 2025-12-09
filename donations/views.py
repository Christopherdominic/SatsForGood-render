from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Donation
from .serializers import DonationSerializer
import requests
import os
from datetime import datetime
from django.db import models
from django.http import JsonResponse

LNBits_API_KEY = os.getenv("LNBITS_API_KEY")
LNBits_BASE_URL = os.getenv("LNBITS_BASE_URL", "https://legend.lnbits.com")

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
        invoice=response['payment_request'],
        payment_hash=response['payment_hash'],
        status="PENDING"
    )

    return Response({
        "invoice": donation.invoice,
        "payment_hash": donation.payment_hash
    })


@api_view(['GET'])
def invoice_status(request, payment_hash):
    headers = {"X-Api-Key": LNBits_API_KEY}

    response = requests.get(
        f"{LNBits_BASE_URL}/api/v1/payments/{payment_hash}",
        headers=headers
    ).json()

    paid = response.get("paid", False)
    status = "PAID" if paid else "PENDING"

    donation = Donation.objects.filter(payment_hash=payment_hash).first()

    if donation and paid and donation.status != "PAID":
        donation.status = "PAID"
        donation.paid_at = datetime.now()
        donation.save()

    return Response({
        "status": donation.status if donation else "UNKNOWN",
        "paid_at": donation.paid_at if donation else None
    })


@api_view(['GET'])
def recent_donations(request):
    # ✅ ONLY SHOW PAID DONATIONS
    donations = Donation.objects.filter(status="PAID").order_by('-paid_at')[:10]
    serializer = DonationSerializer(donations, many=True)
    return Response(serializer.data)


def donation_stats(request):
    # ✅ ONLY COUNT PAID DONATIONS
    total_sats = Donation.objects.filter(status="PAID").aggregate(
        total=models.Sum("amount_sats")
    )["total"] or 0

    donor_count = Donation.objects.filter(status="PAID").count()

    return JsonResponse({
        "totalSats": total_sats,
        "donorCount": donor_count
    })
