from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from .models import *
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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
            auth.login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login')
    else:
        return render(request, 'chat/login.html')
    
def logout_view(request):
    auth.logout(request)
    return redirect('login')
    
    
def home(request):
    if request.user.is_authenticated:
        return redirect('rooms')
    return render(request, 'chat/home.html')

def rooms(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    user_rooms = Room.objects.filter(participants=request.user)
    
    context = {
        'user_rooms': user_rooms,
    }
    return render(request, 'chat/rooms.html', context)

def room(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    
    room_name = pk.lower()
    room_obj = get_object_or_404(Room, name=room_name)
    
    # Check if user is a participant
    if request.user not in room_obj.participants.all():
        return redirect('room_detail', pk=pk)
    
    # Count only PENDING requests
    pending_requests = room_obj.join_requests.filter(status='pending').count()
    
    context = {
        'room': room_name,
        'username': request.user.username,
        'room_details': room_obj,
        'pending_count': pending_requests,
    }
    return render(request, 'chat/room.html', context)

def room_detail(request, pk):
    """Show room details and join request button"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    room_name = pk.lower()
    
    try:
        room_obj = Room.objects.get(name=room_name)
    except Room.DoesNotExist:
        messages.error(request, f'Room "{pk}" does not exist')
        return redirect('rooms')
    
    # If user is already a participant, redirect to room
    if request.user in room_obj.participants.all():
        return redirect('room', pk=pk)
    
    # Check if user already has a pending request
    existing_request = JoinRequest.objects.filter(room=room_obj, user=request.user).first()
    
    context = {
        'room': room_obj,
        'existing_request': existing_request,
        'is_creator': room_obj.creator == request.user,
    }
    return render(request, 'chat/room_detail.html', context)

def request_join(request, pk):
    """Send join request"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        room_name = pk.lower()
        room_obj = get_object_or_404(Room, name=room_name)
        
        # Check if already a participant
        if request.user in room_obj.participants.all():
            messages.info(request, 'You are already a member of this room')
            return redirect('room', pk=pk)
        
        # Create or get join request
        join_req, created = JoinRequest.objects.get_or_create(
            room=room_obj,
            user=request.user,
            defaults={'status': 'pending'}
        )
        
        if created:
            messages.success(request, 'Join request sent! Waiting for approval.')
        else:
            messages.info(request, 'You already have a pending request for this room.')
        
        return redirect('room_detail', pk=pk)

def room_requests(request, pk):
    """Show pending join requests for room creator"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    room_name = pk.lower()
    room_obj = get_object_or_404(Room, name=room_name)
    
    # Check if user is the creator
    if room_obj.creator != request.user:
        messages.error(request, 'Only the room creator can approve requests')
        return redirect('rooms')
    
    pending_requests = room_obj.join_requests.filter(status='pending')
    
    context = {
        'room': room_obj,
        'pending_requests': pending_requests,
    }
    return render(request, 'chat/room_requests.html', context)

def approve_request(request, request_id):
    """Approve join request"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    join_req = get_object_or_404(JoinRequest, id=request_id)
    
    # Check if user is the room creator
    if join_req.room.creator != request.user:
        messages.error(request, 'Only the room creator can approve requests')
        return redirect('rooms')
    
    join_req.status = 'approved'
    join_req.save()
    
    # Add user to room participants
    join_req.room.participants.add(join_req.user)
    
    messages.success(request, f'{join_req.user.username} approved!')
    return redirect('room', pk=join_req.room.name)

def reject_request(request, request_id):
    """Reject join request"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    join_req = get_object_or_404(JoinRequest, id=request_id)
    
    # Check if user is the room creator
    if join_req.room.creator != request.user:
        messages.error(request, 'Only the room creator can reject requests')
        return redirect('rooms')
    
    join_req.status = 'rejected'
    join_req.save()
    
    messages.info(request, f'{join_req.user.username} request rejected')
    return redirect('room_requests', pk=join_req.room.name)

def create_room(request):
    """Create a new room"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        room_name = request.POST.get('room_name', '').lower().strip()
        
        if not room_name:
            messages.error(request, 'Room name cannot be empty')
            return redirect('rooms')
        
        # Check if room already exists
        if Room.objects.filter(name=room_name).exists():
            messages.info(request, 'This room already exists. Join it instead!')
            return redirect('rooms')
        
        # Create room with current user as creator
        room = Room.objects.create(name=room_name, creator=request.user)
        room.participants.add(request.user)
        
        messages.success(request, f'Room "{room_name}" created successfully!')
        return redirect('room', pk=room_name)
    
    return redirect('rooms')

def get_pending_count(request, room_name):
    """Get pending join requests count for a room"""
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    
    try:
        room = Room.objects.get(name=room_name.lower())
        
        # Only room creator can see pending count
        if room.creator != request.user:
            return JsonResponse({'count': 0})
        
        pending_count = room.join_requests.filter(status='pending').count()
        return JsonResponse({'count': pending_count})
    except Room.DoesNotExist:
        return JsonResponse({'count': 0})

def getMessages(request, room_name):
    room = get_object_or_404(Room, name=room_name.lower())
    messages_list = Message.objects.filter(room=room).order_by('timestamp')
    
    message_list = []
    for message in messages_list:
        message_list.append({
            'user': message.sender.username,
            'value': message.content,
            'date': message.timestamp.strftime('%d %b %Y, %I:%M %p')
        })
    
    return JsonResponse({'messages': message_list})

@csrf_exempt
def send(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)
        
        room_id = request.POST.get('room_id')
        message_content = request.POST.get('message')
        
        room = get_object_or_404(Room, id=room_id)
        
        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=message_content
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)