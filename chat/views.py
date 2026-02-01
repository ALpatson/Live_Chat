from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.shortcuts import redirect

from django.contrib.auth import authenticate, login, logout
# Create your views here.



def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Already Used')
                return redirect('register')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')
        else:
            messages.info(request, 'Password Not Matching')
            return redirect('register')
    else:
        return render(request, 'chat/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login')
    else:
        return render(request, 'chat/login.html')
    
    
def index(request):
    return render(request, 'chat/index.html')