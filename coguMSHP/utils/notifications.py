import os

from twilio.rest import Client

from cogu.models import WhatsAppMessage


def send_whatsapp_message(to_number, message_body):
    client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
    from_number = "whatsapp:+14237194194"  # Numéro Twilio Sandbox

    message = client.messages.create(
        from_=from_number,
        body=message_body,
        to=f"whatsapp:{to_number}"
    )

    # Sauvegarder le message
    WhatsAppMessage.objects.create(
        direction="out",
        sender=from_number,
        recipient=to_number,
        body=message_body
    )

    return message.sid