# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
from datetime import datetime
from odoo.exceptions import UserError

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))
class report_sale_tax_report(models.AbstractModel):
    _name = 'report.thai_accounting.sale_tax_report_id'

    def get_amount_multi_currency(self,move_id):
        total_amount = 0.0
        tax_amount = 0.0
        for line in move_id.line_ids:
            total_amount += abs(line.debit)
            if line.account_id.sale_tax_report:
                tax_amount += abs(line.balance)
        return total_amount, tax_amount

    @api.model
    def get_report_values(self, docids, data=None):
        print('get_report_values:')
        print('data:',data)
        invoice_all = []
        domain_pos = []
        vals = {}
        pos_session_obj = self.env['pos.session']

        company_id = self.env.user.company_id
        operating_unit_id = False
        docs = False
        step = self.env.user.company_id.invoice_step
        if self.env.user.company_id.invoice_step == '1step':
            if data['form']['operating_unit_id']:
                operating_unit_id = self.env['operating.unit'].browse(data['form']['operating_unit_id'][0])
                if not data['form']['include_no_vat']:
                    domain = [('type', 'in', ('out_invoice', 'out_refund')), ('number', '!=', False),
                              ('state', '!=', 'draft')]
                else:
                    domain = [('type', 'in', ('out_invoice', 'out_refund')), ('number', '!=', False),
                              ('state', '!=', 'draft')]
                if data['form']['tax_id']:
                    domain.append(('tax_id', '=', data['form']['tax_id'][0]))
                else:
                    domain.append(('tax_id.tax_report', '=', True))

                domain.append(('date_invoice', '>=', data['form']['date_from']))
                domain.append(('date_invoice', '<=', data['form']['date_to']))
                domain.append(('operating_unit_id', '=', data['form']['operating_unit_id'][0]))
                docs = self.env['account.invoice'].search(domain, order='date_invoice,number asc')
            else:
                domain = [('type', 'in', ('out_invoice', 'out_refund')), ('number', '!=', False), ('state', '!=', 'draft')]
                if data['form']['tax_id']:
                    domain.append(('tax_id', '=', data['form']['tax_id'][0]))
                else:
                    domain.append(('tax_id.tax_report', '=', True))

                domain.append(('date_invoice', '>=', data['form']['date_from']))
                domain.append(('date_invoice', '<=', data['form']['date_to']))
                docs = self.env['account.invoice'].search(domain)
        else:
            if data['form']['operating_unit_id']:
                operating_unit_id = self.env['operating.unit'].browse(data['form']['operating_unit_id'][0])
                domain_pos.append(('config_id.operating_branch_id', '=', data['form']['operating_unit_id'][0]))
                domain_pos.append(('start_at', '>=', data['form']['date_from']))
                domain_pos.append(('stop_at', '<=', data['form']['date_to']))
                domain_pos.append(('is_ignore_account', '=', False))

                if not data['form']['include_no_vat']:
                    domain = [('type', 'in', ('out_invoice', 'out_refund')), ('tax_inv_generated', '=', True),
                              ('tax_inv_no', '!=', False),('state', '!=', 'draft')]
                else:
                    domain = [('type', 'in', ('out_invoice', 'out_refund')), ('tax_inv_generated', '=', True),
                              ('tax_inv_no', '!=', False),('state', '!=', 'draft')]
                if data['form']['tax_id']:
                    domain.append(('tax_id', '=', data['form']['tax_id'][0]))
                else:
                    domain.append(('tax_id.tax_report', '=', True))
                domain.append(('tax_inv_date', '>=', data['form']['date_from']))
                domain.append(('tax_inv_date', '<=', data['form']['date_to']))
                domain.append(('operating_unit_id', '=', data['form']['operating_unit_id'][0]))
                docs = self.env['account.invoice'].search(domain, order='tax_inv_date,tax_inv_no asc')
            else:
                if not data['form']['include_no_vat']:
                    domain = [('type', 'in', ('out_invoice', 'out_refund')), ('tax_inv_generated', '=', True),
                              ('tax_inv_no', '!=', False),('state', '!=', 'draft')]
                else:
                    domain = [('type', 'in', ('out_invoice', 'out_refund')), ('tax_inv_generated', '=', True),
                              ('tax_inv_no', '!=', False),('state', '!=', 'draft')]
                if data['form']['tax_id']:
                    domain.append(('tax_id', '=', data['form']['tax_id'][0]))
                else:
                    domain.append(('tax_id.tax_report', '=', True))
                domain_pos.append(('start_at', '>=', data['form']['date_from']))
                domain_pos.append(('stop_at', '<=', data['form']['date_to']))
                domain_pos.append(('is_ignore_account', '=', False))
                domain.append(('tax_inv_date', '>=', data['form']['date_from']))
                domain.append(('tax_inv_date', '<=', data['form']['date_to']))
                docs = self.env['account.invoice'].search(domain, order='tax_inv_date,tax_inv_no asc')
        print('domain:',domain)
        print('docs:',docs)
        check_tax_inv = []
        inv_total = []
        for invoice_id in docs:
            if self.env.user.company_id.invoice_step == '1step':
                date = invoice_id.date_invoice
                name = invoice_id.number
            else:
                print('invoice_id:',invoice_id)
                if invoice_id.tax_inv_no not in check_tax_inv:
                    print('invoice_id_inLoop:',invoice_id)
                    sum_untaxed = sum_amount_tax = sum_amount_total = 0
                    print('invoice_id.tax_inv_no:', invoice_id.tax_inv_no)
                    check_tax_inv.append(invoice_id.tax_inv_no)
                    sum_untaxed = invoice_id.amount_untaxed
                    sum_amount_tax = invoice_id.amount_tax
                    sum_amount_total = invoice_id.amount_total
                    invoice_number = invoice_id.number
                    date = invoice_id.tax_inv_date
                    name = invoice_id.tax_inv_no
                    if invoice_id.discount_value:
                        sum_untaxed -= invoice_id.discounted_amount

                    if invoice_id.partner_id.parent_id:
                        partner = invoice_id.partner_id.parent_id
                        vat = invoice_id.partner_id.parent_id.vat
                    else:
                        partner = invoice_id.partner_id
                        vat = invoice_id.partner_id.vat
                    if invoice_id.partner_id:
                        is_branch_no = invoice_id.partner_id.branch_no
                    else:
                        is_branch_no = invoice_id.move_id.supplier_branch_text
                    vals = {
                        'date': date or '',
                        'name': name or '',
                        'partner_id': partner,
                        'vat': vat,
                        'is_branch_no': is_branch_no,
                        'move_id': invoice_id.move_id,
                        'adjust_move_id': invoice_id.adjust_move_id,
                        'state': invoice_id.state,
                        'currency_id': invoice_id.currency_id,
                        'type': invoice_id.type,
                        'amount_untaxed': sum_untaxed,
                        'amount_tax': sum_amount_tax,
                        'amount_total': sum_amount_total,
                        'state': invoice_id.state,
                        'currency_id': invoice_id.currency_id,
                        'type': invoice_id.type,
                        'is_skip_gl': invoice_id.is_skip_gl,
                        'adjust_move_id': invoice_id.adjust_move_id,
                        'move_id': invoice_id.move_id,
                        'operating_unit_id': invoice_id.operating_unit_id,
                        'invoice': invoice_id.number,
                    }
                    invoice_all.append(vals)

                else:
                    print('invoice_id.tax_inv_noนนนน:',invoice_id.tax_inv_no)
                    print('invoice_id.amount_tax:',invoice_id.amount_tax)
                    print('sum_amount_tax:',sum_amount_tax)
                    sum_untaxed += invoice_id.amount_untaxed
                    sum_amount_tax += invoice_id.amount_tax
                    sum_amount_total += invoice_id.amount_total
                    invoice_number += '  ' + invoice_id.number

                    if invoice_id.discount_value:
                        sum_untaxed -= invoice_id.discounted_amount


                    if vals['name'] == invoice_id.tax_inv_no:
                        vals.update({
                            'amount_untaxed':sum_untaxed,
                            'amount_tax':sum_amount_tax,
                            'amount_total':sum_amount_total,
                            'invoice':invoice_number,
                        })
        print('invoice_all',invoice_all)
        invoice_all.sort(key=lambda k: (k['date'], k['name']), reverse=False)
        pos_session_ids = pos_session_obj.search(domain_pos, order='start_at')
        print('pos_session_ids:',pos_session_ids)
        print('len:',len(pos_session_ids))
        # print "DOCS"
        print (operating_unit_id)
        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs': invoice_all,
            'company_id': company_id,
            'operating_unit_id': operating_unit_id,
            'data': data['form'],
            'step': step,
            'pos' : pos_session_ids
        }



