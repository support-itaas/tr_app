# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import json

import requests

from odoo import fields, api, models


class SendNotificationWizard(models.TransientModel):
    _name = 'send.notification.wizard'
    _description = 'Send Notification Wizard'

    name = fields.Char('Title', required=True)
    message = fields.Text(string='Message', required=True)
    partner_ids = fields.Many2many('res.partner', string="Customer")

    @api.multi
    def send_notifications(self):
        partners = []
        if self.partner_ids:
            for partner in self.partner_ids:
                partners.append(partner)
        else:
            partner = self.env['res.partner'].search([('is_a_member', '=', True)])
            if partner:
                for partner in partner:
                    partners.append(partner)
        for partner_id in partners:
            notification = self.env['wizard.notification'].create({
                'name': self.name,
                'message': self.message,
                'read_message': False,
                'partner_id': partner_id.id,
                'message_at': fields.Datetime.now(),
            })
            if partner_id.device_token:
                serverToken = self.env['car.settings'].sudo().search([]).server_token
                deviceToken = partner_id.device_token
                notifications = self.env['wizard.notification'].search([('partner_id', '=', partner_id.id),
                                                                        ('read_message', '=', False)])

                if serverToken:
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': 'key=' + serverToken,
                    }

                    body = {
                        'notification': {'title': self.name,
                                         'body': self.message,
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
