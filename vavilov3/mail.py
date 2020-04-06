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

from pathlib import Path

from vavilov3.entities.tags import INSTITUTE_EMAIL
from vavilov3.conf import settings
from vavilov3.models import Institute


def prepare_mail_request(seed_request):
    requester_email = seed_request.requester_email

    subject = settings.SEED_REQUEST_MAIL_SUBJECT
    from_email = settings.SEED_REQUEST_MAIL_FROM
    institute_code = seed_request.requested_accessions.first().institute.code
    institute = Institute.objects.get(code=institute_code)
    curator_email = institute.data.get(INSTITUTE_EMAIL, None)
    if not curator_email:
        msg = 'This institute has no email to send requests {}'
        raise RuntimeError(msg.format(institute_code))

    schema = Path(settings.SEED_REQUEST_TEMPLATE).read_text()
    accessions = ["{}:{}".format(acc.institute.code, acc.germplasm_number) for acc in seed_request.requested_accessions.all()]
    body = schema.format(request_uid=seed_request.request_uid,
                         requester_name=seed_request.requester_name,
                         requester_type=seed_request.requester_type,
                         requester_institution=seed_request.requester_institution,
                         requester_address=seed_request.requester_address,
                         requester_city=seed_request.requester_city,
                         requester_postal_code=seed_request.requester_postal_code,
                         requester_region=seed_request.requester_region,
                         requester_country=seed_request.requester_country,
                         requester_email=seed_request.requester_email,
                         requested_accessions="\n".join(accessions),
                         request_aim=seed_request.request_aim,
                         request_comments=seed_request.request_comments)
    if settings.EMAIL_DEBUG:
        curator_email = settings.SEED_REQUEST_MAIL_DEBUG_TO
    recipient_list = [curator_email] + [requester_email]
    message = (subject, body, from_email, recipient_list)
    return message
