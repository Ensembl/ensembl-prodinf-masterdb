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
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import APIException

from ensembl.production.masterdb.models import *

User = get_user_model()


class WebDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebData
        exclude = ('created_at', 'modified_at')


class BaseUserTimestampSerializer(serializers.ModelSerializer):
    user = serializers.CharField(write_only=True, required=False)

    def create(self, validated_data):
        if 'user' in validated_data:
            validated_data['created_by'] = validated_data.pop('user')
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'user' in validated_data:
            validated_data['modified_by'] = validated_data.pop('user')
        return super().update(instance, validated_data)

    def validate(self, data):
        if "user" in data:
            try:
                data['user'] = User.objects.get(username=data.pop('user', ''), is_staff=True)
            except ObjectDoesNotExist:
                exc = APIException(code='error', detail="User not found")
                # hack to update status code. :-(
                exc.status_code = status.HTTP_400_BAD_REQUEST
                raise exc
        data = super().validate(data)
        return data


class BiotypeSerializerUser(BaseUserTimestampSerializer):
    is_current = serializers.BooleanField(default=True, initial=True)

    class Meta:
        model = MasterBiotype
        exclude = ('created_at', 'modified_at')


class AttribTypeSerializerUser(BaseUserTimestampSerializer):
    is_current = serializers.BooleanField(default=True, initial=True)

    class Meta:
        model = MasterAttribType
        exclude = ('created_at', 'modified_at')


class AttribTypeSerializerNoValidator(serializers.ModelSerializer):
    is_current = serializers.BooleanField(default=True, initial=True)

    class Meta:
        model = MasterAttribType
        exclude = ('created_at', 'modified_at')
        extra_kwargs = {
            'code': {
                'validators': [],
            }
        }


class AttribSerializerUser(BaseUserTimestampSerializer):
    is_current = serializers.BooleanField(default=True, initial=True)

    class Meta:
        model = MasterAttrib
        exclude = ('created_at', 'modified_at')

    attrib_type = AttribTypeSerializerNoValidator(many=False, required=True)

    def create(self, validated_data):
        attrib_type = validated_data.pop('attrib_type')
        elem = MasterAttribType.objects.filter(code=attrib_type.get('code')).first()
        if not elem:
            attrib_type['created_by'] = validated_data.get('user', None)
            elem = MasterAttribType.objects.create(**attrib_type)
        elif validated_data.get('user', None) is not None:
            attrib_type['modified_by'] = validated_data.get('user')
            elem = MasterAttribType.objects.update(**attrib_type)
        validated_data['attrib_type'] = elem
        return super(AttribSerializerUser, self).create(validated_data)


class AnalysisDescriptionSerializerUser(BaseUserTimestampSerializer):
    is_current = serializers.BooleanField(default=True, initial=True)

    class Meta:
        model = AnalysisDescription
        exclude = ('created_at', 'modified_at')

    web_data = WebDataSerializer(many=False, required=False)

    def create(self, validated_data):
        if 'web_data' in validated_data:
            validated_data['web_data'] = self.process_web_data(validated_data.pop('web_data'),
                                                               validated_data.get('user', None))
        else:
            validated_data['web_data'] = None

        return super(AnalysisDescriptionSerializerUser, self).create(validated_data)

    @staticmethod
    def process_web_data(web_data_content, user):
        search_content = web_data_content.get('data', None)
        elem = WebData.objects.filter(data=search_content).first()
        if not elem:
            web_data_content['created_by'] = user
            elem = WebData.objects.create(**web_data_content)
        else:
            web_data_content['modified_by'] = user
            WebData.objects.filter(pk=elem.web_data_id).update(**web_data_content)
        return elem

    def update(self, instance, validated_data):
        if 'web_data' in validated_data:
            instance.web_data = self.process_web_data(validated_data.pop('web_data'),
                                                      validated_data.get('user', None))
        return super(AnalysisDescriptionSerializerUser, self).update(instance, validated_data)
