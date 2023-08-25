from odoo import api, fields, models


class material_purchase_requisition_itaas(models.Model):
    _inherit = 'material.purchase.requisition'

    @api.multi
    def action_confirm_order(self):
        res = super(material_purchase_requisition_itaas, self).action_confirm_order()
        if self.employee_id:
            if self.employee_id.source_location_id:
                self.source_location_id = self.employee_id.source_location_id.id
        return res
