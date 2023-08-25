# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import api, fields, models


class WizardCustomerTransfer(models.TransientModel):
    _name = 'wizard.customer.transfer'
    _description = 'Transfer customer in coupon'

    partner_id = fields.Many2one('res.partner', string='Customer')
    note = fields.Text(string='Note')

    @api.multi
    def transfer_customer_button(self):
        coupon_id = self.env['wizard.coupon'].browse(self.env.context.get('active_id'))
        transferring_partner = coupon_id.partner_id
        coupon_id.write({'partner_id': self.partner_id.id, 'note': self.note})
        self.env['wizard.notification'].create({
            'name': 'Coupon ' + coupon_id.name + ' is transferred',
            'message': 'Your coupon ' + coupon_id.name + ' is successfully transferred to ' + self.partner_id.name + ' (' + str(
                self.partner_id.mobile) + ') ',
            'read_message': False,
            'partner_id': transferring_partner.id,
            'message_at': fields.Datetime.now(),
        })
        self.env['wizard.notification'].create({
            'name': 'Coupon ' + coupon_id.name + ' is received',
            'message': 'You are successfully received Coupon with Coupon number ' + coupon_id.name + ' from ' + transferring_partner.name + ' (' + str(
                transferring_partner.mobile) + ') ' + 'is received',
            'read_message': False,
            'partner_id': self.partner_id.id,
            'message_at': fields.Datetime.now(),
        })
