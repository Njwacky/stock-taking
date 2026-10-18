"""
Signal receivers for the stockT application.

- handle_stock_usage_approval: automatically reduces/deletes stock when a
  StockUsage request is approved.
- log_kit_deletion: keeps the audit trail consistent when a Kit is deleted.
"""
import logging

from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import Kit, NotificationLog, StockUsage, User

logger = logging.getLogger('stockT')


@receiver(post_save, sender=StockUsage)
def handle_stock_usage_approval(sender, instance, created, **kwargs):
    """Process approved stock usage requests.

    When a StockUsage is saved with status='approved':
      - the referenced kit's quantity is reduced by quantity_used
      - the kit is deleted entirely when all of its stock is used
      - the usage is marked as 'completed' with stock_deleted=True
    """
    if instance.status != StockUsage.STATUS_APPROVED:
        # Notify admins about new pending requests.
        if created and instance.status == StockUsage.STATUS_PENDING:
            try:
                admins = User.objects.filter(
                    models_q_is_admin()
                )
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
    try:
        if kit is not None:
            if instance.quantity_used >= kit.quantity:
                # Full depletion -> delete the kit entirely.
                kit_id = kit.id
                kit.delete()
                logger.info(
                    'Stock usage #%s deleted kit #%s (all stock used)', instance.id, kit_id
                )
            else:
                kit.quantity -= instance.quantity_used
                kit.save(update_fields=['quantity', 'last_updated'])
                logger.info(
                    'Stock usage #%s reduced kit #%s to %s',
                    instance.id, kit.id, kit.quantity,
                )
    except Exception:
        logger.exception('Failed to process stock deletion for usage #%s', instance.id)
        return

    # Update the usage record without re-triggering this signal.
    StockUsage.objects.filter(pk=instance.pk).update(
        status=StockUsage.STATUS_COMPLETED,
        stock_deleted=True,
        reviewed_at=instance.reviewed_at or timezone.now(),
    )
    instance.status = StockUsage.STATUS_COMPLETED
    instance.stock_deleted = True


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
