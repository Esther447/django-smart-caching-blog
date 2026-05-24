from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import FinancingRequest
from .serializers import FinancingRequestSerializer
from alerts.tasks import send_financing_alert

class FinancingCreateView(generics.CreateAPIView):
    queryset = FinancingRequest.objects.all()
    serializer_class = FinancingRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        send_financing_alert(instance.id)

class FinancingUpdateView(generics.UpdateAPIView):
    queryset = FinancingRequest.objects.all()
    serializer_class = FinancingRequestSerializer
    permission_classes = [IsAuthenticated]


class FinancingListView(generics.ListAPIView):
    queryset = FinancingRequest.objects.all().order_by('-created_at')
    serializer_class = FinancingRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'merchant']
