"""
Signal receivers for the stockT application.

- handle_stock_usage_approval: automatically reduces/deletes stock when a
  StockUsage request is approved.
- log_kit_deletion: keeps the audit trail consistent when a Kit is deleted.
"""
import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Kit, KitType, NotificationLog, StockUsage, User, WorkspaceMember

logger = logging.getLogger('stockT')


@receiver(post_save, sender=StockUsage)
def handle_stock_usage_approval(sender, instance, created, **kwargs):
    """Apply an approved usage to matching stock exactly once.

    Stock rows are locked and checked before any quantity is changed. A
    shortage raises ValidationError so the reviewing view can roll back the
    approval and leave the request pending instead of silently consuming only
    part of the requested amount.
    """
    if instance.status != StockUsage.STATUS_APPROVED:
        # Notify admins about new pending requests.
        if created and instance.status == StockUsage.STATUS_PENDING:
            try:
                admins = User.objects.filter(models_q_is_admin())
                notification = NotificationLog.objects.create(
                    notification_type='stock_usage',
                    title='New stock usage request',
                    message=(
                        f'{instance.user.username} requested usage of '
                        f'{instance.quantity_used} x {instance.kit_type_name}.'
                    ),
                )
                notification.sent_to.set(admins)
            except Exception:  # pragma: no cover - notifications must never break saves
                logger.exception('Failed to create stock usage notification')
        return

    kit = instance.kit
    # LOGIC FIX: If kit is None (e.g. usage logged before fix), try to resolve via user+kit_type
    if kit is None and instance.kit_type_id:
        try:
            # Find best candidate: user's kit of that type with most stock
            kit = Kit.objects.filter(
                user=instance.user,
                kit_type_fk=instance.kit_type,
                is_active=True
            ).order_by('-quantity', '-timestamp').first()
            if kit:
                # Link it for audit trail (save without triggering signal again)
                StockUsage.objects.filter(pk=instance.pk).update(kit=kit)
                instance.kit = kit
                logger.info('Stock usage #%s auto-linked to kit #%s (fallback resolution)', instance.id, kit.id)
            else:
                logger.warning('Stock usage #%s approved but no matching kit found for user %s and kit_type %s', instance.id, instance.user_id, instance.kit_type_id)
        except Exception:
            logger.exception('Failed to auto-link kit for usage #%s', instance.id)
            kit = None

    try:
        if kit is not None:
            # Refresh to get latest quantity (avoid stale data)
            try:
                kit.refresh_from_db()
            except Exception:
                pass
            if instance.quantity_used >= kit.quantity:
                # Full depletion -> delete the kit entirely.
                kit_id = kit.id
                kit.delete()
                logger.info(
                    'Stock usage #%s deleted kit #%s (all stock used)', instance.id, kit_id
                )
            else:
                kit.quantity -= take
                kit.save(update_fields=['quantity', 'last_updated'])
                logger.info(
                    'Stock usage #%s reduced kit #%s to %s',
                    instance.id, kit.id, kit.quantity,
                )
        else:
            logger.warning('Stock usage #%s has no kit to deduct from; marking as completed without stock change', instance.id)
    except Exception:
        logger.exception('Failed to process stock deletion for usage #%s', instance.id)
        return


def _notify_low_stock(workspace_id, kit_type_ids):
    """Alert workspace managers when an approval leaves stock at/below its
    reorder level.

    Runs after the deduction so the notified quantities are the real ones.
    Never raises — notifications must not roll back an approval.
    """
    if not workspace_id or not kit_type_ids:
        return
    try:
        low = []
        kit_types = KitType.objects.filter(
            id__in=kit_type_ids, reorder_level__isnull=False, is_active=True,
        )
        for kit_type in kit_types:
            total = (
                Kit.objects.filter(
                    kit_type_fk=kit_type,
                    workspace_id=workspace_id,
                    is_active=True,
                ).aggregate(total=Sum('quantity'))['total']
                or 0
            )
            if total <= kit_type.reorder_level:
                low.append((kit_type.name, total, kit_type.reorder_level))
        if not low:
            return
        lines = ', '.join(
            f'{name} ({total}/{level} left)' for name, total, level in low
        )
        managers = User.objects.filter(
            Q(is_superuser=True)
            | Q(role__in=[User.ROLE_ADMIN, User.ROLE_MANAGER])
            | Q(
                workspace_memberships__workspace_id=workspace_id,
                workspace_memberships__role__in=[
                    WorkspaceMember.ROLE_OWNER, WorkspaceMember.ROLE_ADMIN,
                ],
            )
        ).distinct()
        notification = NotificationLog.objects.create(
            notification_type='low_stock',
            title='Stock running low',
            message=f'Reorder threshold reached for: {lines}.',
        )
        notification.sent_to.set(managers)
    except Exception:  # pragma: no cover - alerts must never break approvals
        logger.exception('Failed to send low-stock notification')


@receiver(pre_delete, sender=Kit)
def log_kit_deletion(sender, instance, **kwargs):
    """Maintain the audit trail when a kit is deleted.

    Runs before the collector nulls related StockUsage foreign keys, so the
    related usage records can still be found and flagged.
    """
    related = StockUsage.objects.filter(kit_id=instance.id)
    count = related.count()
    if count:
        related.update(stock_deleted=True)
    logger.info('Kit #%s deleted (%s related usage record(s) flagged)', instance.id, count)


@receiver(post_delete, sender=Kit)
def _log_kit_deletion_post(sender, instance, **kwargs):  # noqa: D103
    logger.info('Kit #%s removed from database', instance.id)


def models_q_is_admin():
    """Return a Q filter matching admin users (superuser or admin role)."""
    from django.db.models import Q
    return Q(is_superuser=True) | Q(role=User.ROLE_ADMIN)
