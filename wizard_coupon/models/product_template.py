# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import json
from datetime import date

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    coupon_validity = fields.Integer(string="Coupon Validity")

    @api.model
    def create(self, vals):
        if vals.get('is_pack') == True and vals.get('is_coupon') == True:
            raise UserError(_('Please choose either Combo/Pack or Coupon'))
        if vals.get('is_coupon'):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            notification = self.env['wizard.notification'].create({
                'name': 'New coupon launched',
                'message': 'A new coupon (' + vals.get('name') + ') is launched',
                'read_message': False,
                'partner_id': partner.id,
                'message_at': fields.Datetime.now(),
            })
            if partner.device_token:
                serverToken = self.env['car.settings'].sudo().search([]).server_token
                deviceToken = partner.device_token
                notifications = self.env['wizard.notification'].search([('partner_id', '=', partner.id),
                                                                        ('read_message', '=', False)])
                if serverToken:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': 'key=' + serverToken,
                    }

                    body = {
                        'notification': {'title': 'New coupon launched',
                                         'body': 'A new coupon (' + vals.get('name') + ') is launched',
                                         'badge': len(notifications),
                                         "click_action": "FCM_PLUGIN_ACTIVITY"
                                         },
                        'to':
                            deviceToken,
                        'priority': 'high',
                        'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                    }
                    response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers,
                                             data=json.dumps(body))
        res = super(ProductTemplate, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if self.is_pack and self.is_coupon == True:
            raise UserError(_('Please choose either Combo/Pack or Coupon'))
        if vals.get('is_coupon'):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            coupon = vals.get('name') if vals.get('name') else self.name
            notification = self.env['wizard.notification'].create({
                'name': 'New coupon launched',
                'message': 'A new coupon (' + coupon + ') is launched',
                'read_message': False,
                'partner_id': partner.id,
                'message_at': fields.Datetime.now(),
            })
            if partner.device_token:
                serverToken = self.env['car.settings'].sudo().search([]).server_token
                deviceToken = partner.device_token
                notifications = self.env['wizard.notification'].search([('partner_id', '=', partner.id),
                                                                        ('read_message', '=', False)])
                if serverToken:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': 'key=' + serverToken,
                    }

                    body = {
                        'notification': {'title': 'New coupon launched',
                                         'body': 'A new coupon (' + coupon + ') is launched',
                                         'badge': len(notifications),
                                         "click_action": "FCM_PLUGIN_ACTIVITY"
                                         },
                        'to':
                            deviceToken,
                        'priority': 'high',
                        'data': {"notification_count": len(notifications),
                             'notification_id': notification.id},
                    }
                    response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers,
                                             data=json.dumps(body))
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def buy_coupons(self, partner_id):
        # for app
        products = self.env['product.product'].search(['|', ('is_coupon', '=', True), ('is_pack', '=', True)],
                                                      order='sequence')
        tax_id = self.env['account.tax']
        result = []
        for product in products:
            product_data = {'id': product.id, 'is_pack': product.is_pack,
                            'name': product.name, 'is_coupon': product.is_coupon,
                            'list_price': self.env['account.tax']._fix_tax_included_price_company(
                                self._get_display_price_app(product, partner_id), product.taxes_id, tax_id,
                                product.company_id),
                            'description_sale': product.description_sale,
                            'description': product.description,
                            'coupon_validity': product.coupon_validity,
                            'image': product.image,
                            'currency_id': (product.currency_id.id, product.currency_id.name),
                            'cart_detail_image': product.cart_detail_image
                            }
            result.append(product_data)
        return result

    @api.multi
    def _get_display_price_app(self, product, partner_id):
        # for app
        pricelist = self.env['product.pricelist'].search([('id', '=', 1)])
        partner = self.env['res.partner'].search([('id', '=', partner_id)])
        if pricelist.discount_policy == 'with_discount':
            return product.with_context(pricelist=pricelist.id).price
        product_context = dict(self.env.context, partner_id=partner.id, date=date.today(),
                               uom=product.uom_id.id)
        final_price, rule_id = pricelist.with_context(product_context).get_product_price_rule(
            product, 1.0, partner)
        base_price, currency_id = self.env['sale.order.line'].with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                              1.0,
                                                                                              product.uom_id,
                                                                                              pricelist.id)
        if currency_id != pricelist.currency_id.id:
            base_price = self.env['res.currency'].browse(currency_id).with_context(product_context).compute(base_price,
                                                                                                            pricelist.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)


class ProductPack(models.Model):
    _inherit = 'product.pack'

    coupon_validity = fields.Integer(string="Coupon Validity (days)")
