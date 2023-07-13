# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
import json

import requests

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    add_to_wallet = fields.Boolean(string='Add to Wallet', default=False)
    branch_id = fields.Many2one('project.project', string='Branch')

    @api.model
    def create(self, vals):
        if vals.get('payment_method_id') and vals['payment_method_id'] == 'manual':
            # for app api
            payment_method_ids = self.env['account.journal'].browse(vals['journal_id']). \
                _default_inbound_payment_methods()
            vals['payment_method_id'] = payment_method_ids and payment_method_ids[0].id
        res = super(AccountPayment, self).create(vals)
        if vals.get('add_to_wallet'):
            branch = self.env['project.project'].browse(vals.get('branch_id'))
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            payment_method = self.env['account.journal'].browse(vals.get('journal_id'))
            notification = self.env['wizard.notification'].create({
                'name': self.env.user.company_id.currency_id.symbol + ' ' + str(
                    vals.get('amount')) + ' is added to your wallet',
                'message': self.env.user.company_id.currency_id.symbol + ' ' + str(vals.get(
                    'amount')) + ' is added to your wallet' + ' at ' + branch.name + ' by ' + payment_method.name + ' on ' +
                           res.payment_date,
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
                        'notification': {'title': self.env.user.company_id.currency_id.symbol + ' ' + str(
                        vals.get('amount')) + ' is added to your wallet',
                                         'body': self.env.user.company_id.currency_id.symbol + ' ' + str(vals.get(
                        'amount')) + ' is added to your wallet' + ' at ' + branch.name + ' by ' + payment_method.name + ' on ' +
                               res.payment_date,
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
        if res.branch_id:
            res.write({'name': self.env['ir.sequence'].next_by_code('account.payment.wallet') or _('New')})
        return res
