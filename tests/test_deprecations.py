
import warnings
from django.test import TestCase

from rest_framework_filters import FilterSet
from rest_framework_filters import filters

from .testapp.models import User
from .testapp.filters import UserFilter


class FilterSetCacheDeprecationTests(TestCase):

    def test_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            cache = {}

            UserFilter({}, cache=cache)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

            self.assertIs(UserFilter._subset_cache, cache)


class FixFilterFieldDeprecationTests(TestCase):

    def test_override_notifcation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                @classmethod
                def fix_filter_field(cls, f):
                    return super(F, cls).fix_filter_field(f)

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_override_notifcation_without_invoking_base(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                @classmethod
                def fix_filter_field(cls, f):
                    return f

            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))

    def test_no_override_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                pass

            self.assertEqual(len(w), 0)


class OrderByDeprecationTests(TestCase):

    def test_override_notifcation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = User
                    order_by = 'username'
                    fields = []

            F().qs
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))


class AllLookupsDeprecationTests(TestCase):

    def test_ALL_LOOKUPS_notification(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = User
                    fields = {
                        'last_login': filters.ALL_LOOKUPS,
                    }

            self.assertEqual(len(w), 1)

    def test_no_notification_for__all__(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = User
                    fields = {
                        'last_login': '__all__',
                    }

            self.assertEqual(len(w), 0)

    def test_no_notification_for_fields_list(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                class Meta:
                    model = User
                    fields = ['last_login']

            self.assertEqual(len(w), 0)


class InLookupDeprecationTests(TestCase):

    def test_char_filter_deprecations(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                username__in = filters.InSetCharFilter(name='username', lookup_expr='in')

                class Meta:
                    model = User
                    fields = []

            self.assertEqual(len(w), 1)

            # Generate another warning for field
            F({'username__in': 'a'}).qs
            self.assertEqual(len(w), 2)

    def test_number_filter_deprecations(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            class F(FilterSet):
                id__in = filters.InSetNumberFilter(name='id', lookup_expr='in')

                class Meta:
                    model = User
                    fields = []

            self.assertEqual(len(w), 1)

            # Generate another warning for field
            F({'id__in': '1'}).qs
            self.assertEqual(len(w), 2)
