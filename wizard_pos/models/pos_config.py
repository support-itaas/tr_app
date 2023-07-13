# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    branch_id = fields.Many2one('project.project', 'Branch')
    operating_branch_id = fields.Many2one('operating.unit', 'Operating Branch')

    @api.multi
    def open_session_cb(self):
        if not self.branch_id or not self.operating_branch_id or not self.required_customer:
            raise UserError(_(
                'Please specify a Branch, Operating Branch and enable Customer Required in pos configuration settings'))

        closed_session = self.env['pos.session'].search([('state', '=', 'closed'), ('config_id', '=', self.id)])
        if closed_session:
            self.ensure_one()
            if not self.current_session_id:
                self.current_session_id = self.env['pos.session'].create({
                    'user_id': self.env.uid,
                    'config_id': self.id,
                    'meter_1_start': closed_session[0].meter_1_end,
                    'meter_2_start': closed_session[0].meter_2_end,
                    'meter_3_start': closed_session[0].meter_3_end,
                    'meter_4_start': closed_session[0].meter_4_end,
                    'meter_5_start': closed_session[0].meter_5_end,
                    'meter_6_start': closed_session[0].meter_6_end,
                    'meter_7_start': closed_session[0].meter_7_end,
                    'meter_8_start': closed_session[0].meter_8_end,
                    'meter_9_start': closed_session[0].meter_9_end,
                    'meter_10_start': closed_session[0].meter_10_end,
                })
                if self.current_session_id.state == 'opened':
                    return self._open_session(self.current_session_id.id)
                return self._open_session(self.current_session_id.id)
            return self._open_session(self.current_session_id.id)
        else:
            res = super(PosConfig, self).open_session_cb()
            return res


class account_journal(models.Model):
    _inherit = 'account.journal'

    wallet_journal = fields.Boolean(string="Wallet Journal")

    @api.onchange('wallet_journal')
    def _onchange_wallet_journal(self):
        for pm in self:
            if pm.wallet_journal:
                pm.type = 'bank'
                pm.journal_user = True
            if not pm.wallet_journal:
                pm.journal_user = False




