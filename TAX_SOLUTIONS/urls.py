from django.urls import path
from .views import TaxSolutions

urlpatterns = [
    path("solution/", TaxSolutions.as_view(), name="get_tax_solutions"),

]
