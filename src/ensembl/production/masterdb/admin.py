#   See the NOTICE file distributed with this work for additional information
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
# TODO add uncheck all is_current when checking is_current

from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from django.utils.safestring import mark_safe
import csv
from ensembl.production.djcore.admin import ProductionUserAdminMixin
from ensembl.production.djcore.utils import flatten

from .filters import IsCurrentFilter, DBTypeFilter, BioTypeFilter, TargetSiteFilter
from .forms import AnalysisDescriptionForm, MetaKeyForm, WebDataForm
from .models import *


class ProductionModelAdmin(ProductionUserAdminMixin):
    list_per_page = 50
    readonly_fields = ['created_by', 'created_at', 'modified_by', 'modified_at']
    ordering = ('-modified_at', '-created_at')
    list_filter = ['created_by', 'modified_by']
    # ability to define a list of 'only_super_admin' fields
    super_user_only = []

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser:
            flat = flatten(self.get_fields(request, obj))
            for admin_only in self.super_user_only:
                if admin_only in flat and admin_only not in readonly_fields:
                    readonly_fields += [admin_only, ]
        return readonly_fields

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def has_add_permission(self, request):
        return request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if issubclass(self.model, BaseTimestampedModel):
            list_display = list_display + ('modified_at',)
        return list_display


class ProductionTabularInline(admin.TabularInline):
    readonly_fields = ['modified_by', 'created_by', 'created_at', 'modified_at']


class AttribInline(ProductionTabularInline):
    model = MasterAttrib
    extra = 1
    fields = ('value', 'modified_by', 'created_by', 'created_at', 'modified_at')


class AttribSetInline(ProductionTabularInline):
    model = MasterAttribSet
    extra = 0
    fields = ('attrib_set_id', 'modified_by', 'created_by', 'created_at', 'modified_at')
    can_delete = True


class AnalysisDescriptionInline(ProductionTabularInline):
    model = AnalysisDescription
    extra = 0
    fields = ('logic_name', 'display_label', 'description', 'db_version', 'displayable')
    readonly_fields = ('logic_name', 'display_label', 'description', 'db_version', 'displayable')

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class HasCurrentAdmin(ProductionModelAdmin):
    list_filter = ProductionModelAdmin.list_filter + [IsCurrentFilter, ]


# Register your models here.
@admin.register(MasterAttribType)
class AttribTypeAdmin(HasCurrentAdmin):
    list_display = ('code', 'name', 'description', 'is_current')
    fields = ('code', 'name', 'description',
              ('created_by', 'created_at'),
              ('modified_by', 'modified_at'))
    search_fields = ('code', 'name', 'description')
    inlines = (AttribInline,)
    list_filter = ['code', 'name'] + HasCurrentAdmin.list_filter

    def save_model(self, request, obj, form, change):
        if not change:
            obj.code = form.cleaned_data['code']
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser or obj is None:
            return [i for i in read_only_fields if i != 'code']
        read_only_fields += ['code', ]
        return read_only_fields


@admin.register(MasterAttrib)
class AttribAdmin(HasCurrentAdmin):
    list_display = ('attrib_id', 'value', 'attrib_type', 'is_current')
    fields = ('value', 'attrib_type',
              ('created_by', 'created_at'),
              ('modified_by', 'modified_at'))
    # readonly_fields = ('attrib_id',)
    search_fields = ('attrib_id', 'value', 'attrib_type__name')


@admin.register(MasterAttribSet)
class AttribSetAdmin(HasCurrentAdmin):
    fields = ('attrib_set_id', 'attrib', 'is_current',
              ('created_by', 'created_at'),
              ('modified_by', 'modified_at')
              )
    list_display = ('attrib_set_id', 'attrib', 'is_current')
    search_fields = ('attrib__value', 'attrib_set_id')
    ordering = ('-modified_at',)
    list_filter = ['attrib_set_id', 'attrib'] + HasCurrentAdmin.list_filter


@admin.register(MasterBiotype)
class BioTypeAdmin(HasCurrentAdmin):
    # TODO DBTYPE to add display inline+flex class
    fields = ('name', 'object_type', 'db_type', 'biotype_group', 'attrib_type',
              'description', 'so_acc', 'so_term',
              ('is_dumped', 'is_current'),
              ('created_by', 'created_at'),
              ('modified_by', 'modified_at')
              )
    list_display = (
        'name', 'object_type', 'db_type', 'biotype_group', 'attrib_type', 'description', 'is_current', 'so_acc',
        'so_term')
    search_fields = (
        'name', 'object_type', 'db_type', 'biotype_group', 'attrib_type__name', 'description', 'so_acc', 'so_term')

    list_filter = ['name', 'object_type'] + [DBTypeFilter] + ['biotype_group', 'so_acc',
                                                              'so_term'] + HasCurrentAdmin.list_filter

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="biotypes.csv"'
        field_names = super().get_list_display(request)
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        return response

    export_as_csv.short_description = "Export Selected Biotype as CSV"

    actions = ['export_as_csv']


