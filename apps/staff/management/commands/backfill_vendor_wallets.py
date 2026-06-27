"""
One-time backfill: credit vendor wallets for orders that were verified
BEFORE the wallet-crediting fix was deployed.

Safe to run multiple times — only touches OrderItems where vendor_paid=False,
and marks them vendor_paid=True as it credits them, so nothing is ever
double-counted (whether this command runs again, or approve_receipt_view
runs for a new order).

Usage:
    python manage.py backfill_vendor_wallets            # actually applies changes
    python manage.py backfill_vendor_wallets --dry-run   # preview only, no changes
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from apps.orders.models import Order, OrderItem
from apps.vendors.models import Vendor


class Command(BaseCommand):
    help = 'Backfill vendor wallet_balance for already-verified orders that were never credited.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be credited without making any changes.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Only orders whose payment is verified, restricted to items not yet paid out
        uncredited_items = OrderItem.objects.filter(
            order__payment_status=Order.PAYMENT_STATUS_VERIFIED,
            vendor_paid=False
        )

        if not uncredited_items.exists():
            self.stdout.write(self.style.SUCCESS('Nothing to backfill — all verified orders are already credited.'))
            return

        vendor_totals = uncredited_items.values('vendor').annotate(total=Sum('vendor_amount'))

        self.stdout.write(f"Found {uncredited_items.count()} uncredited order item(s) across {len(vendor_totals)} vendor(s).\n")

        grand_total = 0
        with transaction.atomic():
            for row in vendor_totals:
                vendor = Vendor.objects.get(pk=row['vendor'])
                amount = row['total']
                grand_total += amount

                self.stdout.write(
                    f"  Vendor: {vendor.business_name:<30} "
                    f"Current: ₦{vendor.wallet_balance:>12,.2f}  "
                    f"+Credit: ₦{amount:>12,.2f}  "
                    f"New: ₦{(vendor.wallet_balance + amount):>12,.2f}"
                )

                if not dry_run:
                    vendor.wallet_balance += amount
                    vendor.save(update_fields=['wallet_balance'])

            if not dry_run:
                uncredited_items.update(vendor_paid=True)
            else:
                # Roll back — dry run should never persist anything
                transaction.set_rollback(True)

        self.stdout.write()
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'DRY RUN — no changes made. Would have credited a total of ₦{grand_total:,.2f}.'
            ))
            self.stdout.write(self.style.WARNING('Run again without --dry-run to apply.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Done. Credited a total of ₦{grand_total:,.2f} across {len(vendor_totals)} vendor(s).'
            ))
