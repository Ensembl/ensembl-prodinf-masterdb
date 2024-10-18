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

from .filters import IsCurrentFilter, DBTypeFilter, BioTypeFilter
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
        if request.user.is_superuser:
            return ProductionModelAdmin.readonly_fields
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
    fields = ('logic_name', 'display_label')
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
    search_fields = ('code', 'name', 'description')
    inlines = (AttribInline,)
    list_filter = ['code', 'name'] + HasCurrentAdmin.list_filter
    fieldsets = (
        ("General", {"fields": ('code', 'name', 'description')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )

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
    list_display = ('value', 'attrib_type', 'is_current', 'attrib_id',)
    search_fields = ('attrib_id', 'value', 'attrib_type__name')
    fieldsets = (
        ("General", {"fields": ('value', 'attrib_type')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )


@admin.register(MasterAttribSet)
class AttribSetAdmin(HasCurrentAdmin):
    list_display = ('attrib', 'is_current', 'attrib_set_id')
    search_fields = ('attrib__value', 'attrib_set_id')
    ordering = ('-modified_at',)
    list_filter = ['attrib_set_id', 'attrib'] + HasCurrentAdmin.list_filter
    fieldsets = (
        ("General", {"fields": ('attrib', 'is_current')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )


@admin.register(MasterBiotype)
class BioTypeAdmin(HasCurrentAdmin):
    class Media:
        css = {
            'all': ('production_db/css/prod_db.css',)
        }

    fieldsets = (
        ("General", {"fields": ('name', 'description', 'object_type', 'biotype_group', 'attrib_type')}),
        ("Options", {"fields": ('so_acc', 'so_term', 'db_type', 'is_dumped', 'is_current')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
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
    list_display = ('logic_name', 'short_description', 'web_data_label', 'is_current', 'displayable')
    search_fields = ('logic_name', 'display_label', 'description', 'web_data__data')
    list_filter = ['displayable'] + HasCurrentAdmin.list_filter
    fieldsets = (
        ("General", {"fields": ('logic_name', 'description', 'display_label', 'web_data', 'web_data_label')}),
        ("Options", {"fields": ('db_version', 'displayable', 'is_current')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )

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
    list_display = ('name', 'db_type', 'description')
    fieldsets = (
        ("General", {"fields": ('name', 'description', 'is_optional', 'is_current')}),
        ("Options", {"fields": ('db_type', 'is_multi_value')}),
        ("Extra", {"fields": ('note', 'example')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )
    ordering = ('name',)
    search_fields = ('name', 'db_type', 'description')
    list_filter = ['name'] + [DBTypeFilter, 'is_optional'] + HasCurrentAdmin.list_filter

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
        if request.user.is_superuser:
            return super().get_readonly_fields(request, obj)
        return [str(i) for i in super().get_readonly_fields(request, obj)] + ['name', 'is_optional']


@admin.register(MetaKeyMVP)
class MetakeyMVPAdmin(HasCurrentAdmin):
    class Media:
        css = {
            'all': ('/static/production_db/css/prod_db.css',),
        }

    form = MetaKeyForm
    list_display = ('name', 'db_type', 'description')
    fieldsets = (
        ("General", {"fields": ('name', 'description', 'is_optional', 'is_current')}),
        ("Options", {"fields": ('db_type', 'is_multi_value')}),
        ("Extra", {"fields": ('note', 'example')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )
    ordering = ('name',)
    search_fields = ('name', 'db_type', 'description')
    list_filter = ['name'] + [DBTypeFilter, 'is_optional'] + HasCurrentAdmin.list_filter

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
        if request.user.is_superuser:
            return super().get_readonly_fields(request, obj)
        return [str(i) for i in super().get_readonly_fields(request, obj)] + ['name', 'is_optional']


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

    inlines = (AnalysisDescriptionInline,)
    fieldsets = (
        ('General', {'fields': ('data', 'comment')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        msg = "Updating web data with multiple analysis description update it for all of them"
        if msg not in [m.message for m in messages.get_messages(request)]:
            messages.warning(request, msg)
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(MasterExternalDb)
class MasterExternalDbAdmin(HasCurrentAdmin):
    list_display = ('db_name', 'db_release', 'status', 'db_display_name', 'priority', 'type', 'secondary_db_name',
                    'secondary_db_table', 'is_current')
    search_fields = (
        'db_name', 'db_release', 'status', 'db_display_name', 'priority', 'type', 'secondary_db_name',
        'secondary_db_table')
    list_filter = ['db_name', 'db_release', 'status', 'db_display_name', 'priority', 'type', 'secondary_db_name',
                   'secondary_db_table'] + HasCurrentAdmin.list_filter
    fieldsets = (
        ('General', {
            'fields': ('db_name', 'status', 'db_display_name',
                       'db_release', 'secondary_db_name',
                       'secondary_db_table')
        }),
        ('Details', {'fields': ('description', 'is_current', ('priority', 'type'))}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )


@admin.register(MasterMiscSet)
class MasterMiscSetAdmin(ProductionModelAdmin):
    list_display = ('code', 'name', 'short_description', 'misc_set_id')
    # readonly_fields = ('misc_set_id',)
    search_fields = ('name', 'description', 'code')
    list_filter = ['code', 'name', 'description']
    fieldsets = (
        ('General', {'fields': ('misc_set_id', 'code', 'name', 'description', 'max_length', 'is_current')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )

    def get_readonly_fields(self, request, obj=None):
        return super().get_readonly_fields(request, obj) + ['misc_set_id']


@admin.register(MasterUnmappedReason)
class MasterUnmappedReasonAdmin(ProductionModelAdmin):
    list_display = ('summary_description', 'full_description')
    search_fields = ('summary_description',)
    fieldsets = (
        ('General', {'fields': ('summary_description', 'full_description')}),
        ("Log", {"fields": ('created_by', 'created_at', 'modified_by', 'modified_at')})
    )
