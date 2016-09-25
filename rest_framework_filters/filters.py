from __future__ import absolute_import
from __future__ import unicode_literals

from django.utils import six

from django_filters.rest_framework.filters import *


ALL_LOOKUPS = '__all__'


def _import_class(path):
    module_path, class_name = path.rsplit('.', 1)
    class_name = str(class_name)  # Ensure not unicode on py2.x
    module = __import__(module_path, fromlist=[class_name], level=0)
    return getattr(module, class_name)


class RelatedFilter(ModelChoiceFilter):
    def __init__(self, filterset, lookups=None, *args, **kwargs):
        self.filterset = filterset
        self.lookups = lookups
        return super(RelatedFilter, self).__init__(*args, **kwargs)

    def filterset():
        def fget(self):
            if isinstance(self._filterset, six.string_types):
                self._filterset = _import_class(self._filterset)
            return self._filterset

        def fset(self, value):
            self._filterset = value

        return locals()
    filterset = property(**filterset())

    @property
    def field(self):
        # if no queryset is provided, default to the filterset's default queryset
        self.extra.setdefault('queryset', self.filterset._meta.model._default_manager.all())
        return super(RelatedFilter, self).field


class AllLookupsFilter(Filter):
    lookups = ALL_LOOKUPS
