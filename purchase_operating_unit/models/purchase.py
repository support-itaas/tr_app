# © 2019 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2019 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_operating_unit(self):
        return self.env.user.default_operating_unit_id

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        default=_default_operating_unit,
        readonly=True,
        states={'draft': [('readonly', False)],
                'sent': [('readonly', False)]}
    )

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    requested_by = fields.Many2one('res.users',
                                   'Requested by',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by,
                                   store=True)
    # @api.multi
    # def _prepare_invoice(self):
    #     self.ensure_one()
    #     invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
    #     invoice_vals['operating_unit_id'] = self.operating_unit_id.id
    #     return invoice_vals


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    operating_unit_id = fields.Many2one(related='order_id.operating_unit_id',
                                        string='Operating Unit',
                                        readonly=True)

    # @api.model
    # def _get_default_requested_by(self):
    #     return self.env['res.users'].browse(self.env.uid)
    #
    # requested_by = fields.Many2one('res.users',
    #                                'Requested by',
    #                                required=True,
    #                                track_visibility='onchange',
    #                                default=_get_default_requested_by,
    #                                store=True)

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        self.operating_unit_id = self.purchase_id.operating_unit_id.id

        return super(AccountInvoice, self).purchase_order_change()

    def _prepare_invoice_line_from_po_line(self, line):
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        res['operating_unit_id'] = line.operating_unit_id.id

        return res

