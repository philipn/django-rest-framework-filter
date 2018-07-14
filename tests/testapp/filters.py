
import django_filters

from rest_framework_filters import filters
from rest_framework_filters.filters import AutoFilter, RelatedFilter
from rest_framework_filters.filterset import LOOKUP_SEP, FilterSet

from .models import A, B, Blog, C, Cover, Note, Page, Person, Post, Tag, User


class DFUserFilter(django_filters.FilterSet):
    email = filters.CharFilter(field_name='email')

    class Meta:
        model = User
        fields = '__all__'


class UserFilter(FilterSet):
    username = AutoFilter(field_name='username', lookups='__all__')
    email = filters.CharFilter(field_name='email')
    last_login = AutoFilter(lookups='__all__')
    is_active = filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = User
        fields = []


class NoteFilter(FilterSet):
    title = AutoFilter(field_name='title', lookups='__all__')
    author = RelatedFilter(UserFilter, field_name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


class TagFilter(FilterSet):
    name = AutoFilter(field_name='name', lookups='__all__')

    class Meta:
        model = Tag
        fields = []


class BlogFilter(FilterSet):
    name = AutoFilter(field_name='name', lookups='__all__')
    post = RelatedFilter('PostFilter', field_name='post', queryset=Post.objects.all())

    class Meta:
        model = Blog
        fields = []


class PostFilter(FilterSet):
    # Used for Related filter and Filter.method regression tests
    title = filters.AutoFilter(field_name='title', lookups='__all__')

    publish_date = filters.AutoFilter(lookups='__all__')
    is_published = filters.BooleanFilter(field_name='publish_date', method='filter_is_published')

    note = RelatedFilter(NoteFilter, field_name='note', queryset=Note.objects.all())
    tags = RelatedFilter(TagFilter, field_name='tags', queryset=Tag.objects.all())

    class Meta:
        model = Post
        fields = []

    def filter_is_published(self, qs, name, value):
        """
        `is_published` is based on the actual `date_published`.
        If the publishing date is null, then the post is not published.
        """
        isnull = not value
        lookup_expr = LOOKUP_SEP.join([name, 'isnull'])

        return qs.filter(**{lookup_expr: isnull})


class CoverFilter(FilterSet):
    comment = filters.CharFilter(field_name='comment')
    post = RelatedFilter(PostFilter, field_name='post', queryset=Post.objects.all())

    class Meta:
        model = Cover
        fields = []


class PageFilter(FilterSet):
    title = filters.CharFilter(field_name='title')
    previous_page = RelatedFilter(PostFilter, field_name='previous_page', queryset=Post.objects.all())
    two_pages_back = RelatedFilter(PostFilter, field_name='previous_page__previous_page', queryset=Page.objects.all())

    class Meta:
        model = Page
        fields = []


#############################################################
# Aliased parameter names
#############################################################
class UserFilterWithAlias(FilterSet):
    name = filters.CharFilter(field_name='username')

    class Meta:
        model = User
        fields = []


class NoteFilterWithAlias(FilterSet):
    title = filters.CharFilter(field_name='title')
    writer = RelatedFilter(UserFilter, field_name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


class NoteFilterWithRelatedAlias(FilterSet):
    author = RelatedFilter(UserFilterWithAlias, field_name='author', queryset=User.objects.all())

    class Meta:
        model = Note
        fields = []


#############################################################
# Recursive filtersets
#############################################################
class AFilter(FilterSet):
    title = filters.CharFilter(field_name='title')
    b = RelatedFilter('BFilter', field_name='b', queryset=B.objects.all())

    class Meta:
        model = A
        fields = []


class BFilter(FilterSet):
    name = AutoFilter(field_name='name', lookups='__all__')
    c = RelatedFilter('CFilter', field_name='c', queryset=C.objects.all())

    class Meta:
        model = B
        fields = []


class CFilter(FilterSet):
    title = filters.CharFilter(field_name='title')
    a = RelatedFilter('AFilter', field_name='a', queryset=A.objects.all())

    class Meta:
        model = C
        fields = []


class PersonFilter(FilterSet):
    name = AutoFilter(field_name='name', lookups='__all__')
    best_friend = RelatedFilter(
        'tests.testapp.filters.PersonFilter',
        field_name='best_friend',
        queryset=Person.objects.all(),
    )

    class Meta:
        model = Person
        fields = []
