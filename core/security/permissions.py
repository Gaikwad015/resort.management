from rest_framework import permissions
from core.security.crypto import StepUpTokenManager
from core.security.audit import log_security_event

class IsOwnerOrStaff(permissions.BasePermission):
    """
    OWASP A01:2025 - Broken Access Control & IDOR/BOLA Defense.
    Ensures that regular guests can ONLY view or modify their own objects.
    Hotel staff (Super Admin, Admin, Manager, Receptionist) have operational oversight.
    """
    STAFF_ROLES = ['SUPER_ADMIN', 'ADMIN', 'HOTEL_MANAGER', 'RECEPTIONIST']

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Staff roles are authorized for operational oversight
        if getattr(request.user, 'role', None) in self.STAFF_ROLES or request.user.is_superuser:
            return True
        
        # Check direct ownership attribute
        if hasattr(obj, 'user'):
            is_owner = obj.user == request.user
        elif hasattr(obj, 'id') and obj == request.user:
            is_owner = True
        else:
            is_owner = False

        if not is_owner:
            log_security_event(
                event_type='UNAUTHORIZED_ACCESS',
                severity='HIGH',
                request=request,
                details={
                    'reason': 'IDOR/BOLA Attempt: Attempted to access unowned resource',
                    'resource_id': str(getattr(obj, 'id', 'unknown'))
                },
                status_code=403
            )

        return is_owner

class RoleRequired:
    """
    Factory creating a permission class that strictly requires one of the specified roles.
    Example: permission_classes = [RoleRequired(['SUPER_ADMIN', 'ADMIN'])]
    """
    def __init__(self, allowed_roles):
        self.allowed_roles = allowed_roles

    def __call__(self):
        allowed = self.allowed_roles
        
        class DynamicRolePermission(permissions.BasePermission):
            def has_permission(self, request, view):
                if not (request.user and request.user.is_authenticated):
                    return False
                if request.user.is_superuser:
                    return True
                user_role = getattr(request.user, 'role', None)
                has_role = user_role in allowed
                if not has_role:
                    log_security_event(
                        event_type='UNAUTHORIZED_ACCESS',
                        severity='MEDIUM',
                        request=request,
                        details={
                            'reason': 'RBAC Violation: Missing required role',
                            'user_role': user_role,
                            'required_roles': allowed
                        },
                        status_code=403
                    )
                return has_role
        return DynamicRolePermission

class RequiresStepUpAuth(permissions.BasePermission):
    """
    OWASP A07:2025 & A01:2025: Step-Up Authentication.
    Demands that high-risk operations (e.g. refunding a booking, changing admin roles, cancelling bookings)
    provide a valid, recently issued Step-Up Authentication Token in the `X-Step-Up-Token` header.
    """
    ACTION_NAME = "HIGH_RISK_OPERATION"

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        step_up_token = request.headers.get('X-Step-Up-Token')
        if not step_up_token:
            return False

        action = getattr(view, 'step_up_action', self.ACTION_NAME)
        valid, msg = StepUpTokenManager.verify_token(step_up_token, str(request.user.id), action)
        
        if not valid:
            log_security_event(
                event_type='UNAUTHORIZED_ACCESS',
                severity='HIGH',
                request=request,
                details={'reason': f'Step-Up Verification Failed: {msg}'},
                status_code=403
            )
            return False
            
        return True
