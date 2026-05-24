from rest_framework import generics
from .models import FinancingRequest
from .serializers import FinancingRequestSerializer
from alerts.tasks import send_financing_alert

class FinancingListCreateView(generics.ListCreateAPIView):
    queryset = FinancingRequest.objects.all().order_by("-created_at")
    serializer_class = FinancingRequestSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        send_financing_alert(instance.id)
