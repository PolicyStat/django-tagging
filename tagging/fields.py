"""
A custom Model Field for tagging.
"""
from django.conf import settings
from django.db.models import signals
from django.db.models.fields import CharField
from django.utils.translation import gettext_lazy as _

from tagging.settings import DEFAULT_FORCE_LOWERCASE_TAGS
from tagging.models import Tag
from tagging.utils import edit_string_for_tags

class TagField(CharField):
    """
    A "special" character field that actually works as a relationship to tags
    "under the hood". This exposes a space-separated string of tags, but does
    the splitting/reordering/etc. under the hood.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 255)
        kwargs['blank'] = kwargs.get('blank', True)
        kwargs['default'] = kwargs.get('default', '')
        super(TagField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(TagField, self).contribute_to_class(cls, name)

        # Make this object the descriptor for field access.
        setattr(cls, self.name, self)

        # Save tags back to the database post-save
        signals.post_save.connect(self._save, cls, True)

        # Update tags from Tag objects post-init
        signals.post_init.connect(self._update, cls, True)

    def __get__(self, instance, owner=None):
        """
        Tag getter. Returns an instance's tags if accessed on an instance, and
        all of a model's tags if called on a class. That is, this model::

           class Link(models.Model):
               ...
               tags = TagField()

        Lets you do both of these::

           >>> l = Link.objects.get(...)
           >>> l.tags
           'tag1 tag2 tag3'

           >>> Link.tags
           'tag1 tag2 tag3 tag4'

        """
        # Handle access on the model (i.e. Link.tags)
        if instance is None:
            return edit_string_for_tags(Tag.objects.usage_for_model(owner))

        return self._get_instance_tag_cache(instance)

    def __set__(self, instance, value):
        """
        Set an object's tags.
        """
        if instance is None:
            raise AttributeError(_('%s can only be set on instances.') % self.name)
        if getattr(settings, 'FORCE_LOWERCASE_TAGS', DEFAULT_FORCE_LOWERCASE_TAGS) and value is not None:
            value = value.lower()
        self._set_instance_tag_cache(instance, value)

    def _save(self, **kwargs): #signal, sender, instance):
        """
        Save tags back to the database
        """
        tags = self._get_instance_tag_cache(kwargs['instance'])
        Tag.objects.update_tags(kwargs['instance'], tags)

    def _update(self, **kwargs): #signal, sender, instance):
        """
        Update tag cache from TaggedItem objects.
        """
        instance = kwargs['instance']
        self._update_instance_tag_cache(instance)

    def __delete__(self, instance):
        """
        Clear all of an object's tags.
        """
        self._set_instance_tag_cache(instance, '')

    def _get_instance_tag_cache(self, instance):
        """
        Helper: get an instance's tag cache.
        """
        return getattr(instance, '_%s_cache' % self.attname, None)

    def _set_instance_tag_cache(self, instance, tags):
        """
        Helper: set an instance's tag cache.
        """
        setattr(instance, '_%s_cache' % self.attname, tags)

    def _update_instance_tag_cache(self, instance):
        """
        Helper: update an instance's tag cache from actual Tags.
        """
        # for an unsaved object, leave the default value alone
        if instance.pk is not None:
            tags = edit_string_for_tags(Tag.objects.get_for_object(instance))
            self._set_instance_tag_cache(instance, tags)

    def get_internal_type(self):
        return 'CharField'

    def formfield(self, **kwargs):
        from tagging import forms
        defaults = {'form_class': forms.TagField}
        defaults.update(kwargs)
        return super(TagField, self).formfield(**defaults)
