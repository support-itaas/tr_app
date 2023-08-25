# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.modules.module import get_module_resource
import base64

class res_partner(models.Model):
    _inherit = 'res.partner'

    main_company = fields.Boolean(string='Main Company')



