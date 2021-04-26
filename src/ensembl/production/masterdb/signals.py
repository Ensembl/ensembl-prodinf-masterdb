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

from django.db.models.signals import pre_save
from django.conf import settings
from django.dispatch import receiver
from ensembl.production.masterdb.models import MasterBiotype
from django.core.mail import send_mail


@receiver(pre_save, sender=MasterBiotype)
def master_biotype_update(sender, instance: MasterBiotype, **kwargs):
    """
    Add signal to production DB app to automatically notify `ensembl-production` mailing list when someone update a biotype.
    Triggered if one of these field is modified:
    - misc_non_coding
    - object_type
    - biotype_group
    - attrib_type
    - db_type
    - is_current
    :param instance: updated instance
    :param sender: object MasterBioType Model
    :param kwargs: dict Updates parameters
    :return: None
    """
    watched_fields = [
        'object_type',
        'biotype_group',
        'attrib_type',
        'db_type',
        'is_current',
        'so_acc'
    ]
    updated_fields = []
    from_fixtures = kwargs.get('raw', False)
    created = instance.biotype_id is None
    if not (from_fixtures or created):
        # only trigger when this is no fixture load or new item
        previous = MasterBiotype.objects.get(biotype_id=instance.biotype_id)
        for field in watched_fields:
            old_val = getattr(previous, field)
            new_val = getattr(instance, field)
            if isinstance(old_val, list):
                if len(old_val) == 1:
                    old_val = old_val[0]
                else:
                    old_val = set(sorted(old_val))
            if isinstance(new_val, list):
                if len(new_val) == 1:
                    new_val = new_val[0]
                else:
                    new_val = set(sorted(new_val))
            if old_val != new_val:
                updated_fields += [(field, old_val, new_val)]
        if updated_fields:
            #  send email to config email.
            send_mail(
                '[Production MasterDB] Biotype updated !',
                '%s just modified important fields on MasterBioType table in production Master DB, please check '
                'for:' % instance.modified_by + "".join(
                    ["\n- %s: %s (initially:%s)" % (field, prev, new) for (field, prev, new) in updated_fields]),
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'me@localhost'),
                [getattr(settings, 'MASTER_DB_ALERTS_EMAIL', 'me@localhost')],
                fail_silently=settings.DEBUG
            )
