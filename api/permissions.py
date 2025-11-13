from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'teacher') or request.user.is_staff


class IsOwnerTeacherOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Admin puede todo
        if request.user.is_staff:
            return True
        # Profesores solo sobre sus propios registros
        return hasattr(request.user, 'teacher') and obj.teacher == request.user
