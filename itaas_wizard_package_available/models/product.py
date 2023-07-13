# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    is_limit_branch = fields.Boolean(string='Limited Branch')
    available_branch = fields.Many2many('project.project',string='Available Branch')
    maximum_order_branch = fields.Integer(string='Maximum Order per Branch')
    maximum_order_customer = fields.Integer(string='Maximum Order per Customer')



    @api.multi
    def buy_coupons(self, partner_id):
        today = fields.datetime.today()
        products = self.env['product.product'].search(['|', ('is_coupon', '=', True), ('is_pack', '=', True),('is_app_available', '=', True),('start_date', '<=', today),('end_date', '>=', today)],
                                                      order='sequence')
        tax_id = self.env['account.tax']
        result = []
        for product in products:
            product_data = {'id': product.id, 'is_pack': product.is_pack,
                            'name': product.name, 'is_coupon': product.is_coupon,
                            'is_promotional_pkg': product.is_promotional_pkg,
                            # 'list_price': self.env['account.tax']._fix_tax_included_price_company(
                            #     self._get_display_price_app(product, partner_id), product.taxes_id, tax_id,
                            #     product.company_id),
                            'list_price': self._get_display_price_app(product, partner_id),
                            'description_sale': product.description_sale,
                            'description': product.description,
                            'coupon_validity': product.coupon_validity,
                            'image': product.image,
                            'currency_id': (product.currency_id.id, product.currency_id.name),
                            'cart_detail_image': product.cart_detail_image,
                            'default_code': product.default_code
                            }
            result.append(product_data)
        return result
