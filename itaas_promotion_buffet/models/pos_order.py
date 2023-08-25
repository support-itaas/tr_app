# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import api, fields, models
import requests
import json
from dateutil.relativedelta import relativedelta

class PosOrder(models.Model):
    _inherit = "pos.order"

    car_id = fields.Many2one('car.details', string='Plate Number', domain="[('partner_id','=',partner_id)]",)

    @api.model
    def create(self, values):
        res = super(PosOrder, self).create(values)
        print('PosOrder values ', values)
        if 'partner_id' in values and values.get('partner_id') and values.get('pos_reference'):
            car_id = self.env['car.details'].search([('partner_id', '=', values.get('partner_id'))], limit=1)
            if car_id:
                res.update({'car_id': car_id.id})

        # if 'partner_id' in val and val.get('partner_id'):
        #     partner = self.env['res.partner'].browse(val.get('partner_id'))
        #     if partner.car_ids:
        #         res.update({'car_id': partner.car_ids[0].id})

        return res

    @api.onchange('partner_id')
    def onchange_car_id(self):
        if not self.partner_id:
            return

        if self.partner_id.car_ids:
            self.car_id = self.partner_id.car_ids[0].id
        else:
            self.car_id = False

    def create_coupons(self):
        res = super(PosOrder, self).create_coupons()
        for order in self:
            coupons = self.env['wizard.coupon'].search([('order_id', '=', order.id)])
            for coupon in coupons:
                coupon.update({'plate_number_id': order.car_id.id})

        return res


class WizardCoupon(models.Model):
    _inherit = "wizard.coupon"

    order_car_id = fields.Many2one('car.details', string='Plate Number', related='order_id.car_id')

    # def create(self, val):
    #     res = super(WizardCoupon, self).create(val)
    #     if 'order_id' in val and val.get('order_id'):
    #         order_id = self.env['wizard.coupon'].browse(val.get('order_id'))
    #         if order_id.car_id:
    #             res.update({'plate_number_id': order_id.car_id.id})
    #
    #     return res
