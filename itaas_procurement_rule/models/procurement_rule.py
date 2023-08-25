# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).


from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _make_po_get_domain(self, values, partner):
        domain = super(ProcurementRule, self)._make_po_get_domain(values, partner)
        gpo = self.group_propagation_option
        group = (gpo == 'fixed' and self.group_id) or \
                (gpo == 'propagate' and 'group_id' in values and values['group_id']) or False

        domain += (
            ('partner_id', '=', partner.id),
            ('state', '=', 'draft'),
            ('picking_type_id', '=', self.picking_type_id.id),
            ('company_id', '=', values['company_id'].id),
            ('purchase_type', '=', values['orderpoint_id'].purchase_type.id),
        )
        if group:
            domain += (('group_id', '=', group.id),)
        return domain
