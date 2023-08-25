# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, tools, _
from odoo.modules.module import get_module_resource
import base64

class mrp_production(models.Model):
    _inherit = 'mrp.production'

    permission_type_mrp_production = fields.Selection([('machine', 'Machine'), ('cleanser', 'Cleanser')], string='Type')

    @api.onchange('bom_id')
    def _onchange_bom_id(self):
        if self.bom_id:
            self.permission_type_mrp_production = self.bom_id.permission_type

    # @api.model
    # def create(self, vals):
    #     # Assign the new user in the sales team if there's only one sales team of type `Sales`
    #     user = super(mrp_production, self).create(vals)
    #     if user.has_group('tr_extended.group_manufacturing_bom_machine') and not user.sale_team_id:
    #         teams = self.env['mrp.production'].search([('team_type', '=', 'mrp')])
    #         if len(teams.ids) == 1:
    #             user.sale_team_id = teams.id
    #     return user
