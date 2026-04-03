from django.urls import path

from .views import ContractSearchView

urlpatterns = [
    path("search/", ContractSearchView.as_view(), name="contract_search"),
]
