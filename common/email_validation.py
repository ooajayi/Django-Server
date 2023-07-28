import re

from django.utils.translation import gettext


def validate_email(email):    
    if email is None:
        return gettext("Email is required.")
    elif not re.match(r"^\w+([-+.']\w+)*@\w+([-.]\w+)*\.\w+([-.]\w+)*$", email):
        return gettext("Invalid Email Address.")
    # elif email.split('@')[-1] in disposable_emails:
    #    return "Disposable emails are not allowed."
    else:
        return None
