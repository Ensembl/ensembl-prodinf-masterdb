# See the NOTICE file distributed with this work for additional information
#   regarding copyright ownership.
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from django.contrib.admin import SimpleListFilter
from django.db.models import Q
from ensembl.production.masterdb.models import MetaKey, DB_TYPE_CHOICES_METAKEY, DB_TYPE_CHOICES_BIOTYPE


class IsCurrentFilter(SimpleListFilter):
    title = 'Is Current'

    parameter_name = 'is_current'

    def lookups(self, request, model_admin):
        return (
            (None, 'Yes'),
            ('no', 'No'),
            ('all', 'All'),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(is_current=False)
        elif self.value() is None:
            return queryset.filter(is_current=True)


class IsDisplayableFilter(SimpleListFilter):
    title = 'Is Displayed'

    parameter_name = 'displayable'

    def lookups(self, request, model_admin):
        return (
            (None, 'Yes'),
            ('no', 'No'),
            ('all', 'All'),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(displayable=False)
        elif self.value() is None:
            return queryset.filter(displayable=True)


class DBTypeFilter(SimpleListFilter):
    title = 'DB Type'
    parameter_name = 'db_type'

    def lookups(self, request, model_admin):
        return DB_TYPE_CHOICES_METAKEY

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(db_type__icontains=self.value())
        elif self.value() is None:
            return queryset


class BioTypeFilter(SimpleListFilter):
    title = 'BioType'
    parameter_name = 'db_type'

    def lookups(self, request, model_admin):
        return DB_TYPE_CHOICES_BIOTYPE

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(db_type__icontains=self.value())
        elif self.value() is None:
            return queryset
