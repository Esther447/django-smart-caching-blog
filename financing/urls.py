from django.urls import path
from .views import FinancingCreateView, FinancingListView, FinancingUpdateView

urlpatterns = [
    path('', FinancingListView.as_view(), name='financing-list'),
    path('create/', FinancingCreateView.as_view(), name='financing-create'),
    path('<int:pk>/update/', FinancingUpdateView.as_view(), name='financing-update'),
]
