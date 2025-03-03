"""
Tagging components for Django's form library.
"""
from django import forms
from django.conf import settings
from django.utils.translation import gettext as _

from tagging.models import Tag
from tagging.settings import DEFAULT_MAX_TAG_LENGTH
from tagging.utils import parse_tag_input

class TagAdminForm(forms.ModelForm):
    class Meta:
        model = Tag
        exclude = []

    def clean_name(self):
        value = self.cleaned_data['name']
        tag_names = parse_tag_input(value)
        if len(tag_names) > 1:
            raise forms.ValidationError(_('Multiple tags were given.'))
        elif len(tag_names[0]) > getattr(settings, 'MAX_TAG_LENGTH', DEFAULT_MAX_TAG_LENGTH):
            raise forms.ValidationError(
                _('A tag may be no more than %s characters long.') %
                    getattr(settings, 'MAX_TAG_LENGTH', DEFAULT_MAX_TAG_LENGTH))
        return value

class TagField(forms.CharField):
    """
    A ``CharField`` which validates that its input is a valid list of
    tag names.
    """
    def clean(self, value):
        value = super(TagField, self).clean(value)
        if value == u'':
            return value
        for tag_name in parse_tag_input(value):
            if len(tag_name) > getattr(settings, 'MAX_TAG_LENGTH', DEFAULT_MAX_TAG_LENGTH):
                raise forms.ValidationError(
                    _('Each tag may be no more than %s characters long.') %
                        getattr(settings, 'MAX_TAG_LENGTH', DEFAULT_MAX_TAG_LENGTH))
        return value
