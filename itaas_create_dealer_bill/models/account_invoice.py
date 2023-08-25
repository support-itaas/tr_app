# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import models, fields, api ,_
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    check_dealer_bill = fields.Boolean('Check Dealer Bill', default=False, copy=False)

    @api.multi
    def action_create_bill(self,):
        print('self', self)

        company = self.env['res.company'].sudo().search([('id', '=', 5)], limit=1)
        journal = self.env['account.journal'].sudo().search([('relation_journal', '=', self.journal_id.relation_journal),
                                                             ('company_id', '=', company.id)], limit=1)
        if not journal:
            raise UserError(_('Please Set Journal Relation %s') % (self.journal_id.name))

        operating_unit = self.env['operating.unit'].sudo().search([('id', '=', 5)], limit=1)
        account = self.env['account.account'].sudo().search([('relation_account', '=', self.account_id.relation_account),
                                                             ('company_id', '=', company.id)], limit=1)

        # print('company ',company.name)
        # print('journal ',journal.name)
        # print('operating_unit_id ',operating_unit.name)
        # print('operating_unit_id company_id ',operating_unit.company_id.name)

        new_invoice_id = self.sudo().copy({'company_id': company.id,
                                           'operating_unit_id': 5,
                                           'journal_id': journal.id,
                                           'type': 'in_invoice',
                                           'partner_id': self.company_id.partner_id.id,
                                           'account_id': journal.default_credit_account_id.id,
                                           'reference': self.number,
                                           'tax_line_ids': False,
                                           'invoice_line_ids': False,
                                           })
        price_total=[]
        for line in self.invoice_line_ids:
            account = self.env['account.account'].sudo().search([('relation_account', '=', line.account_id.relation_account),
                                                                 ('company_id', '=', company.id)], limit=1)
            if not account:
                raise UserError(_('Please Set Account Relation %s') % (self.account_id.name))

            tax_rate = list(set(line.invoice_line_tax_ids.mapped('amount')))
            if tax_rate:
                tax_rate = tax_rate[0]
                if tax_rate:
                    price_total = line.price_subtotal + (line.price_subtotal * (tax_rate/100))
                    price_unit = price_total / line.quantity
                else:
                    price_unit = line.price_unit
            else:
                price_unit = line.price_unit

            val_line = {
                'invoice_id': new_invoice_id.id,
                'product_id': line.product_id.id,
                'name': line.name,
                'account_id': account.id,
                'quantity': line.quantity,
                'invoice_line_tax_ids': False,
                'price_unit': price_unit,
            }
            self.env['account.invoice.line'].sudo().create(val_line)

        # for line in new_invoice_id.invoice_line_ids:
        #     account = self.env['account.account'].sudo().search([('relation_account', '=', line.account_id.relation_account),
        #                                                          ('company_id', '=', company.id)], limit=1)
        #     if not account:
        #         raise UserError(_('Please Set Account Relation %s') % (self.account_id.name))
        #
        #     tax = line.product_id.supplier_taxes_id
        #     price_total = line.price_subtotal + (line.price_subtotal * 0.07)
        #     price_unit = price_total / line.quantity
        #     line.sudo().write({
        #         'account_id': account.id,
        #         # 'invoice_line_tax_ids': [(6, 0, line.product_id.supplier_taxes_id.ids)],
        #         'invoice_line_tax_ids': False,
        #         'price_total': price_total,
        #         'price_unit': price_unit,
        #     })

        print('---new_invoice_id:', new_invoice_id)
        if new_invoice_id:
            print('log')
            # message = ("Create Dealer Bill Name %s %s") % (new_invoice_id.sudo().sequence_number_next_prefix, new_invoice_id.sudo().sequence_number_next)
            message = ("Create Dealer Bill ID %s ") % (new_invoice_id.sudo().id)
            self.message_post(body=message)
            self.check_dealer_bill = True

        return new_invoice_id


