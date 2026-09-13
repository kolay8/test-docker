from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Profile
from .forms import format_canonical_phone


class PhoneOrUsernameBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        username = username or kwargs.get('username') or kwargs.get('phone')
        if not username or not password:
            return None

        user = None
        canonical_phone = format_canonical_phone(username)
        if canonical_phone:
            profile = Profile.objects.filter(phone=canonical_phone).select_related('user').first()
            if profile:
                user = profile.user

        if user is None:
            user = User.objects.filter(username__iexact=username).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
