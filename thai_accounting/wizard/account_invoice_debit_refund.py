# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.tools.safe_eval import safe_eval as eval
from openerp.exceptions import UserError

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Refund
    'in_refund': 'in_invoice',          # Vendor Refund
}

class AccountInvoiceDebitRefund(models.TransientModel):
    """Refunds invoice"""

    _name = "account.invoice.debitrefund"
    _description = "Invoice Debit Refund"

    @api.model
    def _get_reason(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        if active_id:
            inv = self.env['account.invoice'].browse(active_id)
            return inv.name
        return ''

    date_invoice = fields.Date(string='Debit Note Date', default=fields.Date.context_today, required=True)
    date = fields.Date(string='Accounting Date')
    description = fields.Selection([
        ('ref01', 'เพิ่มหนี้เนื่องจากสินค้าเกินกว่าจำนวนที่ตกลงซื้อขายกัน'),
        ('ref02', 'เพิ่มหนี้เนื่องจากคำนวณราคาผิดพลาดต่ำกว่าที่เป็นจริง'),
        ('ref03', 'เพิ่มหนี้เนื่องจากเหตุอื่น'),
    ],
        string='Reason', required=True)

    refund_only = fields.Boolean(string='Technical field to hide filter_refund in case invoice is partially paid', compute='_get_refund_only')
    filter_refund = fields.Selection([('refund', 'Create a draft debit note')],
        default='refund', string='Debit Note', required=True, help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled')

    @api.depends('date_invoice')
    @api.one
    def _get_refund_only(self):
        invoice_id = self.env['account.invoice'].browse(self._context.get('active_id',False))
        if len(invoice_id.payment_move_line_ids) != 0 and invoice_id.state != 'paid':
            self.refund_only = True
        else:
            self.refund_only = False


    @api.multi
    def invoice_refund(self):
        data_refund = self.read(['filter_refund'])[0]['filter_refund']
        return self.compute_refund(data_refund)

    @api.multi
    def compute_refund(self, mode='refund'):
        inv_obj = self.env['account.invoice']
        inv_tax_obj = self.env['account.invoice.tax']
        inv_line_obj = self.env['account.invoice.line']
        context = dict(self._context or {})
        xml_id = False

        for form in self:
            created_inv = []
            date = False
            description = False
            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise UserError(_('Cannot refund draft/proforma/cancelled invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise UserError(_(
                        'Cannot refund invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.'))

                date = form.date or False
                if form.description:
                    if form.description == 'ref01':
                        description = 'เพิ่มหนี้เนื่องจากสินค้าเกินกว่าจำนวนที่ตกลงซื้อขายกัน'
                    elif form.description == 'ref02':
                        description = 'เพิ่มหนี้เนื่องจากคำนวณราคาผิดพลาดต่ำกว่าที่เป็นจริง'
                    elif form.description == 'ref03':
                        description = 'เพิ่มหนี้เนื่องจากเหตุอื่น'

                description = description or inv.name
                refund = inv.refund_debit(form.date_invoice, date, description, inv.journal_id.id)
                refund.compute_taxes()

                created_inv.append(refund.id)
                xml_id = (inv.type in ['out_refund', 'out_invoice']) and 'action_invoice_tree1' or \
                         (inv.type in ['in_refund', 'in_invoice']) and 'action_invoice_tree2'
                # Put the reason in the chatter
                subject = _("Invoice Debit")
                body = description
                refund.message_post(body=body, subject=subject)
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
        return True
