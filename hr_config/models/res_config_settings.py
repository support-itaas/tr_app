# -*- coding: utf-8 -*-
# Copyright (C) 2020-today ITAAS (Dev K.Book)

from __future__ import division
from odoo import fields, models, api , _
# from odoo.tools import amount_to_text_en
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class ResCompany(models.Model):
    _inherit = "res.company"

    default_sso_rate = fields.Float(string='Default SSO Rate(%)', digits=(16, 2))
    default_maximum_sso = fields.Float(string='Default Maximum SSO', digits=(16, 2))


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_sso_rate = fields.Float(string='Default SSO Rate(%)', digits=(16, 2),
                                    related='company_id.default_sso_rate')
    default_maximum_sso = fields.Float(string='Default Maximum SSO', digits=(16, 2),
                                       related='company_id.default_maximum_sso')



