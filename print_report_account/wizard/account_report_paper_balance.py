# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError

class AccountPaperBalanceReport(models.TransientModel):
    _inherit = "account.common.account.report"
    _name = 'account.paperbalance.report'
    _description = 'Paper Balance Report'

    journal_ids = fields.Many2many('account.journal', 'account_balance_report_journal_rel', 'account_id', 'journal_id', string='Journals', required=True, default=[])
    is_first_year = fields.Boolean(string='First Year')


    def left(self, s, amount):
        return str(s)[:amount]

    def right(self, s, amount):
        return str(s)[-amount:]

    def get_currency_year_earning(self):
        cye_id = self.env['account.account.type'].search([('name','=','Current Year Earnings')],limit=1)
        if cye_id:
            account_id = self.env['account.account'].search([('user_type_id','=',cye_id.id)],limit=1)
            if not account_id:
                raise UserError(_('There is no current year earning account.'))
        else:
            raise UserError(_('There is no current year earning account.'))

        # print "account"
        # print account_id.name
        # print account_id.code
        return account_id

    @api.model
    def default_get(self, fields):
        res = super(AccountPaperBalanceReport, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, 1, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        res.update({'date_from': str(from_date), 'date_to': str(to_date)})
        return res

    def _print_report(self, data):
        data = self.pre_print_report(data)
        #print "222222222"
        records = self.env[data['model']].browse(data.get('ids', []))
        # return self.env['report'].get_action(records, 'print_report_account.report_paperbalance', data=data)

        return self.env.ref('print_report_account.action_report_paperbalance').report_action(records, data=data)

