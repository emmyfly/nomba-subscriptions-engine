import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payment import Payment
from app.models.tenant import Tenant
from app.models.payout_log import PayoutLog
from app.services.nomba import transfer_to_bank

logger = logging.getLogger("subflow.payout")


def process_instant_payout(payment: Payment, tenant: Tenant, db: Session) -> PayoutLog:
    platform_fee = round(payment.amount * (settings.PLATFORM_FEE_PERCENT / 100), 2)
    net_amount = round(payment.amount - platform_fee, 2)

    if not tenant.bank_account_number or not tenant.bank_code:
        log = PayoutLog(
            tenant_id=tenant.id,
            payment_id=payment.id,
            gross_amount=payment.amount,
            platform_fee=platform_fee,
            net_amount=net_amount,
            status="skipped_no_bank_details",
        )
        db.add(log)
        payment.payout_status = "skipped_no_bank_details"
        logger.warning(
            "Payout skipped for payment %s: tenant %s has no bank details on file",
            payment.id, tenant.id,
        )
        return log

    if tenant.bank_verification_status == "name_mismatch":
        log = PayoutLog(
            tenant_id=tenant.id,
            payment_id=payment.id,
            gross_amount=payment.amount,
            platform_fee=platform_fee,
            net_amount=net_amount,
            status="skipped_name_mismatch",
            error_detail="Bank account name does not match tenant's claimed name -- held for manual review",
        )
        db.add(log)
        payment.payout_status = "skipped_name_mismatch"
        logger.warning(
            "Payout held for payment %s: tenant %s bank account name mismatch",
            payment.id, tenant.id,
        )
        return log

    merchant_tx_ref = f"payout_{payment.id}"

    try:
        result = transfer_to_bank(
            subaccount_id=tenant.nomba_subaccount_id,
            amount=net_amount,
            account_number=tenant.bank_account_number,
            account_name=tenant.bank_account_name or tenant.name,
            bank_code=tenant.bank_code,
            merchant_tx_ref=merchant_tx_ref,
        )
        log = PayoutLog(
            tenant_id=tenant.id,
            payment_id=payment.id,
            gross_amount=payment.amount,
            platform_fee=platform_fee,
            net_amount=net_amount,
            status="completed",
            nomba_transfer_ref=merchant_tx_ref,
        )
        payment.payout_status = "paid_out"
        logger.info(
            "Payout completed for payment %s: tenant %s net %.2f (ref %s)",
            payment.id, tenant.id, net_amount, merchant_tx_ref,
        )
    except Exception as e:
        log = PayoutLog(
            tenant_id=tenant.id,
            payment_id=payment.id,
            gross_amount=payment.amount,
            platform_fee=platform_fee,
            net_amount=net_amount,
            status="failed",
            nomba_transfer_ref=merchant_tx_ref,
            error_detail=str(e)[:500],
        )
        payment.payout_status = "failed"
        logger.error(
            "Payout failed for payment %s: tenant %s - %s",
            payment.id, tenant.id, e,
        )

    db.add(log)
    return log
