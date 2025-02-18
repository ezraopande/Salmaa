from django.db import models
from users.models import User
from django.db import models
from users.models import User
from cryptography.fernet import Fernet
import base64


# Generate a key (keep this secret)
SECRET_KEY = base64.urlsafe_b64encode(Fernet.generate_key())

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    encrypted_content = models.BinaryField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def set_message(self, content):
        f = Fernet(SECRET_KEY)
        self.encrypted_content = f.encrypt(content.encode())

    def get_message(self):
        f = Fernet(SECRET_KEY)
        return f.decrypt(self.encrypted_content).decode()


# Generate a key (keep this secret)
SECRET_KEY = base64.urlsafe_b64encode(Fernet.generate_key())

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    encrypted_content = models.BinaryField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def set_message(self, content):
        f = Fernet(SECRET_KEY)
        self.encrypted_content = f.encrypt(content.encode())

    def get_message(self):
        f = Fernet(SECRET_KEY)
        return f.decrypt(self.encrypted_content).decode()
