from django.urls import path
from .views import case_list, case_detail, assign_case

urlpatterns = [
    path('cases/', case_list, name='case_list'),
    path('cases/<int:case_id>/', case_detail, name='case_detail'),  # Case detail page
    path('assign-case/<int:case_id>/', assign_case, name='assign_case'),
]
