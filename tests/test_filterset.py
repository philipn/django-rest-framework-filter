import sys

from django.http.request import QueryDict
from django.test import TestCase
from django_filters.filters import BaseInFilter
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from rest_framework_filters import FilterSet, filters
from rest_framework_filters.filterset import FilterSetMetaclass

from .testapp.filters import (
    BlogPostFilter, BlogPostOverrideFilter, NoteFilterWithAll,
    NoteFilterWithRelated, PostFilter, TagFilter, UserFilter,
)
from .testapp.models import BlogPost, Note, Person, Post, Tag

factory = APIRequestFactory()


class limit_recursion:
    def __init__(self):
        self.original_limit = sys.getrecursionlimit()

    def __enter__(self):
        sys.setrecursionlimit(100)

    def __exit__(self, *args):
        sys.setrecursionlimit(self.original_limit)


class MetaclassTests(TestCase):

    def test_metamethods(self):
        functions = [
            'expand_auto_filters',
            'get_auto_filters',
            'get_related_filters',
        ]

        for func in functions:
            with self.subTest(func=func):
                self.assertTrue(hasattr(UserFilter, func))
                self.assertFalse(hasattr(UserFilter(), func))


class AutoFilterTests(TestCase):
    """
    Test auto filter generation (`AllLookupsFilter`, `RelatedFilter`, '__all__').
    """

    def test_alllookupsfilter_meta_fields_unmodified(self):
        f = []

        class F(FilterSet):
            id = filters.AllLookupsFilter()

            class Meta:
                model = Note
                fields = f

        self.assertIs(F._meta.fields, f)

    def test_alllookupsfilter_replaced(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/118
        class F(FilterSet):
            id = filters.AllLookupsFilter()

            class Meta:
                model = Note
                fields = []

        self.assertIsInstance(F.declared_filters['id'], filters.AllLookupsFilter)
        self.assertIsInstance(F.base_filters['id'], filters.NumberFilter)

    def test_alllookupsfilter_for_relation(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/84
        class F(FilterSet):
            class Meta:
                model = Note
                fields = {
                    'author': '__all__',
                }

        self.assertIsInstance(F.base_filters['author'], filters.ModelChoiceFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_alllookupsfilter_for_related_field(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/127
        class F(FilterSet):
            author = filters.AllLookupsFilter(field_name='author__last_name')

            class Meta:
                model = Note
                fields = []

        self.assertIsInstance(F.base_filters['author'], filters.CharFilter)
        self.assertEqual(F.base_filters['author'].field_name, 'author__last_name')

    def test_relatedfilter_combined_with__all__(self):
        # ensure that related filter is compatible with __all__ lookups.
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter)

            class Meta:
                model = Note
                fields = {
                    'author': '__all__',
                }

        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_relatedfilter_lookups(self):
        # ensure that related filter is compatible with __all__ lookups.
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter, lookups='__all__')

            class Meta:
                model = Note
                fields = []

        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_relatedfilter_lookups_default(self):
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter)

            class Meta:
                model = Note
                fields = []

        self.assertEqual(len([f for f in F.base_filters if f.startswith('author')]), 1)
        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)

    def test_relatedfilter_lookups_list(self):
        class F(FilterSet):
            author = filters.RelatedFilter(UserFilter, lookups=['in'])

            class Meta:
                model = Note
                fields = []

        self.assertEqual(len([f for f in F.base_filters if f.startswith('author')]), 2)
        self.assertIsInstance(F.base_filters['author'], filters.RelatedFilter)
        self.assertIsInstance(F.base_filters['author__in'], BaseInFilter)

    def test_declared_filter_persistence_with__all__(self):
        # ensure that __all__ does not overwrite declared filters.
        f = filters.Filter()

        class F(FilterSet):
            name = f

            class Meta:
                model = Person
                fields = {'name': '__all__'}

        self.assertIs(F.base_filters['name'], f)

    def test_declared_filter_persistence_with_alllookupsfilter(self):
        # ensure that AllLookupsFilter does not overwrite declared filters.
        f = filters.Filter()

        class F(FilterSet):
            id = filters.AllLookupsFilter()
            id__in = f

            class Meta:
                model = Note
                fields = []

        self.assertIs(F.base_filters['id__in'], f)


