"""Payment gateway adapter layer for initiation, verification, and reconciliation."""

from __future__ import annotations

from abc import ABC, abstractmethod

import stripe
from django.conf import settings

from .mpesa import MPesaClient, process_mpesa_callback


class PaymentGatewayAdapter(ABC):
    """Minimal contract for payment adapters."""

    @abstractmethod
    def initiate(self, payload: dict) -> dict:
        """Initiate payment and return provider response payload."""

    def verify_callback(self, payload, signature: str = '') -> dict:
        """Return verified callback payload (or raise if invalid)."""
        return payload


class MPesaGatewayAdapter(PaymentGatewayAdapter):
    """Adapter for M-Pesa STK push and callback parsing."""

    def __init__(self):
        self.client = MPesaClient()

    def initiate(self, payload: dict) -> dict:
        return self.client.stk_push(
            phone_number=payload['phone_number'],
            amount=payload['amount'],
            account_reference=payload['account_reference'],
            transaction_desc=payload.get('transaction_desc', 'Donation'),
        )

    def verify_callback(self, payload, signature: str = '') -> dict:
        # M-Pesa has no provider-native signature verification in current integration.
        return process_mpesa_callback(payload)


class StripeGatewayAdapter(PaymentGatewayAdapter):
    """Adapter for Stripe PaymentIntent and webhook verification."""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def initiate(self, payload: dict) -> dict:
        payment_intent = stripe.PaymentIntent.create(
            amount=payload['amount'],
            currency=payload['currency'],
            description=payload.get('description', 'Donation'),
            receipt_email=payload.get('receipt_email', ''),
            metadata=payload.get('metadata', {}),
            automatic_payment_methods={'enabled': True},
        )
        return {
            'id': payment_intent.id,
            'client_secret': payment_intent.client_secret,
            'status': payment_intent.status,
        }

    def verify_callback(self, payload, signature: str = '') -> dict:
        return stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
