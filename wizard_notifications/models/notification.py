# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
from odoo import fields, models


class WizardNotification(models.Model):
    _name = 'wizard.notification'
    _description = 'Wizard Notification'

    name = fields.Char('Title', required=True)
    message = fields.Text(string='Message', required=True)
    read_message = fields.Boolean(string='Read', default=False)
    partner_id = fields.Many2one('res.partner', string="Customer")
    message_at = fields.Datetime('Send Date', required=True)

    def get_unread_msg_count(self, partner_id):
        # for app
        if partner_id:
            msg_ids = self.search([('partner_id', '=', partner_id), ('read_message', '=', False)])
            if msg_ids:
                return len(msg_ids.ids)
        else:
            return 0

    def read_all_notification(self, PARTNER_ID):
        # for app
        print('notifications')
        if PARTNER_ID:
            notifications = self.search([('partner_id', '=', PARTNER_ID), ('read_message', '!=', True)])

            for notification in notifications:
                notification.read_message = True
            return [{
                'message': 'success'
            }]

        else:
            return 0
