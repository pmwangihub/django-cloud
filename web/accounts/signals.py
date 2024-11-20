from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save
from app.utils import unique_key_generator
from accounts.models import EmailActivation

User = get_user_model()


@receiver(pre_save, sender=EmailActivation)
def pre_save_email_activation(sender, instance, *args, **kwargs):
    """
    Signal handler that generates a unique key for an EmailActivation object before saving.
    """
    if not instance.activated and not instance.forced_expired:
        if not instance.key:
            instance.key = unique_key_generator(instance)


@receiver(post_save, sender=User)
def post_save_user_create_receiver(sender, instance, created, *args, **kwargs):
    """
    Signal handler that creates an EmailActivation object for a newly created User.
    """
    pass
    # if created:
    #     obj = EmailActivation.objects.create(user=instance, email=instance.email)
    #     try:
    #         obj.send_activation()
    #     except Exception as e:
    #         print(e)
    #         pass