class GetParamFilterNameTests(TestCase):

    def test_regular_filter(self):
        name = UserFilter.get_param_filter_name('email')
        self.assertEqual('email', name)

    def test_exclusion_filter(self):
        name = UserFilter.get_param_filter_name('email!')
        self.assertEqual('email', name)

    def test_non_filter(self):
        name = UserFilter.get_param_filter_name('foobar')
        self.assertEqual(None, name)

    def test_related_filter(self):
        # 'exact' matches
        name = NoteFilterWithRelated.get_param_filter_name('author')
        self.assertEqual('author', name)

        # related attribute filters
        name = NoteFilterWithRelated.get_param_filter_name('author__email')
        self.assertEqual('author', name)

        # non-existent related filters should match, as it's the responsibility
        # of the related filterset to handle non-existent filters
        name = NoteFilterWithRelated.get_param_filter_name('author__foobar')
        self.assertEqual('author', name)

    def test_twice_removed_related_filter(self):
        class PostFilterWithDirectAuthor(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilterWithAll)

            class Meta:
                model = Post
                fields = []

        name = PostFilterWithDirectAuthor.get_param_filter_name('note__title')
        self.assertEqual('note', name)

        # 'exact' matches, preference more specific filter name, as less specific
        # filter may not have related access.
        name = PostFilterWithDirectAuthor.get_param_filter_name('note__author')
        self.assertEqual('note__author', name)

        # related attribute filters
        name = PostFilterWithDirectAuthor.get_param_filter_name('note__author__email')
        self.assertEqual('note__author', name)

        # non-existent related filters should match, as it's the responsibility
        # of the related filterset to handle non-existent filters
        name = PostFilterWithDirectAuthor.get_param_filter_name('note__author__foobar')
        self.assertEqual('note__author', name)

    def test_name_hiding(self):
        class PostFilterNameHiding(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilterWithAll)
            note2 = filters.RelatedFilter(NoteFilterWithAll)

            class Meta:
                model = Post
                fields = []

        name = PostFilterNameHiding.get_param_filter_name('note__author')
        self.assertEqual('note__author', name)

        name = PostFilterNameHiding.get_param_filter_name('note__title')
        self.assertEqual('note', name)

        name = PostFilterNameHiding.get_param_filter_name('note')
        self.assertEqual('note', name)

        name = PostFilterNameHiding.get_param_filter_name('note2')
        self.assertEqual('note2', name)

        name = PostFilterNameHiding.get_param_filter_name('note2__author')
        self.assertEqual('note2', name)


class GetRelatedDataTests(TestCase):

    def test_regular_filter(self):
        params = NoteFilterWithRelated.get_related_data({'title': ''})
        self.assertEqual(params, {})

    def test_related_filter_exact(self):
        params = NoteFilterWithRelated.get_related_data({'author': ''})
        self.assertEqual(params, {})

    def test_related_filters(self):
        params = NoteFilterWithRelated.get_related_data({'author__email': ''})
        self.assertEqual(params, {'author': {'email': ['']}})

    def test_multiple_related_filters(self):
        params = NoteFilterWithRelated.get_related_data({
            'author__username': '',
            'author__is_active': '',
            'author__email': '',
        })
        self.assertEqual(params, {'author': {
            'email': [''],
            'is_active': [''],
            'username': [''],
        }})

    def test_name_hiding(self):
        class PostFilterNameHiding(PostFilter):
            note__author = filters.RelatedFilter(UserFilter)
            note = filters.RelatedFilter(NoteFilterWithAll)
            note2 = filters.RelatedFilter(NoteFilterWithAll)

            class Meta:
                model = Post
                fields = []

        params = PostFilterNameHiding.get_related_data({'note__author__email': ''})
        self.assertEqual(params, {'note__author': {'email': ['']}})

        params = PostFilterNameHiding.get_related_data({'note__title': ''})
        self.assertEqual(params, {'note': {'title': ['']}})

        params = PostFilterNameHiding.get_related_data({'note2__title': ''})
        self.assertEqual(params, {'note2': {'title': ['']}})

        params = PostFilterNameHiding.get_related_data({'note2__author': ''})
        self.assertEqual(params, {'note2': {'author': ['']}})

        # combined
        params = PostFilterNameHiding.get_related_data({
            'note__author__email': '',
            'note__title': '',
            'note2__title': '',
            'note2__author': '',
        })

        self.assertEqual(params, {
            'note__author': {'email': ['']},
            'note': {'title': ['']},
            'note2': {
                'title': [''],
                'author': [''],
            },
        })

    def test_querydict(self):
        self.assertEqual(
            QueryDict('a=1&a=2&b=3'),
            {'a': ['1', '2'], 'b': ['3']}
        )

        result = {'note': {
            'author__email': ['a'],
            'title': ['b', 'c'],
        }}

        query = QueryDict('note__author__email=a&note__title=b&note__title=c')
        self.assertEqual(PostFilter.get_related_data(query), result)

        # QueryDict-like dictionary w/ multiple values for a param (a la m2m)
        query = {'note__author__email': 'a', 'note__title': ['b', 'c']}
        self.assertEqual(PostFilter.get_related_data(query), result)


