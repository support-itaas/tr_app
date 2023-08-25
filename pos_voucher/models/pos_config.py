# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import ast
import logging
from odoo.exceptions import UserError
import base64
import json

_logger = logging.getLogger(__name__)


class pos_config(models.Model):
    _inherit = "pos.config"

    print_voucher = fields.Boolean('Create voucher', default=0)
    scan_voucher = fields.Boolean('Scan voucher', default=0)
    expired_days_voucher = fields.Integer('Expired days of voucher', default=30,
                                          help='Total days keep voucher can use, if out of period days from create date, voucher will expired')

    def init_voucher_journal(self):
        Journal = self.env['account.journal']
        user = self.env.user
        voucher_journal = Journal.sudo().search([
            ('code', '=', 'VCJ'),
            ('company_id', '=', user.company_id.id),
        ])
        if voucher_journal:
            return voucher_journal.sudo().write({
                'pos_method_type': 'voucher'
            })
        Account = self.env['account.account']
        voucher_account_old_version = Account.sudo().search([
            ('code', '=', 'AVC'), ('company_id', '=', user.company_id.id)])
        if voucher_account_old_version:
            voucher_account = voucher_account_old_version[0]
        else:
            voucher_account = Account.sudo().create({
                'name': 'Account voucher',
                'code': 'AVC',
                'user_type_id': self.env.ref('account.data_account_type_current_assets').id,
                'company_id': user.company_id.id,
                'note': 'code "AVC" auto give voucher histories of customers',
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'account_voucher' + str(user.company_id.id),
                'model': 'account.account',
                'module': 'pos_retail',
                'res_id': voucher_account.id,
                'noupdate': True,  # If it's False, target record (res_id) will be removed while module update
            })

        voucher_journal = Journal.sudo().search([
            ('code', '=', 'VCJ'),
            ('company_id', '=', user.company_id.id),
            ('pos_method_type', '=', 'voucher')
        ])
        if voucher_journal:
            voucher_journal[0].sudo().write({
                'voucher': True,
                'default_debit_account_id': voucher_account.id,
                'default_credit_account_id': voucher_account.id,
                'pos_method_type': 'voucher',
                'sequence': 101,
            })
            voucher_journal = voucher_journal[0]
        else:
            new_sequence = self.env['ir.sequence'].sudo().create({
                'name': 'Account Voucher ' + str(user.company_id.id),
                'padding': 3,
                'prefix': 'AVC ' + str(user.company_id.id),
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'journal_sequence' + str(new_sequence.id),
                'model': 'ir.sequence',
                'module': 'pos_retail',
                'res_id': new_sequence.id,
                'noupdate': True,
            })
            voucher_journal = Journal.sudo().create({
                'name': 'Voucher',
                'code': 'VCJ',
                'type': 'cash',
                'pos_method_type': 'voucher',
                'journal_user': True,
                'sequence_id': new_sequence.id,
                'company_id': user.company_id.id,
                'default_debit_account_id': voucher_account.id,
                'default_credit_account_id': voucher_account.id,
                'sequence': 101,
            })
            self.env['ir.model.data'].sudo().create({
                'name': 'journal_voucher_' + str(voucher_journal.id),
                'model': 'account.journal',
                'module': 'pos_retail',
                'res_id': int(voucher_journal.id),
                'noupdate': True,
            })

        config = self
        config.sudo().write({
            'journal_ids': [(4, voucher_journal.id)],
        })

        statement = [(0, 0, {
            'journal_id': voucher_journal.id,
            'user_id': user.id,
            'company_id': user.company_id.id
        })]
        current_session = config.current_session_id
        current_session.sudo().write({
            'statement_ids': statement,
        })
        return

    @api.multi
    def open_ui(self):
        res = super(pos_config, self).open_ui()
        self.init_voucher_journal()
        return res

    @api.multi
    def open_session_cb(self):
        res = super(pos_config, self).open_session_cb()
        self.init_voucher_journal()
        return res
