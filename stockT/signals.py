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

    if instance.stock_deleted:
        raise ValidationError(
            'This usage cannot be approved because its linked stock was already removed or processed.'
        )
    if instance.quantity_used < 1:
        raise ValidationError('Usage quantity must be at least 1.')

    # The review view wraps the status change and this signal in one outer
    # transaction. Keep the stock changes and completion write grouped here as
    # well; callers that approve usages directly must also use a transaction.
    with transaction.atomic():
        if instance.kit_id:
            kits = list(
                Kit.objects.select_for_update().filter(pk=instance.kit_id)
            )
            if not kits:
                raise ValidationError('The selected stock item no longer exists.')
            kit = kits[0]
            if (
                kit.user_id != instance.user_id
                or (instance.kit_type_id and kit.kit_type_fk_id != instance.kit_type_id)
                or kit.workspace_id != instance.workspace_id
                or not kit.is_active
            ):
                raise ValidationError(
                    'The selected stock item does not match this usage request.'
                )
        elif instance.kit_type_id:
            # The tracking form selects a type, not a particular kit. Apply
            # usage FIFO, but only to active stock owned by this user in the
            # same workspace as the request.
            kits = list(
                Kit.objects.select_for_update().filter(
                    user_id=instance.user_id,
                    kit_type_fk_id=instance.kit_type_id,
                    workspace_id=instance.workspace_id,
                    is_active=True,
                    quantity__gt=0,
                ).order_by('timestamp', 'pk')
            )
        else:
            kits = []

        available = sum(kit.quantity for kit in kits)
        if available < instance.quantity_used:
            raise ValidationError(
                f'Not enough stock to approve this request: '
                f'{available} available, {instance.quantity_used} requested.'
            )

        touched_kit_types = {
            kit.kit_type_fk_id for kit in kits if kit.kit_type_fk_id
        }
        remaining = instance.quantity_used
        for kit in kits:
            if remaining <= 0:
                break
            take = min(kit.quantity, remaining)
            if take == kit.quantity:
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
            remaining -= take

        # Update without re-triggering this signal. Since stock and usage are
        # in the same transaction, a failure rolls both changes back.
        StockUsage.objects.filter(pk=instance.pk).update(
            status=StockUsage.STATUS_COMPLETED,
            stock_deleted=True,
            reviewed_at=instance.reviewed_at or timezone.now(),
        )
        instance.status = StockUsage.STATUS_COMPLETED
        instance.stock_deleted = True

    _notify_low_stock(instance.workspace_id, touched_kit_types)


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
