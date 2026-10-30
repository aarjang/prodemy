from django.shortcuts import render

from prices.views import price_status


def home(request):
    return render(request, "core/home.html", price_status())
