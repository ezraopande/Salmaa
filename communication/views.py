from .models import Message
from users.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def send_message(request):
    if request.method == "POST":
        receiver_username = request.POST["receiver_username"]
        content = request.POST["content"]
        
        try:
            receiver = User.objects.get(username=receiver_username)
            message = Message(sender=request.user, receiver=receiver)
            message.set_message(content)
            message.save()
            return redirect('inbox')
        except User.DoesNotExist:
            return render(request, 'communication/send_message.html', {'error': "User not found"})

    return render(request, 'communication/send_message.html')
