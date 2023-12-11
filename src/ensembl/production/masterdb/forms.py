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
import json
from ckeditor.widgets import CKEditorWidget
from django import forms
from ensembl.production.masterdb.models import AnalysisDescription, WebData


class AnalysisDescriptionForm(forms.ModelForm):
    class Meta:
        model = AnalysisDescription
        exclude = ('created_at', 'modified_at')

    web_data_label = forms.CharField(required=False,
                                     label="WebData content (ReadOnly)",
                                     widget=forms.Textarea(attrs={'rows': 10, 'cols': 40, 'class': 'vLargeTextField',
                                                                  'readonly': 'readonly'}))

    def __init__(self, *args, **kwargs):
        super(AnalysisDescriptionForm, self).__init__(*args, **kwargs)
        current = kwargs.get('instance')
        if current:
            self.fields['web_data_label'].initial = current.web_data.label if current.web_data else ''
        if not current or not current.web_data:
            self.fields['web_data_label'].widget.attrs.update({'style': 'display:None'})


class WebDataForm(forms.ModelForm):
    class Meta:
        model = WebData
        fields = ('data', 'comment')
        widgets = {
            'data': forms.Textarea(attrs={'rows': 20, 'class': 'vLargeTextField'}),
            'comment': forms.Textarea(attrs={'rows': 7, 'class': 'vLargeTextField'}),
        }


class MetaKeyForm(forms.ModelForm):
    
    note = forms.CharField(label="Note", widget=CKEditorWidget(), required=False)
    example = forms.CharField(label="example", widget=forms.Textarea({'rows': 3}), required=False, max_length=255)
