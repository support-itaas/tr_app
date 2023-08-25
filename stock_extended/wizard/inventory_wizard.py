# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
#
# class inventory_age_wizard(models.TransientModel):
#     _inherit = 'inventory.age.wizard'
#
#     restrict_locations = fields.Many2many('stock.location', string='Restrict Location')
#
#     @api.model
#     def default_get(self, fields):
#         res = super(inventory_age_wizard,self).default_get(fields)
#         if self.env.user.restrict_locations:
#             restrict_locations = self.env.user.stock_location_ids.filtered(lambda x: x.usage == 'internal').ids
#         else:
#             restrict_locations = self.env['stock.location'].search([('usage', '=', 'internal')]).ids
#         res.update({'restrict_locations':restrict_locations})
#         return res