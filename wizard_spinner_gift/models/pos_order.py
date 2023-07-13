# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import api, fields, models
import requests
import json


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.multi
    def action_pos_order_paid(self):
        super(PosOrder, self).action_pos_order_paid()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        if self.amount_total >= 0 and self.lines and self.lines[0].qty > 0:
            allotted_attempts = self.amount_total / 2000
            self.partner_id.allotted_attempts = int(allotted_attempts)

            if allotted_attempts > 0:
                spinner_notification = self.env['wizard.notification'].create({
                    # 'name': "Spin a wheel to win a prize",
                    'name': self.name + ' Providing spinning game for you.',
                    'message': 'Here is the game for you, as you ordered more than 2000' + self.pricelist_currency_id.symbol +'. Click the link %s/my/spinner_login to play spinning game and collect gifts.'% (base_url),
                    'read_message': False,
                    'partner_id': self.partner_id.id,
                    'message_at': fields.Datetime.now(),
                })

                if self.partner_id.device_token and allotted_attempts:
                    serverToken = self.env['car.settings'].sudo().search([]).server_token
                    deviceToken = self.partner_id.device_token
                    notifications = self.env['wizard.notification'].search([('partner_id', '=', self.partner_id.id),
                                                                         ('read_message', '=', False)])
                    if serverToken:
                        headers = {
                            'Content-Type': 'application/json',
                            'Authorization': 'key=' + serverToken,
                        }

                        body = {
                            'notification': {'title': 'Spin the wheel and collect Gifts',
                                             'body': 'Here is the game for you, as you ordered more than 2000' + self.pricelist_currency_id.symbol +'. Click the link %s/my/spinner_login to play spinning game and collect gifts.'% (base_url),
                                             'badge': len(notifications),
                                             "click_action": "FCM_PLUGIN_ACTIVITY"
                                             },
                            'to':
                                deviceToken,
                            'priority': 'high',
                            'data': {"notification_count": len(notifications),
                                 'notification_id': spinner_notification.id},
                        }
                        response = requests.post("https://fcm.googleapis.com/fcm/send", headers=headers, data=json.dumps(body))
