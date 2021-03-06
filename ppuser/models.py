from django.db import models
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from shortuuid import uuid
from datetime import datetime


class CustomUserManager(BaseUserManager):
    def _create_user(self, username, password, is_staff, is_superuser, **extra_fields):
        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')

        user = self.model(username=username, is_staff=is_staff, is_active=True, is_superuser=is_superuser, last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, False, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        return self._create_user(username, password, True, True, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(_('username'), max_length=254, unique=True)
    display_name = models.CharField(_('display_name'), max_length=254, null=True, blank=True)
    email = models.EmailField(_('email address'), max_length=254)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    avatar = models.URLField(_('avatar url'), max_length=255, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False, help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True, help_text=_('Designates whether this user should be treated as '
                                                                           'active. Unselect this instead of deleting accounts.'))
    is_verified = models.BooleanField(_('verified'), default=False, help_text=_('Designates whether the user has been verified via an email confirmation.'))
    verify_token = models.CharField(max_length=22, null=True, blank=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    set_profile = models.BooleanField(_('set_profile'), default=False, help_text=('Has the user set up his profile.'))
    verified_on = models.DateTimeField(_('verified on'), blank=True, null=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        if not self.verify_token:
            self.verify_token = uuid()

        if self.verify_token and not self.verified_on:
            self.verified_on = datetime.now()

        return super(CustomUser, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.username)

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])


# This is where the signal stuff belongs, I guess.
from rq import Queue
from redis import Redis
from worker import conn
from mailframework.mails import send_verify_email, send_welcome_email
from django.db.models.signals import post_save
from django.dispatch import receiver

redis_conn = Redis()
# try: 
    # q = Queue(connection=redis_conn)  # no args implies the default queue
# except Exception:
    # q = Queue(connection=conn)
q = Queue(connection=conn)

@receiver(post_save, sender=CustomUser)
def handle(sender, instance, created, **kwargs):
    if created and instance.email and not instance.is_verified:
        job = q.enqueue(send_welcome_email, instance.email)
        # job = q.enqueue("Hi World")

    if instance.email and not instance.is_verified:
        job = q.enqueue(send_verify_email, instance.email, instance.verify_token)
        # job = q.enqueue("Hi", "World")
