# -*- coding: utf-8 -*-

# Copyright (C) 2013  Chenxiong Qi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple
from datetime import datetime

import krbV
import os
import pwd


CredentialTime = namedtuple('CredentialTime',
                            'authtime starttime endtime renew_till')


def get_login():
    ''' Get current effective user name '''
    return pwd.getpwuid(os.getuid()).pw_name


def build_tgt_ticket(principal):
    return 'krbtgt/%(realm)s@%(realm)s' % {'realm': principal.realm}


def get_tgt_time(context, ccache, principal):
    ''' Get specified TGT's credential time.

    Arguments:
    - context, current context object.
    - ccache, the CCache object that is associated with context.
    - principal, the principal that is being used for getting ticket.
    '''
    tgt_princ = krbV.Principal(build_tgt_ticket(principal), context=context)
    creds = (principal, tgt_princ,
             (0, None), (0, 0, 0, 0), None, None, None, None,
             None, None)
    result = ccache.get_credentials(creds, krbV.KRB5_GC_CACHED, 0)
    time_conv = datetime.fromtimestamp
    return CredentialTime._make([time_conv(t) for t in result[3]])
