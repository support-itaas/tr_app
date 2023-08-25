# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class MrpRepairInherit(models.Model):
    _inherit = 'mrp.repair'

    name = fields.Char(
        'Repair Reference',
        default='New',
        copy=False, required=True,
        states={'confirmed': [('readonly', True)]})

    # defaults = {
    #     'name': None,
    # }

    # default=lambda self: self.env['ir.sequence'].next_by_code('mrp.repair'),

    @api.multi
    def _create(self, vals):
        res = super(MrpRepairInherit, self)._create(vals)

        if vals['name'] == 'New':
            repair_id = self.env['mrp.repair'].search([('id','=',res)])
            if repair_id:
                repair_id.name = self.env['ir.sequence'].next_by_code('mrp.repair')

        return res

    # @api.multi
    # def _write(self, vals):
    #     print('_write')
    #     res = super(MrpRepairInherit, self)._write(vals)
    #     print(res)
    #
    #     print(vals)
    #     print('write end...')
    #     return res