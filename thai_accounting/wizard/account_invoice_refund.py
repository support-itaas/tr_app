# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

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

MAGIC_COLUMNS = ('id', 'create_uid', 'create_date', 'write_uid', 'write_date')

class AccountInvoice(models.Model):
    _inherit = "account.invoice"


    # @api.model
    # def _refund_debit_cleanup_lines(self, lines):
    #     """ Convert records to dict of values suitable for one2many line creation
    #
    #         :param recordset lines: records to convert
    #         :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
    #     """
    #
    #
    #     result = []
    #     for line in lines:
    #         values = {}
    #         for name, field in line._fields.items():
    #             if name in MAGIC_COLUMNS:
    #                 continue
    #             elif field.type == 'many2one':
    #                 values[name] = line[name].id
    #             elif field.type not in ['many2many', 'one2many']:
    #                 values[name] = line[name]
    #             elif name == 'invoice_line_tax_ids':
    #                 values[name] = [(6, 0, line[name].ids)]
    #             elif name == 'analytic_tag_ids':
    #                 values[name] = [(6, 0, line[name].ids)]
    #         result.append((0, 0, values))
    #     return result

    @api.model
    def _prepare_refund_debit(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        """ Prepare the dict of values to create the new refund from the invoice.
            This method may be overridden to implement custom
            refund generation (making sure to call super() to establish
            a clean extension chain).

            :param record invoice: invoice to refund
            :param string date_invoice: refund creation date from the wizard
            :param integer date: force date from the wizard
            :param string description: description of the refund from the wizard
            :param integer journal_id: account.journal from the wizard
            :return: dict of value to create() the refund
        """
        values = {}
        for field in ['name', 'reference', 'comment', 'date_due', 'partner_id', 'company_id',
                      'account_id', 'currency_id', 'payment_term_id', 'user_id', 'fiscal_position_id']:
            if invoice._fields[field].type == 'many2one':
                values[field] = invoice[field].id
            else:
                values[field] = invoice[field] or False

        values['invoice_line_ids'] = self._refund_cleanup_lines(invoice.invoice_line_ids)

        tax_lines = invoice.tax_line_ids
        values['tax_line_ids'] = self._refund_cleanup_lines(tax_lines)

        # if journal_id:
        #     journal = self.env['account.journal'].browse(journal_id)
        # elif invoice['type'] == 'in_invoice':
        #     journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        # else:
        #     journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        # values['journal_id'] = journal.id

        values['type'] = invoice.type
        values['date_invoice'] = date_invoice or fields.Date.context_today(invoice)
        values['state'] = 'draft'
        values['number'] = False
        values['original_date_inv_skip_gl'] = invoice.date_invoice
        values['origin'] = invoice.number
        values['debit_note'] = True

        if date:
            values['date'] = date
        if description:
            values['name'] = description
        return values

    @api.multi
    @api.returns('self')
    def refund_debit(self, date_invoice=None, date=None, description=None, journal_id=None):
        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self._prepare_refund_debit(invoice, date_invoice=date_invoice, date=date,
                                          description=description, journal_id=journal_id)

            new_invoices += self.create(values)
        return new_invoices

class AccountInvoiceRefund(models.TransientModel):
    """Refunds invoice"""

    _inherit = "account.invoice.refund"
    _description = "Invoice Refund"

    other_reason = fields.Char(string='Reason Detail')

    @api.model
    def _get_reason(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        if active_id:
            inv = self.env['account.invoice'].browse(active_id)
            return inv.name
        return ''


    description = fields.Selection([
        ('ref01','ลดหนี้เนื่องจากมีการลดราคาสินค้าที่ขายเนื่องจากสินค้าผิดข้อกำหนดที่ตกลงกัน'),
        ('ref02', 'ลดหนี้เนื่องจากสินค้าชำรุดเสียหาย'),
        ('ref03', 'ลดหนี้เนื่องจากสินค้าขาดจำนวนตามที่ตกลงซื้อขาย'),
        ('ref04', 'ลดหนี้เนื่องจากคำนวณราคาสินค้าผิดพลาดสูงกว่าที่เป็นจริง'),
        ('ref05', 'ลดหนี้เนื่องจากเหตุอื่น')
                                    ],
                                   string='CN Reason', required=True)

    filter_refund = fields.Selection(
        [('refund', 'Create a draft refund'), ('cancel', 'Cancel: create refund and reconcile')],
        default='refund', string='Refund Method', required=True,
        help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled')

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
                    raise UserError(_('Cannot refund invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.'))

                date = form.date or False
                if form.description:
                    if form.description == 'ref01':
                        description = 'ลดหนี้เนื่องจากมีการลดราคาสินค้าที่ขายเนื่องจากสินค้าผิดข้อกำหนดที่ตกลงกัน'
                    elif form.description == 'ref02':
                        description = 'ลดหนี้เนื่องจากสินค้าชำรุดเสียหาย'
                    elif form.description == 'ref03':
                        description = 'ลดหนี้เนื่องจากสินค้าขาดจำนวนตามที่ตกลงซื้อขาย'
                    elif form.description == 'ref04':
                        description = 'ลดหนี้เนื่องจากคำนวณราคาสินค้าผิดพลาดสูงกว่าที่เป็นจริง'
                    elif form.description == 'ref05':
                        description = 'ลดหนี้เนื่องจากเหตุอื่น'
                        if form.other_reason:
                            description = form.other_reason


                description = description or inv.name
                refund = inv.refund(form.date_invoice, date, description, inv.journal_id.id)
                #print "Original date_invoice"
                #print inv.date_invoice

                refund.write({'original_date_inv_skip_gl': inv.date_invoice})
                refund.compute_taxes()

                created_inv.append(refund.id)
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_ids
                    to_reconcile_ids = {}
                    to_reconcile_lines = self.env['account.move.line']
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_lines += line
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconciled:
                            line.remove_move_reconcile()
                    refund.action_invoice_open()
                    for tmpline in refund.move_id.line_ids:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_lines += tmpline
                    to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                    if mode == 'modify':
                        invoice = inv.read(inv_obj._get_refund_modify_read_fields())
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(invoice['invoice_line_ids'])
                        invoice_lines = inv_obj.with_context(mode='modify')._refund_cleanup_lines(invoice_lines)
                        tax_lines = inv_tax_obj.browse(invoice['tax_line_ids'])
                        tax_lines = inv_obj._refund_cleanup_lines(tax_lines)
                        # print "inv.date_invoice and date"
                        # print inv.date_invoice
                        # print date
                        # print "end"
                        invoice.update({
                            'type': inv.type,
                            'original_date_inv_skip_gl': inv.date_invoice,
                            'date_invoice': form.date_invoice,
                            'state': 'draft',
                            'number': False,
                            'invoice_line_ids': invoice_lines,
                            'tax_line_ids': tax_lines,
                            'date': date,
                            'name': description,
                            'origin': inv.origin,
                            'fiscal_position_id': inv.fiscal_position_id.id,
                        })
                        # for field in ('partner_id', 'account_id', 'currency_id',
                        #                  'payment_term_id', 'journal_id'):
                        #         invoice[field] = invoice[field] and invoice[field][0]

                        for field in inv_obj._get_refund_common_fields():
                            if inv_obj._fields[field].type == 'many2one':
                                invoice[field] = invoice[field] and invoice[field][0]
                            else:
                                invoice[field] = invoice[field] or False

                        inv_refund = inv_obj.create(invoice)
                        if inv_refund.payment_term_id.id:
                            inv_refund._onchange_payment_term_date_invoice()
                        created_inv.append(inv_refund.id)
                xml_id = inv.type == 'out_invoice' and 'action_invoice_out_refund' or \
                         inv.type == 'out_refund' and 'action_invoice_tree1' or \
                         inv.type == 'in_invoice' and 'action_invoice_in_refund' or \
                         inv.type == 'in_refund' and 'action_invoice_tree2'
                # Put the reason in the chatter
                subject = _("Credit Note")
                body = description
                refund.message_post(body=body, subject=subject)
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
        return True
