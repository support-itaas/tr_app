# -*- coding: utf-8 -*-
from unittest import result

from odoo import models, fields, api, _
from odoo.addons.test_impex.models import field
from odoo.exceptions import UserError, AccessError
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta

# from odoo.fields import FailedValue
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, relativedelta, pytz, float_compare



class MeterType(models.Model):
    _name = 'meter.type'
    _description = 'Meter Type'
    _order = "sequence, id"

    @api.model
    def _get_sequence(self):
        others = self.search([('sequence', '<>', False)], order='sequence desc', limit=1)
        if others:
            return (others[0].sequence or 0) + 1
        return 1

    sequence = fields.Integer('Sequence', default=_get_sequence)
    name = fields.Char(string='Name', required=True)
