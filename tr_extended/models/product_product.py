# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class ProductTemplate_inherit(models.Model):
    _inherit = "product.template"

    # add fields 20190527 ###################################
    cost_currency_id = fields.Many2one('res.currency',string='Cost Currency')


class ProductProduct_inherit(models.Model):
    _inherit = "product.product"

    # add fields 20190527 ###################################
    cost_currency_id = fields.Many2one('res.currency',string='Cost Currency')

    @api.multi
    def set_default_internal_ref(self):
        product_ids = self.env['product.product'].search([]).filtered(lambda x: x.default_code != x.product_tmpl_id.default_code)
        for product in product_ids:
            product.update({'default_code':product.product_tmpl_id.default_code})

