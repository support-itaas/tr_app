# -*- coding: utf-8 -*-
from unittest import result

from odoo import models, fields, api, _
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, AccessError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

# from odoo.fields import FailedValue
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, relativedelta, pytz, float_compare

_STATES = [
    ('draft', 'Draft'),
    ('to_mkt_approve', 'To MKT Approve'),
    ('to_approve', 'To be approved'),
    ('to_waiting', 'Waiting To be approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('done', 'Done')
]



class Purchase_request_s(models.Model):
    _inherit = 'purchase.request'

    @api.one
    def button_approved(self):
        super(Purchase_request_s,self).button_approved()
        group_id = self.env.ref('pr_notification.group_pr_approve_notification').sudo()
        print (group_id.sudo().users)


