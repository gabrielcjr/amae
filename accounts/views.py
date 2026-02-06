from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import ChurchRegisterForm, MissionaryRegisterForm


def register_church(request):
    if request.method == "POST":
        form = ChurchRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("mission_field_map")
    else:
        form = ChurchRegisterForm()
    return render(request, "accounts/register_church.html", {"form": form})


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
