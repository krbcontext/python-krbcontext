# -*- coding: utf-8 -*-

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
