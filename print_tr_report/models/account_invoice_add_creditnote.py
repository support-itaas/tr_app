# -*- coding: utf-8 -*-
from openerp import fields, api, models
from bahttext import bahttext

class TaxInvoiceNo(models.Model):
    _inherit ="account.invoice"

    tax_invoice_no = fields.Char(String='Tax invoice No.')






