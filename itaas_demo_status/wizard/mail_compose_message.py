# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        res = super(MailComposeMessage,self).send_mail(auto_commit =auto_commit)
        if self._context.get('default_model') == 'sale.order' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            order = self.env['sale.order'].browse([self._context['default_res_id']])
            if order.state == 'request' or order.state== 'validate':
                order.with_context(tracking_disable=True).state = 'sent'
        return res