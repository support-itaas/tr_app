# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime,timedelta,date

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class AssetDepreciationConfirmationWizard(models.TransientModel):
    _inherit = "asset.depreciation.confirmation.wizard"

    asset_category_id = fields.Many2one('account.asset.category',string='Category')


    @api.multi
    def asset_compute(self):
        if self.asset_category_id:
            self.ensure_one()
            context = self._context
            date_check = []
            date_check.append(self.date)
            self.env.cr.execute(
                'SELECT DISTINCT ON (depreciation_date) depreciation_date FROM account_asset_depreciation_line WHERE depreciation_date <= %s ORDER BY depreciation_date',
                (date_check))
            depreciation_date_ids = self.env.cr.dictfetchall()
            ############ split date ###############
            for depreciation_date in depreciation_date_ids:
                created_move_ids = self.env['account.asset.asset'].compute_generated_entries_by_group(depreciation_date['depreciation_date'], asset_type=context.get('asset_type'),group=self.asset_category_id)

            return {
                'name': _('Created Asset Moves') if context.get('asset_type') == 'purchase' else _('Created Revenue Moves'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'domain': "[('id','in',[" + ','.join(map(str, created_move_ids)) + "])]",
                'type': 'ir.actions.act_window',
            }
        else:
            return super(AssetDepreciationConfirmationWizard,self).asset_compute()
