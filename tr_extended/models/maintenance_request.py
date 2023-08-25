# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class maintenance_request_inherit(models.Model):
    _inherit = "maintenance.request"

    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")

