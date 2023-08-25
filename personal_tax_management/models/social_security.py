# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import datetime

class social_security(models.Model):
    _name = 'social.security'

    name = fields.Char('Name')
    social_line_ids = fields.One2many('social.security.line','social_id')

class social_security_line(models.Model):
    _name = 'social.security.line'
    _rec_name = 'year'

    def year_choices(self):
        return [(r, r) for r in range(1984, datetime.date.today().year + 1)]

    def current_year(self):
        return datetime.date.today().year

    minimum_rate = fields.Float('Minimum Rate')
    maximum_rate = fields.Float('Maximum Rate')
    year = fields.Integer(_('Year'), choices=year_choices, default=current_year)
    social_id = fields.Many2one('social.security')










