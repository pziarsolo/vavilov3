#
# Copyright (C) 2019 P.Ziarsolo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import smtplib
from pathlib import Path

from django.core.mail import send_mass_mail

from vavilov3.entities.tags import (INSTITUTE_CODE, INSTITUTE_EMAIL,
                                    GERMPLASM_NUMBER)
from vavilov3.conf import settings
from vavilov3.models import Institute


def prepare_mail_petition(seed_petition):
    petitioner_email = seed_petition.petitioner_email

    subject = settings.SEED_PETITION_MAIL_SUBJECT
    from_email = settings.SEED_PETITION_MAIL_FROM
    institute_code = seed_petition.requested_accessions.first().institute.code
    institute = Institute.objects.get(code=institute_code)
    curator_email = institute.data.get(INSTITUTE_EMAIL, None)

    if not curator_email:
        msg = 'This institute has no email to send petitions {}'
        raise RuntimeError(msg.format(institute_code))

    schema = Path(settings.SEED_PETITION_TEMPLATE).read_text()
    accessions = ["{}:{}".format(acc.institute.code, acc.germplasm_number) for acc in seed_petition.requested_accessions.all()]
    body = schema.format(petition_id=seed_petition.petition_id,
                         petitioner_name=seed_petition.petitioner_name,
                         petitioner_type=seed_petition.petitioner_type,
                         petitioner_institution=seed_petition.petitioner_institution,
                         petitioner_address=seed_petition.petitioner_address,
                         petitioner_city=seed_petition.petitioner_city,
                         petitioner_postal_code=seed_petition.petitioner_postal_code,
                         petitioner_region=seed_petition.petitioner_region,
                         petitioner_country=seed_petition.petitioner_country,
                         petitioner_email=seed_petition.petitioner_email,
                         petition_accessions="\n".join(accessions),
                         petition_aim=seed_petition.petition_aim,
                         petition_comments=seed_petition.petition_comments)
    if settings.EMAIL_DEBUG:
        curator_email = settings.SEED_PETITION_MAIL_DEBUG_TO
    recipient_list = [curator_email] + [petitioner_email]
    message = (subject, body, from_email, recipient_list)
    return message


def prepare_and_send_seed_petition_mails(struct):
    accessions_by_institute = {}
    for accession in struct.petition_accessions:
        institute_code = accession[INSTITUTE_CODE]
        if institute_code not in accessions_by_institute:
            accessions_by_institute[institute_code] = []
        accessions_by_institute[institute_code].append(accession)

    errors = []
    mail_tuples = []
    petitioner_email = struct.petitioner_email

    subject = settings.SEED_PETITION_MAIL_SUBJECT
    from_email = settings.SEED_PETITION_MAIL_FROM

    for institute_code, accessions in accessions_by_institute.items():
        institute = Institute.objects.get(code=institute_code)
        curator_email = institute.data.get(INSTITUTE_EMAIL, None)
        if not curator_email:
            msg = 'This institute has no email to send petitions {}'
            errors.append(msg.format(institute_code))
            continue
        schema = Path(settings.SEED_PETITION_TEMPLATE).read_text()
        accessions = ["{}:{}".format(acc[INSTITUTE_CODE], acc[GERMPLASM_NUMBER]) for acc in struct.petition_accessions]
        body = schema.format(petition_id=struct.petition_id,
                             petitioner_name=struct.petitioner_name,
                             petitioner_type=struct.petitioner_type,
                             petitioner_institution=struct.petitioner_institution,
                             petitioner_address=struct.petitioner_address,
                             petitioner_city=struct.petitioner_city,
                             petitioner_postal_code=struct.petitioner_postal_code,
                             petitioner_region=struct.petitioner_region,
                             petitioner_country=struct.petitioner_country,
                             petitioner_email=struct.petitioner_email,
                             petition_accessions="\n".join(accessions),
                             petition_aim=struct.petition_aim,
                             petition_comments=struct.petition_comments)
        if settings.EMAIL_DEBUG:
            curator_email = settings.SEED_PETITION_MAIL_DEBUG_TO
        recipient_list = [curator_email] + [petitioner_email]
        message = (subject, body, from_email, recipient_list)
        mail_tuples.append(message)

    if errors:
        raise RuntimeError('There were some error: {}'.format(','.join(errors)))

    try:
        send_mass_mail(tuple(mail_tuples))
    except smtplib.SMTPException as error:
        raise RuntimeError(error)
