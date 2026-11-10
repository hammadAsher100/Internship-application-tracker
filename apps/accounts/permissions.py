import logging
from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from apps.audit.services import record_event

logger = logging.getLogger(__name__)


def require_role(*roles):
    allowed = {str(role) for role in roles}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/login/?next={request.path}")
            if request.user.role not in allowed:
                logger.warning(
                    "unauthorized_access_attempt user_id=%s path=%s",
                    request.user.pk,
                    request.path,
                )
                record_event(request, "unauthorized_access_attempt", actor=request.user)
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.role not in self.allowed_roles
        ):
            logger.warning(
                "unauthorized_access_attempt user_id=%s path=%s",
                request.user.pk,
                request.path,
            )
            record_event(request, "unauthorized_access_attempt", actor=request.user)
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
