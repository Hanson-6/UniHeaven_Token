# authentication.py

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import University

class UniversityTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('Authorization')
        if not token:
            raise AuthenticationFailed('No token provided')
        try:
            # 假设 Token 以 "Token <token>" 的形式传递
            token = token.split(" ")[1]
            university = University.objects.get(token=token)
            return (university, None)
        except (IndexError, University.DoesNotExist):
            raise AuthenticationFailed('Invalid token')