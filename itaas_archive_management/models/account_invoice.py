# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from datetime import date, datetime
from odoo.tools import float_compare, float_is_zero, UserError


class Account_invoice_auto_create(models.Model):
    _inherit = 'account.invoice'


    ref_sh = fields.Char('Ref SH')


    def action_copy_invoice(self):
        print('action_copy_invoice')
        account_move_obj = self.env['account.invoice']
        account_move_line_obj = self.env['account.invoice.line']
        company_id = self.env['res.company'].sudo().search([('name', '=','ดีลเลอร์ วิชาร์ด')])
        operating_id = self.env['operating.unit'].sudo().search([('id', '=',company_id.id),('show_invoice','=',True)],limit=1)
        journal_id = self.env['account.journal'].sudo().search([('company_id','=',company_id.id)],limit=1)
        print('company_id:',company_id.id)
        print('journal_id:',journal_id)
        print('operating_id:',operating_id.id)
        print('operating_id:',operating_id.name)
        vals={
            'partner_id': self.partner_id.id,
            'journal_id': journal_id.id,
            'sale_type_id' : self.sale_type_id.id,
            'currency_id': self.currency_id.id,
            'company_id': company_id.id,
            'operating_unit_id:':operating_id.id,
            'ref_sh': self.number

        }
        account_move = account_move_obj.sudo().create(vals)
        for line in self.invoice_line_ids:
            account_dealer = self.env['account.account'].sudo().search([('code', '=', line.product_id.categ_id.property_account_income_categ_id.code),('company_id','=',company_id.id)],limit=1)
            print('account_dealer:',account_dealer)
            print('line',line.product_id)
            print('line',line.product_id.categ_id)
            vals_line={
                'invoice_id': account_move.id,
                'product_id':line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'uom_id': line.uom_id.id,
                'account_id': account_dealer.id,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'discount_amount':line.discount_amount,
                'invoice_line_tax_ids': [(6,0,line.invoice_line_tax_ids.ids)],
                'price_subtotal':line.price_subtotal,
                'price_total':line.price_total,

            }
            account_move_line = account_move_line_obj.sudo().create(vals_line)
            print('account_move:', account_move)
            print('account_move_line:', account_move_line)



