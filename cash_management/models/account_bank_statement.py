# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime, date

class pos_order_inherit(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def update_notes(self):
        pos = self.env['pos.order'].search([])
        print('pos:',pos)
        print('xxxxxxxxxxx')
        for pos_id in pos:
            if pos_id.note:
                for line in pos_id.statement_ids:
                    line.note = pos_id.note

    # @api.model
    # def create(self, values):
    #     journal_id = values.get('is_not_post')
    #     if not values.get('is_not_post') and
    #
    #     res = super(pos_order_inherit, self).create(values)
    #     return res

class pos_session_inherit(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_closing_control(self):
        for line_ids in self.order_ids:
            for line_id in line_ids.statement_ids:
                line_id.note = line_ids.note


        return super(pos_session_inherit, self).action_pos_session_closing_control()





class account_cheque_statement(models.Model):
    _inherit = 'account.cheque.statement'

    is_done = fields.Boolean(string='นำฝากแล้ว',default=False)
    account_voucher_id = fields.Many2one('account.voucher', string='หมายเลขใบนำฝาก')


class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    is_done = fields.Boolean(string='นำฝากแล้ว',default=False)
    pos_config = fields.Many2one('pos.config',related='pos_statement_id.config_id',store=True)
    account_voucher_id = fields.Many2one('account.voucher',string='หมายเลขใบนำฝาก',store=True)

    voucher_copy = fields.Many2one('account.voucher',string="Copy",store=True , related="account_voucher_id")




class account_bank_statement(models.Model):
    _inherit = 'account.bank.statement'

    is_done = fields.Boolean(string='นำฝากแล้ว',default=False)
    pos_config = fields.Many2one('pos.config',compute='get_pos_config',store=True)
    account_voucher_id = fields.Many2one('account.voucher',string='หมายเลขใบนำฝาก')

    @api.depends('pos_session_id')
    def get_pos_config(self):
        for statement in self:
            if statement.pos_session_id:
                statement.pos_config = statement.pos_session_id.config_id



class bank_statement_account_voucher(models.TransientModel):
    _name = 'bank.statement.account.voucher'


    post_date = fields.Date(string='วันที่นำฝาก')
    journal_id = fields.Many2one('account.journal',string='สมุดบัญชีนำฝาก')
    is_existing_voucher = fields.Boolean(string='Existing Voucher',default=False)
    existing_voucher_id = fields.Many2one('account.voucher',string='รายการ Voucher เดิม')

    ################# from bank statement line #################
    @api.multi
    def confirm_order(self):
        print('confirm_order')
        active_model = self._context.get('active_model', [])
        print ('--MODEL')
        print (active_model)

        if active_model == 'account.bank.statement.line':
            bank_statement_line_ids = self.env['account.bank.statement.line'].browse(
                self._context.get('active_ids', []))
            if self.journal_id:
                journal_id = self.journal_id
            else:
                if bank_statement_line_ids:
                    journal_id = bank_statement_line_ids[0].journal_id
                else:
                    raise UserError(_("Please select at least one record"))

                if any(journal_id != statement_id_line.journal_id for statement_id_line in bank_statement_line_ids):
                    raise UserError(_("Please select record of the same journal"))

                if not journal_id.bank_for_cheque_account_id.id:
                    raise UserError(_("Please setup journal to define account for money in"))
            if not self.existing_voucher_id:
                print('not existing_voucher_id')
                val_voucher = {
                    'journal_id': journal_id.id,
                    'date': self.post_date or datetime.today().date(),
                    'account_date': self.post_date or datetime.today().date(),
                    'pay_now': 'pay_now',
                    'payment_journal_id': journal_id.id,
                    'voucher_type': 'sale',
                    'voucher_type_new': 'normal',
                    'account_id': journal_id.bank_for_cheque_account_id.id,
                }
                voucher_id = self.env['account.voucher'].create(val_voucher)
            else:
                print('Sssssssss')
                voucher_id = self.existing_voucher_id

            to_do_statement_line_ids = bank_statement_line_ids.filtered(lambda x: x.is_done != True)

            if not to_do_statement_line_ids:
                raise UserError(_("There is not record to process"))

            for statement_line_id in to_do_statement_line_ids:
                print('xxxxxxxxxx')
                department_id = False
                if statement_line_id.pos_config.branch_id and statement_line_id.pos_config.branch_id.analytic_account_id:
                    department_id = self.env['hr.department'].sudo().search([('analytic_account_id','=',statement_line_id.pos_config.branch_id.analytic_account_id.id)],limit=1)


                # if department_id:


                val_line = {
                    'name': statement_line_id.pos_config.name,
                    'account_id': journal_id.default_credit_account_id.id,
                    'operating_unit_id': statement_line_id.pos_config.operating_branch_id.id,
                    'department_id': department_id.id if department_id else False,
                    'quantity': 1,
                    'bill_ref': statement_line_id.ref,
                    'bill_date': statement_line_id.date,
                    'note': statement_line_id.note,
                    'price_unit': statement_line_id.amount,
                    'voucher_id': voucher_id.id,
                }
                self.env['account.voucher.line'].create(val_line)
                statement_line_id.update(
                    {
                        'account_voucher_id': voucher_id.id,
                        'is_done': True,
                    }
                )
        else:
            print('Else')
            ############ This is from cheque ####
            bank_statement_line_ids = self.env['account.cheque.statement'].browse(
                self._context.get('active_ids', []))
            if self.journal_id:
                journal_id = self.journal_id
            else:
                if bank_statement_line_ids:
                    journal_id = bank_statement_line_ids[0].journal_id
                else:
                    raise UserError(_("Please select at least one record"))

                if any(journal_id != statement_id_line.journal_id for statement_id_line in bank_statement_line_ids):
                    raise UserError(_("Please select record of the same journal"))

                if not journal_id.bank_for_cheque_account_id.id:
                    raise UserError(_("Please setup journal to define account for money in"))

            if not self.existing_voucher_id:
                print('NOT existing_voucher_id')
                val_voucher = {
                    'journal_id': journal_id.id,
                    'date': self.post_date or datetime.today().date(),
                    'account_date': self.post_date or datetime.today().date(),
                    'pay_now': 'pay_now',
                    'payment_journal_id': journal_id.id,
                    'voucher_type': 'sale',
                    'voucher_type_new': 'normal',
                    'account_id': journal_id.bank_for_cheque_account_id.id,
                }
                voucher_id = self.env['account.voucher'].create(val_voucher)
            else:
                print('existing_voucher_id:xxxxxx')
                voucher_id = self.existing_voucher_id

            to_do_statement_line_ids = bank_statement_line_ids.filtered(lambda x: x.is_done != True)
            # to_do_statement_line_ids = bank_statement_line_ids

            if not to_do_statement_line_ids:
                raise UserError(_("There is not record to process"))



            for statement_line_id in to_do_statement_line_ids:
                ou_id = self.env['operating.unit'].search([('partner_id', '=', statement_line_id.partner_id.id)], limit=1)
                val_line = {
                    'name': statement_line_id.partner_id.name,
                    'account_id': journal_id.default_credit_account_id.id,
                    'operating_unit_id': ou_id and ou_id.id or False,
                    'pay_now': 'pay_now',
                    'bill_ref': '',
                    'note': '',
                    'quantity': 1,
                    'price_unit': statement_line_id.amount,
                    'voucher_id': voucher_id.id,
                }
                self.env['account.voucher.line'].create(val_line)
                statement_line_id.update(
                    {
                        'account_voucher_id': voucher_id.id,
                        'is_done': True,
                        'state': 'confirm',
                    }
                )
        view_id = self.env.ref('account_voucher.view_sale_receipt_form').id
        return {
            'name': voucher_id.name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.voucher',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'res_id': voucher_id.id,
        }

    ################# from bank statement #################
    # @api.multi
    # def confirm_order(self):
    #     bank_statement_ids = self.env['account.bank.statement'].browse(self._context.get('active_ids', []))
    #
    #
    #     if bank_statement_ids:
    #         journal_id = bank_statement_ids[0].journal_id
    #     else:
    #         raise UserError(_("Please select at least one record"))
    #
    #     if any(journal_id != statement_id.journal_id for statement_id in bank_statement_ids):
    #         raise UserError(_("Please select record of the same journal"))
    #
    #     if not journal_id.bank_for_cheque_account_id.id:
    #         raise UserError(_("Please setup journal to define account for money in"))
    #
    #     val_voucher = {
    #         'journal_id': journal_id.id,
    #         'pay_now': 'pay_now',
    #         'payment_journal_id': journal_id.id,
    #         'voucher_type': 'sale',
    #         'voucher_type_new': 'normal',
    #         'account_id': journal_id.bank_for_cheque_account_id.id,
    #     }
    #     voucher_id = self.env['account.voucher'].create(val_voucher)
    #
    #     to_do_statement_ids = bank_statement_ids.filtered(lambda x: x.is_done != True)
    #
    #     if not to_do_statement_ids:
    #         raise UserError(_("There is not record to process"))
    #
    #     for statement_id in to_do_statement_ids:
    #         val_line = {
    #             'name': statement_id.name,
    #             'account_id':journal_id.default_credit_account_id.id,
    #             'operating_unit_id': statement_id.pos_config.operating_branch_id.id,
    #             'quantity': 1,
    #             'price_unit': statement_id.total_entry_encoding,
    #             'voucher_id': voucher_id.id,
    #         }
    #         self.env['account.voucher.line'].create(val_line)
    #         statement_id.update(
    #             {
    #                 'account_voucher_id': voucher_id.id,
    #                 'is_done': True,
    #              }
    #         )
    #
    #     view_id = self.env.ref('account_voucher.view_sale_receipt_form').id
    #     return {
    #         'name': voucher_id.name,
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'account.voucher',
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'view_id': view_id,
    #         'views': [(view_id, 'form')],
    #         'res_id': voucher_id.id,
    #     }

