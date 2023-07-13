# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    available_coupon_count = fields.Integer(string='Available Coupons', compute='_compute_available_coupon_count')
    total_coupon_count = fields.Integer(string='Total Coupons', compute='_compute_total_coupon_count')
    device_token = fields.Char(string='Device Token')

    @api.multi
    def _compute_total_coupon_count(self):
        for partner in self:
            total_count = self.env['wizard.coupon'].search([('partner_id', '=', partner.id)])
            partner.total_coupon_count = len(total_count)

    @api.multi
    def _compute_available_coupon_count(self):
        for partner in self:
            available_count = self.env['wizard.coupon'].search(
                [('partner_id', '=', partner.id), ('state', '=', 'draft')])
            partner.available_coupon_count = len(available_count)

    @api.multi
    def action_view_coupons(self):
        self.ensure_one()
        action = self.env.ref('wizard_coupon.wizard_coupon_action').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action

    def get_fcm_token(self, PARTNER_ID, FCM_TOKEN):
        if PARTNER_ID:
            if FCM_TOKEN:
                partner = self.browse(PARTNER_ID)
                partner.device_token = FCM_TOKEN

                return [{
                    'message': 'success'
                }]
            else:
                return [{
                    'message': 'FCM Token not found.'
                }]
        else:
            return [{
                'message': 'Partner ID not found.'
            }]

