from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail

from common.func_utils import unique_slug_generator

from .models.common import Genre
from .models.util import Contact
from .models.user import User, UserProfile, Studio

recipient_list = settings.NOTIFS_RECIPIENT_LIST

"""
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            full_name=instance.first_name + ' ' + instance.last_name,
            active=True
        )
    else:
        try:
            UserProfile.objects.get(user=instance).save()
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(
                user=instance,
                active=True,
                full_name=instance.first_name + ' ' + instance.last_name
            )
"""


@receiver(post_save, sender=UserProfile)
def create_studio_obj(sender, instance, created, **kwargs):
    if created and instance.type == "studio":
        # create a studio and send email to admin to verify studio??
        obj, created = Studio.objects.get_or_create(
            profile=instance,
            defaults={
                "name": instance.display_name,
                "phone": instance.phone,
                "email": instance.user.email,
                "bio": instance.bio,
                "address": instance.address,
                "city": instance.city,
                "province": instance.province,
                "country": instance.country,
                "postal_code": instance.postal_code,
                "facebook": instance.facebook,
                "twitter": instance.twitter,
                "instagram": instance.instagram
            }
        )
        obj.genres.set(instance.genres.all())

        subject = 'DCC - A new Studio has been created'
        message = 'A new Studio has been created, \
                  created by %s and email is' %(instance.user.full_name, 
                                                instance.user.email)
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email,
                  recipient_list=recipient_list,
                  fail_silently=True)
    if not created:
        print("Profile saved!")


@receiver(pre_save, sender=Genre)
def pre_save_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = unique_slug_generator(instance, instance.name)
    else:
        instance.slug = unique_slug_generator(instance, instance.slug)


@receiver(post_save, sender=Contact)
def contact_form_submission(sender, instance, created, **kwargs):
    if created:
        subject = 'DCC - Contact Form Submission'
        message = 'A new Contact Form submission was received'
        from_email = settings.DEFAULT_FROM_EMAIL
        send_mail(subject, message, from_email,
                  recipient_list=recipient_list,
                  fail_silently=True)
