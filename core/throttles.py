from rest_framework.throttling import AnonRateThrottle


class PublicFormRateThrottle(AnonRateThrottle):
    scope = 'public_forms'


class DonationInitiationRateThrottle(AnonRateThrottle):
    scope = 'donation_initiation'


class PaymentCallbackRateThrottle(AnonRateThrottle):
    scope = 'payment_callbacks'
