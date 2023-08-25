# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class SaleOrderInheritWebsale(models.Model):
        _inherit = 'sale.order'

        @api.multi
        def websale_wizard_popup(self):
                print('ewewwwewewew')

                return {

                        'warning': {

                                'title': 'Warning!',

                                'message': 'The warning text'}

                }
                return {
                        'name': 'test Hello',
                        'type': 'ir.actions.act_window',
                        'res_model': 'websale.wizard',
                        'view_mode': 'form',
                        'view_type': 'form',
                        'target': 'new'
                }

class websale_wizard(models.TransientModel):
        _name = 'websale.wizard'

        _description = 'websale wizard'

        name = fields.Char('New',default='New')
