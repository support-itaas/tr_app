# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class pos_session(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def fix_more_payment_online(self):
        pos_config = self.config_id
        ABS = self.env['account.bank.statement']
        ctx = dict(self.env.context, company_id=pos_config.company_id.id)
        pos_name = self.name
        uid = SUPERUSER_ID if self.env.user.has_group('point_of_sale.group_pos_user') else self.env.user.id

        journal_ids = []
        for statement in self.statement_ids:
            if statement.journal_id not in journal_ids:
                journal_ids.append(statement.journal_id)

        for journal in pos_config.journal_ids:
            if journal not in journal_ids:
                # set the journal_id which should be used by
                # account.bank.statement to set the opening balance of the
                # newly created bank statement
                print (journal.name)
                ctx['journal_id'] = journal.id if pos_config.cash_control and journal.type == 'cash' else False
                st_values = {
                    'journal_id': journal.id,
                    'user_id': self.env.user.id,
                    'name': pos_name,
                    'pos_session_id': self.id,
                }

                ABS.with_context(ctx).sudo(uid).create(st_values)
        ############Fix Error All the account entries lines must be processed in order to close the statement.###
        for statement in self.statement_ids:
            line_no_account_id_ids = statement.line_ids.filtered(lambda x: not x.account_id)
            ########if has some account missing account_id, then update it
            if line_no_account_id_ids:
                ######### find reference account to update on missing line
                line_account_id_ids = statement.line_ids.filtered(lambda x: x.account_id)
                if line_account_id_ids:
                    ########### Update missing line
                    line_no_account_id_ids.write({'account_id': line_account_id_ids[0].account_id.id})
                else:
                    ########## if could not find reference account then looking for another first statement, hope it has, if not raise an user error
                    line_account_id_ids = self.statement_ids[0].line_ids.filtered(lambda x: x.account_id)
                    if line_account_id_ids:
                        line_no_account_id_ids.write({'account_id': line_account_id_ids[0].account_id.id})
                    else:
                        raise UserError(
                            _('Please check with admin'))



class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    payment_date = fields.Date(string='Payment Date')

    @api.multi
    def check(self):
        """Check the order:
        if the order is not paid: continue payment,
        if the order is paid print ticket.
        """
        self.ensure_one()
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        currency = order.pricelist_id.currency_id
        amount = order.amount_total - order.amount_paid
        data = self.read()[0]
        # add_payment expect a journal key
        data['journal'] = data['journal_id'][0]
        data['amount'] = currency.round(data['amount']) if currency else data['amount']
        data['payment_date'] = data['payment_date']

        if not float_is_zero(amount, precision_rounding=currency.rounding or 0.01):
            order.add_payment(data)
        if order.test_paid():
            order.action_pos_order_paid()
            return {'type': 'ir.actions.act_window_close'}
        return self.launch_payment()