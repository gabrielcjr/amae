from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import InvestorRegisterForm, MissionaryRegisterForm


def register_investor(request):
    if request.method == "POST":
        form = InvestorRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("mission_field_map")
    else:
        form = InvestorRegisterForm()
    return render(request, "accounts/register_investor.html", {"form": form})


def register_missionary(request):
    if request.method == "POST":
        form = MissionaryRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("mission_field_map")
    else:
        form = MissionaryRegisterForm()
    return render(request, "accounts/register_missionary.html", {"form": form})
