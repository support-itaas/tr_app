# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    @api.multi
    def _get_default_invoice_step(self):
        #if company setting is done then get from compnay, otherwise set default to 2 step
        if self.env.user.company_id.invoice_step:
            return self.env.user.company_id.invoice_step
        else:
            # print self.env.user.company_id.payment_with_deduct
            return '2step'

    date_invoice = fields.Date(string='Invoice Date',index=True,readonly=False,help="Keep empty to use the current date", copy=False)
    reference = fields.Char(string='Vendor Reference',
                            help="The partner reference of this invoice.", readonly=True,
                            states={'draft': [('readonly', False)],'open': [('readonly', False)]})
    account_note = fields.Text(string='Note for Account', readonly=True, states={'draft': [('readonly', False)]},copy=False ,size=120)
    tax_inv_no = fields.Char(string='Tax Invoice No.', readonly=True, copy=False)
    tax_inv_date = fields.Date(string='Tax Invoice Date', help='Tax Invoice Number generated date.', copy=False)
    tax_inv_generated = fields.Boolean(string='Tax Invoice Generated', default=False, copy=False)

    multi_so = fields.Boolean(string='Multiple Sales Order', default=False)
    sale_id = fields.Many2one('sale.order', string='Add Sales Order',
                              help='Encoding help. When selected, the associated sales order lines are added to the customer invoice. Several SO can be selected.')
    adjust_move_id = fields.Many2one('account.move', string="Tax Journal Entry", copy=False)
    adjust_require = fields.Boolean(string="Tax Adjust Require", default=False)
    contact_person = fields.Many2one('res.partner',string="Contact Person")
    bill_date = fields.Date(string='Schedule Bill Date',copy=False)
    bill_date_str = fields.Char(string='Schedule Bill Date', compute='_get_string_date', store=True, copy=False)
    invoice_step = fields.Selection([('1step', 'Invoice/Tax Invoice'), ('2step', 'Invoice--->Tax Invoice')],
                                    default=lambda self: self.env.user.company_id.invoice_step,
                                    help='1step is invoice and tax invoice is the same, 2 step is invoice and tax invoice is difference number')
    readonly_date_invoice = fields.Boolean(string='Readonly Date Invoice',
                                           default=lambda self: self.env.user.company_id.readonly_date_invoice)
    allow_invoice_backward = fields.Boolean(string='Allow Record Invoice Backward',
                                            default=lambda self: self.env.user.company_id.allow_invoice_backward)
    is_skip_gl = fields.Boolean(string='New Invoice Without GL',copy=False)
    is_skip_gl_original = fields.Boolean(string='Invoice Without GL Original', copy=False)
    original_date_inv_skip_gl = fields.Date(string='Original Date Invoice',copy=False)
    print_tax_invoice = fields.Boolean(string='พิมพ์ใบกำกับภาษีแล้ว',copy=False)
    print_credit_note = fields.Boolean(string='พิมพ์ใบลดหนี้/ใบกำกับภาษีแล้ว',copy=False)
    print_debit_note = fields.Boolean(string='พิมพ์ใบเพิ่มหนี้/ใบกำกับภาษีแล้ว',copy=False)
    debit_note = fields.Boolean(string='Debit Note', copy=False)
    reference_later = fields.Boolean(string='Receive Tax Invoice Later',copy=False)

    #############for credit note only ###########
    is_manual_cn = fields.Boolean(string='Manual CN',default=False)
    ref_tax_invoice_number = fields.Char(string='Ref Inv')
    ref_tax_invoice_date = fields.Date(string='Ref Inv Date')
    ref_tax_invoice_amount = fields.Float(string='Ref Inv Amt')
    #############for credit note only ###########

    ############### for company which can issue with tax or none-tax
    tax_id = fields.Many2one('account.tax',string='Tax ID',compute='_get_tax_id',store=True)


    #################################################################

    # @api.depends('date_invoice')
    # def onchange_date_invoice(self):
    #     print "xxx"
    #     for invoice in self:
    #         if invoice.date_invoice and invoice.type in ('in_invoice','in_refund'):
    #             print "yyyy"
    #             if strToDate(invoice.date_invoice) > datetime.today():
    #                 raise UserError(_("Invoice Date should be today or before"))
    #             else:
    #                 print "zzz"
    #         else:
    #             print "uuuu"

    @api.multi
    def _get_aml_for_register_payment(self):
        """ Get the aml to consider to reconcile in register payment """
        self.ensure_one()
        return self.move_id.line_ids.filtered(
            lambda r: not r.reconciled and r.account_id.reconcile and r.account_id.internal_type in ('payable', 'receivable'))

    @api.depends('invoice_line_ids')
    def _get_tax_id(self):
        for inv in self:
            if inv.invoice_line_ids and inv.invoice_line_ids[0].invoice_line_tax_ids:
                inv.tax_id = inv.invoice_line_ids[0].invoice_line_tax_ids[0].id
                if not inv.tax_id.tax_report:
                    inv.tax_id = self.env['account.tax'].search([('type_tax_use','=','sale'),('tax_report','=',True)],limit=1)


    @api.model
    def create(self, vals):
        tz_base = pytz.timezone('Asia/Bangkok')
        today = datetime.today()
        today = pytz.utc.localize(today, "%Y-%m-%d %H:%M:%S").astimezone(tz_base)

        if vals.get('date_invoice'):
            end_tax_date = strToDate(vals['date_invoice']) + relativedelta(months=+6)

            #last date of end tax month
            end_tax_date = date(end_tax_date.year, end_tax_date.month,
                                calendar.monthrange(end_tax_date.year, end_tax_date.month)[1])

            #invoie date should not allow in the future
            if not self.env.user.company_id.allow_invoice_backward and strToDate(vals['date_invoice']) > today.date():
                raise UserError(_("ใบกำกับภาษีไม่สามารถลงวันที่ล่วงหน้า"))

            #if last day end tax month pass then alert
            if not self.env.user.company_id.allow_invoice_backward and end_tax_date < today.date():
                raise UserError(_("ใบกำกับภาษีฉบับนี้เกิน 6 เดือนรอบภาษี"))


        if vals.get('date'):
            print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxaaaaaa')
            #date should be in last day end tax month but can't before start date of today month
            date_inv = strToDate(vals['date'])
            tax_month_date = date(today.year, today.month, 1)
            print('date_inv:',date_inv)
            print('tax_month_date:',tax_month_date)
            print('today.date():',today.date())

            if not self.env.user.company_id.allow_invoice_backward and (date_inv > today.date() or date_inv < tax_month_date):
                raise UserError(_("วันที่ลงบัญชีควรเป็นวันนี้หรือวันภายในเดือนนี้"))

        return super(AccountInvoice, self).create(vals)

    @api.multi
    def write(self, vals):
        tz_base = pytz.timezone('Asia/Bangkok')
        today = datetime.today()
        today = pytz.utc.localize(today, "%Y-%m-%d %H:%M:%S").astimezone(tz_base)

        if vals.get('date_invoice'):
            end_tax_date = strToDate(vals['date_invoice']) + relativedelta(months=+6)

            #last date of end tax month
            end_tax_date = date(end_tax_date.year, end_tax_date.month,
                                calendar.monthrange(end_tax_date.year, end_tax_date.month)[1])


            # invoie date should not allow in the future
            if not self.env.user.company_id.allow_invoice_backward and strToDate(vals['date_invoice']) > today.date():
                raise UserError(_("ใบกำกับภาษีไม่สามารถลงวันที่ล่วงหน้า"))

            #if last day end tax month pass then alert
            if not self.env.user.company_id.allow_invoice_backward and end_tax_date < today.date():
                raise UserError(_("ใบกำกับภาษีฉบับนี้เกิน 6 เดือนรอบภาษี"))


        if vals.get('date'):

            #date should be in last day end tax month but can't before start date of today month
            # print vals['date']
            date_inv = strToDate(vals['date'])
            if today.month == 1:
                tax_month_before_date = date(today.year-1, 12, 1)
            else:
                tax_month_before_date = date(today.year, today.month-1, 1)

            tax_month_date = date(today.year, today.month, 1)
            tax_month_limit_date = date(today.year, today.month, 15)

            # print today
            # print tax_month_limit_date
            # print tax_month_before_date
            # print tax_month_date

            if today.date() <= tax_month_limit_date:
                if not self.env.user.company_id.allow_invoice_backward and (date_inv > today.date() or date_inv < tax_month_before_date):
                    raise UserError(_("วันที่ลงบัญชีควรเป็นวันนี้หรือวันภายในเดือนนี้"))
            elif today.date() > tax_month_limit_date:
                if not self.env.user.company_id.allow_invoice_backward and (date_inv > today.date() or date_inv < tax_month_date):
                    raise UserError(_("วันที่ลงบัญชีควรเป็นวันนี้หรือวันภายในเดือนนี้"))

        # print vals
        # print self
        return super(AccountInvoice, self).write(vals)

    @api.depends('bill_date')
    def _get_string_date(self):
        for invoice in self:
            if invoice.bill_date:
                invoice.bill_date_str = str(strToDate(invoice.bill_date).strftime("%d/%m/%Y"))

    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        self.print_tax_invoice = True
        return self.env['report'].get_action(self, 'print_itaas_report.invoice01_report_id')

    @api.multi
    def credit_note_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        self.print_credit_note = True
        return self.env['report'].get_action(self, 'print_itaas_report.creditnote_report_id')

    @api.multi
    def debit_note_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        self.print_debit_note = True
        return self.env['report'].get_action(self, 'print_itaas_report.debitnote_report_id')

    @api.multi
    def invoice_validate(self):
        for invoice in self:

            if invoice.type in ('out_invoice', 'out_refund') and not invoice.partner_id.vat and not invoice.partner_id.customer_no_vat:
                raise UserError(_("Invalid Customer TAX ID"))

            # if not invoice.amount_total > 0.0:
            #     raise UserError(_("Your Invoice Amount is 0"))

            # if invoice.type in ('out_invoice', 'out_refund') and invoice.account_id.user_type_id.name != 'Receivable' and (invoice.account_id.user_type_id.name).encode('utf-8') != 'ลูกหนี้':
            #     raise UserError(_("Your receivable account is wrong, please contact your account manager"))
            #
            # if invoice.type in ('in_invoice', 'in_refund') and invoice.account_id.user_type_id.name != 'Payable' and invoice.account_id.user_type_id.name != 'เจ้าหนี้':
            #     raise UserError(_("Your payable account is wrong, please contact your account manager"))

            if invoice.type in ('in_invoice', 'in_refund'):
                if invoice.reference:
                    if self.search([('type', '=', invoice.type), ('reference', '=', invoice.reference), ('company_id', '=', invoice.company_id.id), ('commercial_partner_id', '=', invoice.commercial_partner_id.id), ('id', '!=', invoice.id)]):
                        raise UserError(_("Duplicated vendor reference detected. You probably encoded twice the same vendor bill/refund."))
                if not invoice.reference and not invoice.reference_later:
                    raise UserError(_(
                        "Please input vendor tax invoice number before validate"))

            if self.env.user.company_id.invoice_step == '1step':
                self.write({'tax_inv_generated': True})

        return self.write({'state': 'open'})



    #return amount untax
    def get_tax_invoice(self):
        tax_invoice = self.env['account.invoice'].search([('number','=',self.origin)],limit=1)
        return tax_invoice.amount_untaxed

    # return invoice id
    def get_tax_invoice_id(self):
        tax_invoice = self.env['account.invoice'].search([('number', '=', self.origin)], limit=1)
        return tax_invoice

    ############ REMOVE from 31/08/2019
    #     # Load all unsold PO lines
    # @api.onchange('purchase_id')
    # def purchase_order_change(self):
    #     if not self.purchase_id:
    #         return {}
    #     if not self.partner_id:
    #         self.partner_id = self.purchase_id.partner_id.id
    #     new_lines = self.env['account.invoice.line']
    #     for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
    #         data = self._prepare_invoice_line_from_po_line(line)
    #         new_line = new_lines.new(data)
    #         new_line._set_additional_fields(self)
    #         new_lines += new_line
    #
    #     self.invoice_line_ids += new_lines
    #     self.purchase_id = False
    #     return {}

    def _prepare_invoice_line_from_po_line(self, line):
        # print "111111111111"
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        res['department_id'] = line.department_id.id
        res['discount_amount'] = line.discount_amount
        return res


    @api.onchange('multi_so')
    def _onchange_multi_so(self):
        return self._onchange_allowed_sale_ids()

    @api.onchange('state', 'partner_id', 'invoice_line_ids')
    def _onchange_allowed_sale_ids(self):
        '''
        The purpose of the method is to define a domain for the available
        sales orders.
        '''
        result = {}

        # A SO can be selected only if at least one SO line is not already in the invoice
        so_line_ids = self.invoice_line_ids.mapped('so_line_id')
        sale_ids = self.invoice_line_ids.mapped('sale_id').filtered(lambda r: r.order_line <= so_line_ids)

        result['domain'] = {'sale_id': [
            ('invoice_status', '=', 'to invoice'),
            ('partner_id', 'child_of', self.partner_id.id),
            ('id', 'not in', sale_ids.ids),
        ]}
        return result

    # Load all unsold SO lines
    @api.onchange('sale_id')
    def sale_order_change(self):
        if not self.sale_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.sale_id.partner_id.id
            # self.account_note = self.sale_id.account_note

        new_lines = self.env['account.invoice.line']
        for line in self.sale_id.order_line:
            # Load a SO line only once
            if line in self.invoice_line_ids.mapped('so_line_id'):
                continue
            if line.product_id.invoice_policy == 'order':
                qty = line.product_uom_qty - line.qty_invoiced
            else:
                qty = line.qty_delivered - line.qty_invoiced
            if float_compare(qty, 0.0, precision_rounding=line.product_uom.rounding) <= 0:
                qty = 0.0
            taxes = line.tax_id
            invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes)

            account = line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(
                    _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') % \
                    (line.product_id.name, line.product_id.id, line.product_id.categ_id.name))

            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            if fpos:
                account = fpos.map_account(account)


            # if line.department_id:
            #     department_id = line.department_id.id
            # else:
            #     department_id = False

            data = {
                'so_line_id': line.id,
                'name': line.name,
                'sequence': line.sequence,
                'origin': self.sale_id.name,
                'uom_id': line.product_uom.id,
                'product_id': line.product_id.id or False,
                'account_id': account.id,
                'price_unit': line.order_id.currency_id.compute(line.price_unit, self.currency_id, round=False),
                'quantity': qty,
                'discount': line.discount,
                'discount_amount':line.discount_amount,
                # 'department_id': department_id,
                # 'account_analytic_id': line.order_id and line.order_id.project_id.id,
                'invoice_line_tax_ids': invoice_line_tax_ids.ids,
            }

            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.sale_id = False
        sale_ids = self.invoice_line_ids.mapped('sale_id')
        if sale_ids:
            self.origin = ', '.join(sale_ids.mapped('name'))
        return {}

    @api.model
    def invoice_line_move_line_get(self):
        res = []
        for line in self.invoice_line_ids:
            tax_ids = []
            for tax in line.invoice_line_tax_ids:
                tax_ids.append((4, tax.id, None))
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        tax_ids.append((4, child.id, None))

            move_line_dict = {
                'invl_id': line.id,
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': line.price_unit,
                'quantity': line.quantity,
                'price': line.price_subtotal,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
                'uom_id': line.uom_id.id,
                'partner_id': line.partner_id,
                'account_analytic_id': line.account_analytic_id.id,
                'tax_ids': tax_ids,
                'invoice_id': self.id,
                'department_id': line.department_id.id,
            }
            if line['account_analytic_id']:
                move_line_dict['analytic_line_ids'] = [(0, 0, line._get_analytic_line())]
            res.append(move_line_dict)
        # print "invoice_line_move_line_get"
        # print res
        return res

    @api.model
    def tax_line_move_line_get(self):
        res = []
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount:
                tax = tax_line.tax_id
                if tax.amount_type == "group":
                    for child_tax in tax.children_tax_ids:
                        done_taxes.append(child_tax.id)
                done_taxes.append(tax.id)
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount,
                    'quantity': 1,
                    'partner_id': tax_line.partner_id,
                    'ref': tax_line.ref,
                    'price': tax_line.amount,
                    'account_id': tax_line.account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'invoice_id': self.id,
                    'tax_ids': [(6, 0, done_taxes)] if tax_line.tax_id.include_base_amount else []
                })
        # print "tax_line_move_line_get"
        # print res
        return res


    #check "partner_id" and "ref" in case provided, then use as the same with provided otherwise refer from invoice level
    @api.model
    def line_get_convert(self, line, part):
        partner_id = line.get('partner_id', False)
        if not partner_id:
            partner_id = part;
        else:
            partner_id = partner_id.id

        return {
            'date_maturity': line.get('date_maturity', False),
            'partner_id': partner_id,
            'ref': line.get('ref', False),
            'name': line['name'][:64],
            'debit': line['price'] > 0 and line['price'],
            'credit': line['price'] < 0 and -line['price'],
            'account_id': line['account_id'],
            'analytic_line_ids': line.get('analytic_line_ids', []),
            'amount_currency': line['price'] > 0 and abs(line.get('amount_currency', False)) or -abs(
                line.get('amount_currency', False)),
            'currency_id': line.get('currency_id', False),
            'quantity': line.get('quantity', 1.00),
            'product_id': line.get('product_id', False),
            'product_uom_id': line.get('uom_id', False),
            'analytic_account_id': line.get('account_analytic_id', False),
            'invoice_id': line.get('invoice_id', False),
            'department_id': line.get('department_id', False),
            'tax_ids': line.get('tax_ids', False),
            'tax_line_id': line.get('tax_line_id', False),
        }

    @api.multi
    def action_move_create(self):
        # for invoice in self:
        # print "invoice discount"
        # print invoice.discount_view
        # print self.env.user.company_id.default_sales_discount_account_id
        # print self.env.user.company_id.default_purchase_discount_account_id
        # flag = invoice.discount_view and (
        # not self.env.user.company_id.default_sales_discount_account_id.id or self.env.user.company_id.default_purchase_discount_account_id.id)
        #
        # print "flag"
        # print flag

        # if invoice.discount_view and not (self.env.user.company_id.default_sales_discount_account_id or self.env.user.company_id.default_purchase_discount_account_id):
        #     raise UserError(_("Please define sale and purchase discount account"))

        result = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if inv.move_id:
                move_id = self.env['account.move'].sudo().search([('id', '=', inv.move_id.id), ('company_id', '=', inv.company_id.id)])
                if move_id:
                    move_id.write({'invoice_date': inv.date_invoice})




        return result

    @api.multi
    def action_move_without_gl_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue
            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            date_invoice = inv.date_invoice
            journal = inv.journal_id.with_context(ctx)

            date = inv.date or date_invoice
            move_vals = {
                'ref': inv.name + "-" + inv.origin,
                'partner_id': inv.partner_id.id,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['dont_create_taxes'] = True
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        return True

    @api.multi
    def action_generate_tax_inv(self,payment=False):
        print ('---ACTION GEN TAX--')
        print('payment:',payment)
        if self.env.user.company_id.invoice_step == '2step':
            tax_inv_no = self.number
            # if not self.tax_inv_date and self.date_invoice:
            #     self.tax_inv_date = self.date_invoice
            # if self.tax_inv_date:
            #     tax_in_date = self.tax_inv_date
            # else:
            #     tax_in_date = fields.Date.context_today(self)
            # print('tax_in_date:',tax_in_date)
            # if not self.tax_inv_no and self.journal_id.payment_sequence_id:
            #     sequence = self.journal_id.payment_sequence_id
            #     print('sequenceeeeeeee:',sequence)
            #     try:
            #         # Close ByJeng 28/04/2021 กรณี Gentax โดยตรงผ่านหน้า Invoice Error เพราะ Payment ตัวนี้ไม่ใช่ Date ไม่รุ้ว่า ดู log แล้ว Payment ไม่ใช่ Date ขอปิดไว้ก่อน
            #         # tax_inv_no = sequence.with_context(ir_sequence_date=payment).next_by_id()
            #         tax_inv_no = sequence.with_context(ir_sequence_date=tax_in_date).next_by_id()
            #
            #
            #     except:
            #         tax_inv_no = sequence.with_context(ir_sequence_date=tax_in_date).next_by_id()
            #
            # elif not self.tax_inv_no:
            #     # tax_inv_no = self.env['ir.sequence'].next_by_code('tax.inv.no') or 'New'
            #     tax_inv_no = self.number
            #
            # else:
            #     tax_inv_no = self.number

            if self.tax_inv_date:
                self.write({'tax_inv_no': tax_inv_no,
                            'tax_inv_generated': True})
            else:
                self.write({'tax_inv_no': tax_inv_no,
                            'tax_inv_date': fields.Date.context_today(self),
                            'tax_inv_generated': True})

        if not self.is_skip_gl:
            print ('--XXXX')
            self.action_move_tax_reverse_create()




    @api.multi
    def action_cancel_draft(self):
        # go from canceled state to draft state
        self.write({'state': 'draft', 'date': False,'tax_inv_generated': False})
        self.delete_workflow()
        self.create_workflow()
        # Delete former printed invoice
        try:
            report_invoice = self.env['report']._get_report_from_name('account.report_invoice')
        except IndexError:
            report_invoice = False
        if report_invoice and report_invoice.attachment:
            for invoice in self:
                with invoice.env.do_in_draft():
                    invoice.number, invoice.state = invoice.move_name, 'open'
                    attachment = self.env['report']._attachment_stored(invoice, report_invoice)[invoice.id]
                if attachment:
                    attachment.unlink()
        return True

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        adj_moves = self.env['account.move']

        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            if inv.adjust_move_id:
                adj_moves += inv.adjust_move_id
            if inv.payment_move_line_ids:
                raise UserError(_(
                    'You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

            if inv.tax_inv_generated:
                raise UserError(_(
                    'You cannot cancel an invoice which is tax invoice generated. You need to cancel tax invoice first.'))

        # First, set the invoices as cancelled and detach the move ids

        number = self.number
        tax_inv_no = self.tax_inv_no
        self.write({'state': 'cancel', 'move_id': False, })
        self.write({'number': number})
        self.write({'tax_inv_no': tax_inv_no})

        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            moves.unlink()
        if adj_moves:
            adj_moves.button_cancel()

        return True

    @api.multi
    def get_taxes_values(self):
        tax_grouped = {}
        for line in self.invoice_line_ids:
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if line.discount_amount > 0 and self.env.user.company_id.discount_amount_condition and self.env.user.company_id.discount_amount_condition == 'unit':
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0) - line.discount_amount
            elif line.discount_amount > 0 and line.quantity and self.env.user.company_id.discount_amount_condition and self.env.user.company_id.discount_amount_condition == 'total':
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0) - (line.discount_amount / line.quantity)

            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = {
                    'invoice_id': self.id,
                    'name': tax['name'],
                    'tax_id': tax['id'],
                    'amount': tax['amount'],
                    'manual': False,
                    'sequence': tax['sequence'],
                    'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
                    'account_id': self.type in ('out_invoice', 'in_invoice') and (tax['account_id'] or line.account_id.id) or (tax['refund_account_id'] or line.account_id.id),
                }

                # If the taxes generate moves on the same financial account as the invoice line,
                # propagate the analytic account from the invoice line to the tax line.
                # This is necessary in situations were (part of) the taxes cannot be reclaimed,
                # to ensure the tax move is allocated to the proper analytic account.
                if not val.get('account_analytic_id') and line.account_analytic_id and val['account_id'] == line.account_id.id:
                    val['account_analytic_id'] = line.account_analytic_id.id

                key = tax['id']
                if key not in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
        return tax_grouped

        # this section need to revese all validated invoiced and tax
    @api.multi
    def action_move_tax_reverse_create(self):
        """ Creates invoice related analytics and financial move lines """
        # print "action_move_tax_reverse_create"
        print ('--action_move_tax_reverse_create--')
        account_move = self.env['account.move']

        for inv in self:
            ctx = dict(self._context, lang=inv.partner_id.lang)
            ctx['company_id'] = inv.company_id.id
            ctx['dont_create_taxes'] = True
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            #check journal
            if inv.journal_id.adj_journal:
                journal = inv.journal_id.adj_journal.with_context(ctx)
            else:
                raise UserError(_('Please define sequence on the journal related to this adjust tax.'))
                journal = inv.journal_id.with_context(ctx)

            #check some setting
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))

            if not inv.tax_inv_date:
                inv.with_context(ctx).write({'tax_inv_date': fields.Date.context_today(self)})
            date = fields.Date.context_today(self)

            #check existing journal, if exist and post
            if inv.adjust_move_id and inv.adjust_move_id.state == 'posted':
                continue

            #if exist but draft
            elif inv.adjust_move_id and inv.adjust_move_id.state == 'draft':
                move_vals = {
                    'line_ids': False,
                }
                account_move.browse(inv.adjust_move_id.id).update(move_vals)


            tax_invoice_date = inv.tax_inv_date
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.tax_line_move_line_reverse_get()
            # print "tax line"
            # print iml

            if not inv.adjust_require:
                continue

            print ('--UPDATE Tax reverse')
            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)


            line = inv.finalize_invoice_move_lines(line)

            if journal.sequence_id and not inv.adjust_move_id:
                # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                sequence = journal.sequence_id
                # if invoice and invoice.type in ['out_refund', 'in_refund'] and journal.refund_sequence:
                #     sequence = journal.refund_sequence_id
                new_name = sequence.with_context(ir_sequence_date=date).next_by_id()

            #if journal exist then keep the same name
            elif journal.sequence_id and inv.adjust_move_id:
                new_name = account_move.browse(inv.adjust_move_id.id).name
            else:
                raise UserError(_('Please define a sequence on the journal.'))

            if inv.type in ('out_invoice'):
                ref = inv.tax_inv_no
                date = inv.tax_inv_date
                invoice_date = inv.tax_inv_date
            elif inv.type in ('in_invoice'):
                ref = inv.number
                date = fields.Date.context_today(self)
                invoice_date = inv.date_invoice

            move_vals = {
                'ref': ref,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'name': new_name,
                'invoice_date': invoice_date,
                'narration': inv.comment,
            }
            #if journal exist
            if inv.adjust_move_id and inv.adjust_move_id.state == 'draft':
                # print "update draft"
                account_move.browse(inv.adjust_move_id.id).with_context(ctx_nolang).write(move_vals)
                account_move.browse(inv.adjust_move_id.id).post()
                # print "after update"

            #if new
            else:
                move = account_move.with_context(ctx_nolang).create(move_vals)
                move.post()
                vals = {
                    'adjust_move_id': move.id,
                }
                inv.with_context(ctx).write(vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:

        print ('--ENTRY CREATe--')
        return True

    @api.model
    def tax_line_move_line_reverse_get(self):
        res = []
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        default_purchase_tax_id = self.env['account.tax'].search(
            [('tax_report', '=', True),('type_tax_use', '=', 'purchase'), ('company_id', '=', self.company_id.id)],limit=1)

        default_sale_tax_id = self.env['account.tax'].search(
            [('tax_report', '=', True),('type_tax_use', '=', 'sale'), ('company_id', '=', self.company_id.id)],limit=1)

        if self.type in ('out_invoice','out_refund'):
            # print "invoice"
            if default_sale_tax_id:
                default_tax_id = default_sale_tax_id
                ref = self.number
            else:
                raise UserError(_('Please define a default sale tax'))

        if self.type in ('in_invoice','in_refund'):
            # print "vendor bbill"
            if default_purchase_tax_id:
                default_tax_id = default_purchase_tax_id
                ref = self.reference
            else:
                raise UserError(_('Please define a default purchase tax'))


        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            # print tax_line.name
            if tax_line.amount:
                tax = tax_line.tax_id
                if not tax.tax_report and not tax.tax_no_refund:
                    self.adjust_require = True
                    done_taxes.append(tax.id)
                    # append debit for the original one, reverse from previous post
                    res.append({
                        'invoice_tax_line_id': tax_line.id,
                        'tax_line_id': tax.id,
                        'type': 'tax',
                        'name': tax_line.name,
                        'price_unit': tax_line.amount,
                        'quantity': 1,
                        #this will support multiple tax, but for single tax tax_line.amount and self.amount_tax is the same
                        # 'price': tax_line.amount * (-1),
                        'price': self.amount_tax * (-1),
                        'account_id': tax.account_id.id,
                        'account_analytic_id': tax_line.account_analytic_id.id,
                        'invoice_id': self.id,
                        'tax_ids': [(6, 0, done_taxes)] if tax_line.tax_id.include_base_amount else []
                    })

                    # append create new tax one
                    res.append({
                        'invoice_tax_line_id': tax_line.id,
                        'tax_line_id': default_sale_tax_id.id,
                        'type': 'tax',
                        'name': default_tax_id.name,
                        'price_unit': tax_line.amount,
                        'quantity': 1,
                        'ref': ref,
                        #this will support multiple tax, but for single tax tax_line.amount and self.amount_tax is the same
                        # 'price': tax_line.amount * (-1),
                        'price': self.amount_tax,
                        'account_id': default_tax_id.account_id.id,
                        'account_analytic_id': tax_line.account_analytic_id.id,
                        'invoice_id': self.id,
                        'tax_ids': [(6, 0, done_taxes)] if tax_line.tax_id.include_base_amount else []
                    })

        return res


class AccountInvoiceLine(models.Model):
    """ Override AccountInvoice_line to add the link to the sales order line it is related to"""
    _inherit = 'account.invoice.line'

    so_line_id = fields.Many2one('sale.order.line', 'Sales Order Line', ondelete='set null', select=True, readonly=True)
    sale_id = fields.Many2one('sale.order', related='so_line_id.order_id', string='Sales Order', store=False,
                              readonly=True,
                              help='Associated Sales Order. Filled in automatically when a SO is chosen on the vendor bill.')
    discount_amount = fields.Float('Discount (Amount)', default=0.0)
    department_id = fields.Many2one('hr.department', string='Department')

    @api.one
    @api.depends('price_unit', 'discount', 'discount_amount','invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):

        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        if self.discount_amount > 0.0:
            if self.env.user.company_id.discount_amount_condition and self.env.user.company_id.discount_amount_condition == 'unit':
                price -= self.discount_amount
            elif self.quantity:
                price -= self.discount_amount / self.quantity
            else:
                price = 0.00

        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)
        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price
        if self.invoice_id.currency_id and self.invoice_id.company_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed,
                                                                        self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1

        self.price_subtotal_signed = price_subtotal_signed * sign

    # get total description line
    def get_line(self, data):
        return data.count("\n")

    @api.model
    def create(self, vals):
        if vals.get('so_line_id', False):
            vals.update({'sale_line_ids': [(6, 0, [vals['so_line_id']])]})
        # Add by Book 2019/12/13 ಠ_ಠ
        if vals.get('sale_line_ids', False):
            sale_line_ids = vals['sale_line_ids'][0]
            so_line_id = sale_line_ids[2]
            so_line_obj = self.env['sale.order.line'].search([('id', '=', so_line_id[0])],limit=1)
            vals.update({'so_line_id': so_line_id[0]})
            vals.update({'discount_amount': so_line_obj.discount_amount})
        return super(AccountInvoiceLine, self).create(vals)




class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    partner_id = fields.Many2one('res.partner', string='Partner')
    ref = fields.Char(string='Sup Invoice No.')
