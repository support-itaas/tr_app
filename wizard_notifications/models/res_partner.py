# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    unread_msg_count = fields.Integer(string='Unread Message Count', compute='compute_unread_msg_count')

    @api.multi
    def compute_unread_msg_count(self):
        for partner in self:
            count = self.env['wizard.notification'].search_count(
                [('read_message', '=', False), ('partner_id', '=', partner.id)])
            partner.unread_msg_count = count

    @api.multi
    def action_view_unread_messages(self):
        notification = self.env['wizard.notification'].search(
            [('partner_id', '=', self.id), ('read_message', '=', False)])
        action = self.env.ref('wizard_notifications.wizard_notification_action').read()[0]
        if len(notification) > 1:
            action['domain'] = [('id', 'in', notification.ids)]
        elif notification:
            action['views'] = [(self.env.ref('wizard_notifications.view_notification_form').id, 'form')]
            action['res_id'] = notification.ids[0]
        return action
