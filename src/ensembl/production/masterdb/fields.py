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
from django.conf import settings
from django.db import models

if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    from django_mysql.models import EnumField
else:
    class EnumField(models.CharField):
        def __init__(self, *args, **kwargs):
            if 'choices' not in kwargs:
                raise AttributeError('EnumField requires `choices` attribute.')
            else:
                choices = []
                for choice in kwargs["choices"]:
                    if isinstance(choice, tuple):
                        choices.append(choice)
                    elif isinstance(choice, str):
                        choices.append((choice, choice))
                    else:
                        raise TypeError(
                            'Invalid choice "{choice}". '
                            "Expected string or tuple as elements in choices".format(
                                choice=choice
                            )
                        )
                kwargs["choices"] = choices
            if 'max_length' not in kwargs:
                kwargs["max_length"] = 256
            super(EnumField, self).__init__(*args, **kwargs)