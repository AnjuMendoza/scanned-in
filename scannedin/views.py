from django.shortcuts import render

# Home page view
def home(request):
    render(request, 'scannedin/home.html')