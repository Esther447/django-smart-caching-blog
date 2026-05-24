from rest_framework import serializers
from .models import FinancingRequest

class FinancingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancingRequest
        fields = "__all__"
