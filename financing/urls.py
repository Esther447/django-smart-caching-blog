from django.urls import path
from .views import FinancingListCreateView

urlpatterns = [
    path("financing/", FinancingListCreateView.as_view()),
]
