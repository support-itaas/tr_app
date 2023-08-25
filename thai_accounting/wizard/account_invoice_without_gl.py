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

class AccountInvoiceWithoutGl(models.TransientModel):
    """Refunds invoice"""

    _name = "account.invoice.withoutgl"
    _description = "Invoice Issue Without GL"

    @api.model
    def _get_reason(self):
        context = dict(self._context or {})
        active_id = context.get('active_id', False)
        if active_id:
            inv = self.env['account.invoice'].browse(active_id)
            return inv.name
        return ''

    date_invoice = fields.Date(string='วันที่', default=fields.Date.context_today, required=True)
    date = fields.Date(string='วันที่ลงบัญชี', groups='base.group_no_one')
    description = fields.Selection([
        ('ref01', 'เนื่องจากสาระสำคัญผิด'),
        ('ref02', '่เนื่องจากพิมพ์ครั้งแรกไม่สมบูรณ์'),
    ],
        string='เหตุผล', required=True)
    description_more = fields.Char(string='เหตุผลเพิ่มเติม',required=True)

    refund_only = fields.Boolean(string='Technical field to hide filter_refund in case invoice is partially paid', compute='_get_refund_only')
    filter_refund = fields.Selection([('refund', 'Create New Invoice Without GL')],
        default='refund', string='ออกใบกำกับภาษีใหม่', required=True, help='Refund base on this type. You can not Modify and Cancel if the invoice is already reconciled')

    @api.depends('date_invoice')
    @api.one
    def _get_refund_only(self):
        invoice_id = self.env['account.invoice'].browse(self._context.get('active_id',False))
        if len(invoice_id.payment_move_line_ids) != 0 and invoice_id.state != 'paid':
            self.refund_only = True
        else:
            self.refund_only = False


    @api.multi
    def invoice_without_gl(self):
        data_refund = self.read(['filter_refund'])[0]['filter_refund']
        return self.compute_invoice_without_gl(data_refund)

    @api.multi
    def compute_invoice_without_gl(self, mode='refund'):
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
                date = form.date or False
                if form.description:
                    if form.description == 'ref01':
                        description = 'เนื่องจากสาระสำคัญผิด ' + str((form.description_more).encode('utf-8'))
                    elif form.description == 'ref02':
                        description = 'เนื่องจากพิมพ์ครั้งแรกไม่สมบูรณ์ ' + str((form.description_more).encode('utf-8'))


                description = description or inv.name
                refund = inv.new_inv_without_gl(form.date_invoice, date, description, inv.journal_id.id)
                refund.compute_taxes()
                refund.action_move_without_gl_create()
                refund.invoice_validate()
                if self.env.user.company_id.invoice_step == '2step':
                    refund.action_generate_tax_inv()


                created_inv.append(refund.id)
                xml_id = (inv.type in ['out_refund', 'out_invoice']) and 'action_invoice_tree1' or \
                         (inv.type in ['in_refund', 'in_invoice']) and 'action_invoice_tree2'
                # Put the reason in the chatter
                subject = _("ออกใบกำกับภาษีใหม่")
                body = description
                refund.message_post(body=body, subject=subject)
        if xml_id:
            result = self.env.ref('account.%s' % (xml_id)).read()[0]
            invoice_domain = eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
        return True
