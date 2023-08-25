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


    @api.model
    def _issue_invoice_without_gl_cleanup_lines(self, lines):
        """ Convert records to dict of values suitable for one2many line creation

            :param recordset lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """
        result = []
        for line in lines:
            values = {}
            for name, field in line._fields.iteritems():
                if name in MAGIC_COLUMNS:
                    continue
                elif field.type == 'many2one':
                    values[name] = line[name].id
                elif field.type not in ['many2many', 'one2many']:
                    values[name] = line[name]
                elif name == 'invoice_line_tax_ids':
                    values[name] = [(6, 0, line[name].ids)]
            result.append((0, 0, values))
        return result

    @api.model
    def _prepare_invoice_without_gl(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
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

        values['invoice_line_ids'] = self._issue_invoice_without_gl_cleanup_lines(invoice.invoice_line_ids)

        tax_lines = invoice.tax_line_ids
        values['tax_line_ids'] = self._issue_invoice_without_gl_cleanup_lines(tax_lines)


        values['type'] = 'out_invoice'
        values['original_invoice_date_inv_skip_gl'] = invoice.date_invoice
        values['state'] = 'draft'
        values['number'] = False
        if self.env.user.company_id.invoice_step == '2step':
            values['origin'] = invoice.tax_inv_no
        else:
            values['origin'] = invoice.number
        values['is_skip_gl'] = True

        if date or date_invoice:
            values['date'] = date or date_invoice
        if description:
            values['name'] = description
        return values

    @api.multi
    @api.returns('self')
    def new_inv_without_gl(self, date_invoice=None, date=None, description=None, journal_id=None):
        new_invoices = self.browse()
        for invoice in self:
            # create the new invoice
            values = self._prepare_invoice_without_gl(invoice, date_invoice=date_invoice, date=date,
                                          description=description, journal_id=journal_id)
            # print values
            new_invoices += self.create(values)
            invoice.write({'is_skip_gl_original': True})
        return new_invoices

