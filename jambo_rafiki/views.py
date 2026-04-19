from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

def home_view(request):
    """
    Homepage view for Jambo Rafiki backend.
    Shows a welcome message and redirects to admin after a short delay.
    """
    if request.user.is_authenticated:
        # Optionally, redirect staff directly to admin
        return HttpResponseRedirect(reverse('admin:index'))
    return render(request, "home.html")
