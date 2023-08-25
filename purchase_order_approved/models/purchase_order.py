# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[('approved', 'Approved')])
    # TODO: inhterit state but adding approved state in a position after 'to
    # aprove' state.

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
        'approved': [('readonly', True)],
    }

    # Update the readonly states:
    origin = fields.Char(states=READONLY_STATES)
    date_order = fields.Datetime(states=READONLY_STATES)
    partner_id = fields.Many2one(states=READONLY_STATES)
    dest_address_id = fields.Many2one(states=READONLY_STATES)
    currency_id = fields.Many2one(states=READONLY_STATES)
    order_line = fields.One2many(states=READONLY_STATES)
    company_id = fields.Many2one(states=READONLY_STATES)
    picking_type_id = fields.Many2one(states=READONLY_STATES)

    @api.multi
    def button_release(self):
        super(PurchaseOrder, self).button_approve()

    @api.multi
    def button_approve(self, force=False):
        approve_purchases = self.filtered(
            lambda p: p.company_id.purchase_approve_active)
        approve_purchases.write({'state': 'approved'})
        return super(PurchaseOrder, self - approve_purchases).button_approve(
            force=force)

    @api.multi
    def write(self, vals):
        # print("write po")
        res = super(PurchaseOrder, self).write(vals)
        for request in self:
            if vals.get('user_check_id'):
                self.message_subscribe_users(user_ids=[request.user_check_id.id])
        return res

    @api.multi
    def _track_subtype(self, init_values):
        self.ensure_one()
        for rec in self:
            if 'state' in init_values and rec.state == 'draft':
                if rec.user_check_id.id :
                    rec.message_subscribe_users(user_ids=[rec.user_check_id.id])
                return 'purchase_order_approved.mt_rfq_draft'
            if 'user_check_id' in init_values and rec.state == 'draft':
                old_user_check = init_values.get('user_check_id')
                print('old_user_check: ',old_user_check)
                rec.sudo().message_unsubscribe_users(user_ids=[old_user_check.id])
                print('user_check_id: ', rec.user_check_id)
                rec.message_subscribe_users(user_ids=[rec.user_check_id.id])
                print('purchase_order_approved.mt_rfq_draft')
                return 'purchase_order_approved.mt_rfq_draft'
            if 'state' in init_values and rec.state == 'sent':
                if rec.user_check_id.id:
                    rec.message_unsubscribe_users(user_ids=[rec.user_check_id.id])
                if rec.assigned_to.id:
                    rec.message_subscribe_users(user_ids=[rec.assigned_to.id])
                if rec.purchase_type:
                    user_ids = rec.purchase_type.user_ids.ids
                    rec.message_subscribe_users(user_ids=user_ids)
                return 'purchase_order_approved.mt_rfq_sent'
            if 'state' in init_values and rec.state == 'to approve':
                if rec.user_check_id.id:
                    rec.message_unsubscribe_users(user_ids=[rec.user_check_id.id])
                if rec.assigned_to.id:
                    rec.message_subscribe_users(user_ids=[rec.assigned_to.id])
                if rec.purchase_type:
                    user_ids = rec.purchase_type.user_ids.ids
                    rec.message_subscribe_users(user_ids=user_ids)
                return 'purchase.mt_rfq_confirmed'
            if 'state' in init_values and rec.state == 'purchase':
                if rec.assigned_to.id:
                    rec.message_unsubscribe_users(user_ids=[rec.assigned_to.id])
                if rec.purchase_type:
                    user_ids = rec.purchase_type.user_ids.ids
                    rec.message_unsubscribe_users(user_ids=user_ids)
                    user_ids_2_level = rec.purchase_type.user_ids_2_level.ids
                    rec.message_subscribe_users(user_ids=user_ids_2_level)
                return 'purchase.mt_rfq_approved'
            if 'state' in init_values and rec.state == 'cancel':
                return 'purchase_order_approved.mt_rfq_cancel'

            if 'requested_by' in init_values and 'state' not in init_values:
                rec.message_subscribe_users(user_ids=[rec.requested_by.id])
        print('_track_subtype end')
        return super(PurchaseOrder, self)._track_subtype(init_values)


