# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools import float_is_zero


class MrpProductionWorkcenterLineTime(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    cost_already_recorded = fields.Boolean('Cost Recorded', help="Technical field automatically checked when a ongoing production posts journal entries for its costs. This way, we can record one production's cost multiple times and only consider new entries in the work centers time lines.")


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('qc_pass', 'QC Pass'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, default='confirmed', track_visibility='onchange')

    def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
        """
        super(MrpProduction, self)._cal_price(consumed_moves)
        work_center_cost = 0
        finished_move = self.move_finished_ids.filtered(lambda x: x.product_id == self.product_id and x.state not in ('done', 'cancel') and x.quantity_done > 0)
        if finished_move:
            finished_move.ensure_one()
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(lambda x: x.date_end and not x.cost_already_recorded)
                duration = sum(time_lines.mapped('duration'))
                time_lines.write({'cost_already_recorded': True})
                work_center_cost += (duration / 60.0) * work_order.workcenter_id.costs_hour
            if finished_move.product_id.cost_method in ('fifo', 'average'):
                qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done, finished_move.product_id.uom_id)
                finished_move.price_unit = (sum([-m.value for m in consumed_moves]) + work_center_cost) / qty_done
                finished_move.value = sum([-m.value for m in consumed_moves]) + work_center_cost
        return True


    def _prepare_wc_analytic_line(self, wc_line):
        wc = wc_line.workcenter_id
        hours = wc_line.duration / 60.0
        value = hours * wc.costs_hour
        account = wc.costs_hour_account_id.id
        return {
            'name': wc_line.name + ' (H)',
            'amount': -value,
            'account_id': account,
            'ref': wc.code,
            'unit_amount': hours,
        }

    def _costs_generate(self):
        """ Calculates total costs at the end of the production.
        :param production: Id of production order.
        :return: Calculated amount.
        """
        self.ensure_one()
        AccountAnalyticLine = self.env['account.analytic.line']
        amount = 0.0
        for wc_line in self.workorder_ids:
            wc = wc_line.workcenter_id
            if wc.costs_hour_account_id:
                # Cost per hour
                hours = wc_line.duration / 60.0
                value = hours * wc.costs_hour
                account = wc.costs_hour_account_id.id
                if value and account:
                    amount -= value
                    # we user SUPERUSER_ID as we do not guarantee an mrp user
                    # has access to account analytic lines but still should be
                    # able to produce orders
                    AccountAnalyticLine.sudo().create(self._prepare_wc_analytic_line(wc_line))
        return amount

    @api.multi
    def button_mark_done(self):
        self.ensure_one()
        res = super(MrpProduction, self).button_mark_done()
        self._costs_generate()
        return res

    @api.multi
    def button_qc_pass(self):
        return self.write({'state': 'qc_pass'})

    @api.multi
    def fix_post_inventory(self):
        for order in self:
            sum_raw = sum(move.value for move in order.move_raw_ids.filtered(lambda x: abs(x.value) > 0))

            moves_finish_ids = order.move_finished_ids.filtered(lambda x: x.state == 'done')

            if moves_finish_ids.account_move_ids:
                account_move_id = moves_finish_ids.account_move_ids[0]
            else:
                account_move_id = False

            if account_move_id:
                #cancel first
                account_move_id.button_cancel()
                wip_line = account_move_id.line_ids.filtered(lambda x: x.credit)
                if wip_line and len(wip_line) > 1:
                    continue
                fg_line = account_move_id.line_ids.filtered(lambda x: x.debit)
                fg_value = fg_line.debit
                if fg_value < abs(sum_raw):
                    fg_value = abs(sum_raw)

                fg_line.with_context(check_move_validity=False).write({'debit': abs(fg_value)})

                move_raw_ids = order.move_raw_ids.filtered(lambda x: x.state == 'done')
                count = 0

                
                for move in move_raw_ids.filtered(lambda x: abs(x.value) > 0):

                    count +=1
                    if count == 1:
                        wip_line.with_context(check_move_validity=False).write({'credit': abs(move.value),'product_id': move.product_id.id,'quantity': move.product_uom_qty})
                    else:
                        new_line = wip_line.with_context(check_move_validity=False).copy()
                        new_line.with_context(check_move_validity=False).write({'credit': abs(move.value),'product_id': move.product_id.id,'quantity': move.product_uom_qty})
                    fg_value -= abs(move.value)

                if not float_is_zero(fg_value, precision_rounding=0.01):
                    new_line = wip_line.with_context(check_move_validity=False).copy()
                    new_line.with_context(check_move_validity=False).write({'credit': abs(fg_value),'product_id': False,'quantity': 0})

                #post back with credit, debit balance check
                account_move_id.post()



class MrpProductionWAdvance(models.TransientModel):
    _name = 'mrp.production.advance'

    def action_confirm(self):
        context = self._context
        mrp_production_ids = self.env['mrp.production'].browse(context['active_ids'])
        for mrp_production in mrp_production_ids:
            mrp_production.fix_post_inventory()