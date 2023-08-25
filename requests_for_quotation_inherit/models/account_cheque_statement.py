from odoo import api, fields, models


class Account_Cheque_Statement(models.Model):
    _inherit = 'account.cheque.statement'

    is_done = fields.Boolean(string='นำฝากแล้ว', default=False)

    @api.multi
    def action_cancel_new(self):
        self.move_new_id.button_cancel()
        self.move_new_id.unlink()
        return self.write({'state': 'cancel'})



    @api.multi
    def action_setto_draft(self):
        return self.write({'state': 'open'})

