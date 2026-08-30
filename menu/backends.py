from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Profile
from .forms import normalize_phone, format_canonical_phone


class PhoneOrUsernameBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('username') or kwargs.get('phone')
        if not username or not password:
            return None

        phone_digits = normalize_phone(username)
        if phone_digits:
            canonical_phone = format_canonical_phone(phone_digits)
            profile = Profile.objects.filter(phone=canonical_phone).select_related('user').first()
            if profile and profile.user.check_password(password) and self.user_can_authenticate(profile.user):
                return profile.user

        try:
            user = User.objects.get(username__iexact=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None

        return None
