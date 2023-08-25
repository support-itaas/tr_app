#-*-coding: utf-8 -*-

from odoo import api, fields, models, _

class hr_period(models.Model):
    _inherit = "hr.period"

    @api.multi
    def action_set_tax(self):
        if self.payslip_ids:
            for payslip in self.payslip_ids:
                summary_for_tax_onetime = payslip.get_summary_for_tax_onetime()
                # print('summary_for_tax_onetime : ',summary_for_tax_onetime)
                payslip.write({'summary_for_tax_one':abs(summary_for_tax_onetime)})