class GetFilterSubsetTests(TestCase):

    def test_get_subset(self):
        filter_subset = UserFilter.get_filter_subset(['email'])

        # ensure that the FilterSet subset only contains the requested fields
        self.assertIn('email', filter_subset)
        self.assertEqual(len(filter_subset), 1)

    def test_related_subset(self):
        # related filters should only return the local RelatedFilter
        filter_subset = NoteFilterWithRelated.get_filter_subset(['title', 'author', 'author__email'])

        self.assertIn('title', filter_subset)
        self.assertIn('author', filter_subset)
        self.assertEqual(len(filter_subset), 2)

    def test_non_filter_subset(self):
        # non-filter params should be ignored
        filter_subset = NoteFilterWithRelated.get_filter_subset(['foobar'])
        self.assertEqual(len(filter_subset), 0)

    def test_metaclass_inheritance(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/132
        class SubMetaclass(FilterSetMetaclass):
            pass

        class SubFilterSet(FilterSet, metaclass=SubMetaclass):
            pass

        class NoteFilter(SubFilterSet):
            author = filters.RelatedFilter(UserFilter)

            class Meta:
                model = Note
                fields = ['title', 'content']

        filter_subset = NoteFilter.get_filter_subset(['author', 'content'])

        # ensure that the FilterSet subset only contains the requested fields
        self.assertIn('author', filter_subset)
        self.assertIn('content', filter_subset)
        self.assertEqual(len(filter_subset), 2)


class FilterOverrideTests(TestCase):

    def test_declared_filters(self):
        F = BlogPostOverrideFilter

        # explicitly declared filters SHOULD NOT be overridden
        self.assertIsInstance(
            F.base_filters['declared_publish_date__isnull'],
            filters.NumberFilter
        )

        # declared `AllLookupsFilter`s SHOULD generate filters that ARE overridden
        self.assertIsInstance(
            F.base_filters['all_declared_publish_date__isnull'],
            filters.BooleanFilter
        )

    def test_dict_declaration(self):
        F = BlogPostOverrideFilter

        # dictionary style declared filters SHOULD be overridden
        self.assertIsInstance(
            F.base_filters['publish_date__isnull'],
            filters.BooleanFilter
        )


class FilterExclusionTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        t1 = Tag.objects.create(name='Tag 1')
        t2 = Tag.objects.create(name='Tag 2')
        t3 = Tag.objects.create(name='Something else entirely')

        p1 = BlogPost.objects.create(title='Post 1', content='content 1')
        p2 = BlogPost.objects.create(title='Post 2', content='content 2')

        p1.tags.set([t1, t2])
        p2.tags.set([t3])

    def test_exclude_property(self):
        """
        Ensure that the filter is set to exclude
        """
        GET = {
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        requested_filters = filterset.request_filters

        self.assertTrue(requested_filters['name__contains!'].exclude)

    def test_filter_and_exclude(self):
        """
        Ensure that both the filter and exclusion filter are available
        """
        GET = {
            'name__contains': 'Tag',
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        requested_filters = filterset.request_filters

        self.assertFalse(requested_filters['name__contains'].exclude)
        self.assertTrue(requested_filters['name__contains!'].exclude)

    def test_related_exclude(self):
        GET = {
            'tags__name__contains!': 'Tag',
        }

        filterset = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        requested_filters = filterset.related_filtersets['tags'].request_filters

        self.assertTrue(requested_filters['name__contains!'].exclude)

    def test_exclusion_results(self):
        GET = {
            'name__contains!': 'Tag',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        results = [r.name for r in filterset.qs]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Something else entirely')

    def test_filter_and_exclusion_results(self):
        GET = {
            'name__contains': 'Tag',
            'name__contains!': '2',
        }

        filterset = TagFilter(GET, queryset=Tag.objects.all())
        results = [r.name for r in filterset.qs]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Tag 1')

    def test_related_exclusion_results(self):
        GET = {
            'tags__name__contains!': 'Tag',
        }

        filterset = BlogPostFilter(GET, queryset=BlogPost.objects.all())
        results = [r.title for r in filterset.qs]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Post 2')

    def test_exclude_and_request_interaction(self):
        # See: https://github.com/philipn/django-rest-framework-filters/issues/171
        request = APIView().initialize_request(factory.get('/?tags__name__contains!=Tag'))
        filterset = BlogPostFilter(request.query_params, request=request, queryset=BlogPost.objects.all())

        try:
            with limit_recursion():
                qs = filterset.qs
        except RuntimeError:
            self.fail('Recursion limit reached')

        results = [r.title for r in qs]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 'Post 2')
