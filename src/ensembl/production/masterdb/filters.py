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
from ensembl.production.masterdb.models import DB_TYPE_CHOICES_METAKEY, DB_TYPE_CHOICES_BIOTYPE, DC_META_SITE
from ensembl.production.djcore.filters import BackEndListFilter


class IsCurrentFilter(BackEndListFilter):
    title = 'Is Current'
    parameter_name = 'is_current'
    _lookups = (
        (None, 'Yes'),
        ('no', 'No'),
        ('all', 'All'),
    )

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(is_current=False)
        elif self.value() is None:
            return queryset.filter(is_current=True)


class IsDisplayableFilter(BackEndListFilter):
    title = 'Is Displayed'
    parameter_name = 'displayable'
    _lookups = (
        (None, 'Yes'),
        ('no', 'No'),
        ('all', 'All'),
    )

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(displayable=False)
        elif self.value() is None:
            return queryset.filter(displayable=True)


class DBTypeFilter(BackEndListFilter):
    title = 'DB Type'
    parameter_name = 'db_type'
    _lookups = DB_TYPE_CHOICES_METAKEY

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(db_type__icontains=self.value())
        elif self.value() is None:
            return queryset


class TargetSiteFilter(BackEndListFilter):
    title = 'Target Site'
    parameter_name = 'target_site'
    _lookups = DC_META_SITE

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(target_site__icontains=self.value())
        elif self.value() is None:
            return queryset


class BioTypeFilter(BackEndListFilter):
    title = 'BioType'
    parameter_name = 'db_type'
    _lookups = DB_TYPE_CHOICES_BIOTYPE

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(db_type__icontains=self.value())
        elif self.value() is None:
            return queryset
