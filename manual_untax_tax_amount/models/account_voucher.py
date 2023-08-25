from odoo import api, fields,_ ,models

class accont_voucher_inherit(models.Model):
    _inherit = "account.voucher"

    is_manual_amount = fields.Boolean(string='Manual Amount', default=False)

    new_tax_correction = fields.Float(string='New Tax Correction')
    new_amount_tax = fields.Float(string='New Amount Tax')
    new_amount_total = fields.Float(string='New Amount Total')

    @api.multi
    def apply_price(self):
        if self.new_tax_correction:
            self.tax_correction = self.new_tax_correction
        if self.new_amount_tax:
            self.tax_amount = self.new_amount_tax
        if self.new_amount_total:
            self.amount = self.new_amount_total
