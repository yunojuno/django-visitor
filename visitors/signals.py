from django.dispatch import Signal

# sent when a user creates their own Visitor - can
# be used to send the email with the token
# kwargs: visitor
self_service_visitor_created = Signal()
