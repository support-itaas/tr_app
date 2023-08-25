# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.modules.module import get_module_resource
import base64

class Hr_Holidays(models.Model):
    _inherit = "hr.holidays"

    image = fields.Binary(related='employee_id.image', string='Photo', attachment=True,
        help="This field holds the image used as photo for the employee, limited to 1024x1024px.")