@admin.register(AnalysisDescription)
class AnalysisDescriptionAdmin(HasCurrentAdmin):
    form = AnalysisDescriptionForm
    fields = ('logic_name', 'description', 'display_label', 'web_data',
              'web_data_label',
              ('db_version', 'displayable', 'is_current'),
              ('created_by', 'created_at'),
              ('modified_by', 'modified_at'))
    list_display = ('logic_name', 'short_description', 'web_data_label', 'is_current', 'displayable')
    search_fields = ('logic_name', 'display_label', 'description', 'web_data__data')
    list_filter = ['logic_name', 'displayable'] + HasCurrentAdmin.list_filter

    def web_data_label(self, obj):
        return obj.web_data.label if obj.web_data else 'EMPTY'

    web_data_label.short_description = "Web Data Content"


@admin.register(MetaKey)
class MetakeyAdmin(HasCurrentAdmin):
    class Media:
        css = {
            'all': ('/static/production_db/css/prod_db.css',),
        }

    form = MetaKeyForm
    list_display = ('name', 'db_type', 'description', 'target_site')
    fieldsets = (
        ("General", {"fields": ('name', 'description', 'is_optional', 'target_site')}),
        ("Options", {"fields": ('db_type', 'is_current', 'is_multi_value')}),
        ("Extra", {"fields": ('note', 'example')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )
    ordering = ('name',)
    search_fields = ('name', 'db_type', 'description')
    list_filter = ['name'] + [DBTypeFilter, 'is_optional', TargetSiteFilter] + HasCurrentAdmin.list_filter

    def note(self, obj):
        if obj:
            raw_data = obj.note
            return mark_safe(raw_data.get('note'))
        return ""

    def example(self, obj):
        if obj:
            raw_data = obj.example
            return mark_safe(raw_data.get('example'))
        return ""

    def save_model(self, request, obj, form, change):
        obj.note = form.cleaned_data['note'].replace('\n', '').replace('\r', '').replace('\t', '')
        obj.example = form.cleaned_data['example'].replace('\n', '').replace('\r', '').replace('\t', '')
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return [str(i) for i in super().get_readonly_fields(request, obj) if str(i) != 'name']

        return [str(i) for i in super().get_readonly_fields(request, obj)] + ['name']


@admin.register(WebData)
class WebDataAdmin(ProductionModelAdmin):
    class Media:
        css = {
            'all': ('admin/production_db/css/prod_db.css',)
        }

    form = WebDataForm
    list_display = ('pk', 'data', 'comment', 'modified_by')
    list_editable = ('comment', 'data')
    search_fields = ('pk', 'data', 'comment')
    fields = ('data', 'comment',
              ('created_by', 'created_at'),
              ('modified_by', 'modified_at'))
    inlines = (AnalysisDescriptionInline,)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        msg = "Updating web data with multiple analysis description update it for all of them"
        if msg not in [m.message for m in messages.get_messages(request)]:
            messages.warning(request, msg)

        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(MasterExternalDb)
class MasterExternalDbAdmin(HasCurrentAdmin):
    list_display = ('db_name', 'db_release', 'status', 'db_display_name', 'priority', 'type', 'secondary_db_name',
                    'secondary_db_table', 'is_current')
    fields = ('db_name', 'status', 'db_display_name',
              'db_release', 'secondary_db_name',
              'secondary_db_table', 'description',
              'is_current',
              ('priority', 'type'),
              ('created_by', 'created_at'),
              ('modified_by', 'modified_at'))
    search_fields = (
        'db_name', 'db_release', 'status', 'db_display_name', 'priority', 'type', 'secondary_db_name',
        'secondary_db_table')
    list_filter = [
                      'db_name', 'db_release', 'status', 'db_display_name', 'priority', 'type', 'secondary_db_name',
                      'secondary_db_table'] + HasCurrentAdmin.list_filter


@admin.register(MasterMiscSet)
class MasterMiscSetAdmin(admin.ModelAdmin):
    list_display = ('misc_set_id', 'code', 'name', 'short_description')
    readonly_fields = ('misc_set_id',)
    fields = ('misc_set_id', 'code', 'name',
              'description', 'max_length', 'is_current',
              ('created_by', 'created_at'),
              ('modified_by', 'modified_at'))
    search_fields = ('name', 'description', 'code')
    list_filter = ['code', 'name', 'description']


@admin.register(MasterUnmappedReason)
class MasterUnmappedReasonAdmin(admin.ModelAdmin):
    list_display = ('unmapped_reason_id', 'summary_description')
    search_fields = ('summary_description',)
    list_filter = ('summary_description',)
