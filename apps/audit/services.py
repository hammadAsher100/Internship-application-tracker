from apps.audit.models import AuditLog


def record_event(request, action, actor=None, target=None, metadata=None):
    ip_address = request.META.get("REMOTE_ADDR")
    if ip_address:
        ip_address = ip_address[:45]
    target_type = target_id = ""
    if target is not None:
        target_type = target._meta.label_lower
        target_id = str(target.pk)
    return AuditLog.objects.create(
        actor=actor,
        actor_role=getattr(actor, "role", "") if actor else "",
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {},
        ip_address=ip_address,
    )
