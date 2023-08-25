# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class mrp_repair_inherit(models.Model):
    _inherit = "mrp.repair"

    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")
    origin = fields.Char("Source Document")
    name = fields.Char(
        'Repair Reference',
        default=lambda self: _('New'),
        copy=False, required=True,
        states={'confirmed': [('readonly', True)]})

    @api.model
    def default_get(self, flds):
        result = super(mrp_repair_inherit, self).default_get(flds)
        # result['employee_id'] = self.env.user.partner_id.id
        result['operating_unit_id'] = self.env.user.default_operating_unit_id.id
        return result

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] =  self.env['ir.sequence'].next_by_code('mrp.repair') or _('New')
        result = super(mrp_repair_inherit, self).create(vals)
        return result

class mrp_repair_line_inherit(models.Model):
    _inherit = "mrp.repair.line"

    @api.onchange('product_id')
    def product_id_change_name(self):
        if self.product_id:
            self.update({'name':self.product_id.name,})



