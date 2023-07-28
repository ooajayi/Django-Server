import string, random
from django.utils.text import slugify


def random_string_generator(size = 10,
                            chars=string.ascii_lowercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))

def unique_slug_generator(instance, val, new_slug=None):
	if new_slug is not None:
		slug = new_slug
	else:
		slug = slugify(val)
	Klass = instance.__class__
	max_length = Klass._meta.get_field('slug').max_length
	slug = slug[:max_length]
	qs_exists = Klass.objects.filter(slug=slug).exists()
	
	if qs_exists:
		new_slug = "{slug}-{randstr}".format(
			slug = slug[:max_length-5],
            randstr = random_string_generator(size = 4)
        )

		return unique_slug_generator(instance, new_slug = new_slug)
	return slug


def get_user_primary_email(user):
	email = user.email

	for emailaddress in user.emailaddress_set.all():
		if emailaddress.primary and emailaddress.verified:
			email = emailaddress
			break
		elif emailaddress.verified:
			email = emailaddress
			break

	return email


def get_obj_loc_str(obj):
	loc_str = ""

	if not obj:
		return loc_str

	if obj.address:
		loc_str = obj.address

	if obj.city:
		loc_str = f"{loc_str} {obj.city},"

	if obj.province:
		loc_str = f"{loc_str} {obj.province}"

	if obj.country:
		loc_str = f"{loc_str} {obj.country}"

	if obj.postal_code:
		loc_str = f"{loc_str}\n{obj.postal_code}"

	return loc_str
