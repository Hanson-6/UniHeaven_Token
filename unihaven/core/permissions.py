# permissions.py

from rest_framework import permissions
from .models import University

class IsUniversityAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, University)