#start This is to generate purchase tax report
class report_purchase_tax_report(models.AbstractModel):
    _name = 'report.thai_accounting.purchase_tax_report_id'


    @api.model
    def get_report_values(self, docids, data=None):
        print('get_report_values')
        vals = {}
        invoice_all = []
        company_id = self.env.user.company_id
        #############################  Case 1 #####################################
        print('#############################  Case 1 #####################################')
        domain =[('is_closing_month','=',False)]
        # domain = []
        if data['form']['tax_id']:
            account_id = self.env['account.tax'].browse(data['form']['tax_id'][0]).account_id
            domain.append(('account_id', '=', account_id.id))
        else:
            domain.append(('account_id.purchase_tax_report', '=', True))

        if data['form']['date_from']:
            domain.append(('date', '>=', data['form']['date_from']))
        if data['form']['date_to']:
            domain.append(('date', '<=', data['form']['date_to']))

        print('Domain:',domain)
        if data['form']['operating_unit_id']:
            operating_unit_id = self.env['operating.unit'].browse(data['form']['operating_unit_id'][0])
            domain.append(('operating_unit_id', '=', data['form']['operating_unit_id'][0]))
        else:
            operating_unit_id = False

        docs = self.env['account.move.line'].search(domain)
        print('docs:',docs)
        docs = docs.filtered(lambda m: m.date_maturity == m.date)

        for invoice_id in docs:
            if not invoice_id.invoice_date:
                raise UserError(_("Please check date for item %s" % invoice_id.move_id.name))
            date = invoice_id.invoice_date
            # CASE OLD
            # if invoice_id.date_maturity:
            #     date = invoice_id.date_maturity
            # elif not invoice_id.date_maturity and invoice_id.invoice_date:
            #     date = invoice_id.invoice_date
            # else:
            #     date = invoice_id.date
            name = invoice_id.ref
            if invoice_id.partner_id:
                partner = invoice_id.partner_id
                vat = invoice_id.partner_id.vat
                is_branch_no = invoice_id.partner_id.branch_no
            else:
                partner = invoice_id.move_id.supplier_name_text
                vat = invoice_id.move_id.supplier_taxid_text
                is_branch_no = invoice_id.move_id.supplier_branch_text

            vals = {
                'date': date or '',
                'name': name or '',
                'partner_id': partner,
                'vat': vat,
                'is_branch_no': is_branch_no,
                'invoice_id': invoice_id.invoice_id,
                'debit': invoice_id.debit,
                'credit': invoice_id.credit,
                'amount_before_tax': invoice_id.amount_before_tax,
                'move_id': invoice_id.move_id,
                'balance': invoice_id.balance,

            }
            invoice_all.append(vals)
        invoice_all.sort(key=lambda k: (k['date'], k['name']), reverse=False)
        print (docs)
        #############################  Case 2 #####################################
        print('###################### Case 2 ###############################')
        domain = [('is_closing_month', '=', False)]
        if data['form']['tax_id']:
            account_id = self.env['account.tax'].browse(data['form']['tax_id'][0]).account_id
            domain.append(('account_id', '=', account_id.id))
        else:
            domain.append(('account_id.purchase_tax_report', '=', True))

        if data['form']['date_from']:
            domain.append(('date_maturity', '>=', data['form']['date_from']))
        if data['form']['date_to']:
            domain.append(('date_maturity', '<=', data['form']['date_to']))

        print('Domain:', domain)
        if data['form']['operating_unit_id']:
            operating_unit_id = self.env['operating.unit'].browse(data['form']['operating_unit_id'][0])
            domain.append(('operating_unit_id', '=', data['form']['operating_unit_id'][0]))
        else:
            operating_unit_id = False

        docs = self.env['account.move.line'].search(domain)
        docs = docs.filtered(lambda m: m.date_maturity != m.date)
        for invoice_id in docs:
            date_maturity = datetime.strptime(invoice_id.date_maturity, '%Y-%m-%d')
            invoice_date = datetime.strptime(invoice_id.invoice_date, '%Y-%m-%d')

            date = invoice_id.invoice_date
            # if date_maturity.month != invoice_date.month:
            #     date = invoice_id.date_maturity
            # elif date_maturity.month == invoice_date.month:
            #     date = invoice_id.invoice_date
            # else:
            #     date = invoice_id.date
            name = invoice_id.ref
            if invoice_id.partner_id:
                partner = invoice_id.partner_id
                vat = invoice_id.partner_id.vat
                is_branch_no = invoice_id.partner_id.branch_no
            else:
                partner = invoice_id.move_id.supplier_name_text
                vat = invoice_id.move_id.supplier_taxid_text
                is_branch_no = invoice_id.move_id.supplier_branch_text

            vals = {
                'date': date or '',
                'name': name or '',
                'partner_id': partner,
                'vat': vat,
                'is_branch_no': is_branch_no,
                'invoice_id': invoice_id.invoice_id,
                'debit': invoice_id.debit,
                'credit': invoice_id.credit,
                'amount_before_tax': invoice_id.amount_before_tax,
                'move_id': invoice_id.move_id,
                'balance': invoice_id.balance,

            }
            invoice_all.append(vals)
        invoice_all.sort(key=lambda k: (k['date'], k['name']), reverse=False)
        print(docs)
        print('###################### Case 2 ###############################')
        return {
            'doc_ids': docids,
            'doc_model': 'account.invoice',
            'docs': invoice_all,
            'company_id': company_id,
            'operating_unit_id': operating_unit_id,
            'data': data['form'],
        }
