# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from datetime import date, datetime
from odoo.tools import float_compare, float_is_zero

class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'


    @api.multi
    def auto_compute(self):
        print('bbbbbbbbb')
        asset_all_ids = self.env['account.asset.asset'].search([('category_id','=', self.category_id.id)])
        print(len(asset_all_ids))
        print(asset_all_ids)
        for i in asset_all_ids:
            i.compute_depreciation_board()

    @api.multi
    def check_and_close(self):
        asset_all_ids = self.env['account.asset.asset'].search([('state','=','open')])
        asset_zero_value_ids = asset_all_ids.filtered(lambda x: x.currency_id.is_zero(x.value_residual))
        # print len(asset_zero_value_ids)
        for asset in asset_zero_value_ids:
            # print ('ASSET')
            # print asset.name
            asset.message_post(body=_("Document closed."))
            asset.write({'state': 'close'})

    ###################### Change cron job function to use here instead ##########
    @api.model
    def _cron_generate_entries(self):
        for grouped_category in self.env['account.asset.category'].search([]):
            # print ('-------PER GROUP--')
            # print (grouped_category.name)
            context = self._context
            date_check = []
            date_check.append(datetime.today())
            self.env.cr.execute(
                'SELECT DISTINCT ON (depreciation_date) depreciation_date FROM account_asset_depreciation_line WHERE depreciation_date <= %s ORDER BY depreciation_date',
                (date_check))
            depreciation_date_ids = self.env.cr.dictfetchall()
            ############ split date ###############
            for depreciation_date in depreciation_date_ids:
                self.compute_generated_entries_by_group(depreciation_date['depreciation_date'], asset_type=context.get('asset_type'),group=grouped_category)

    @api.model
    def compute_generated_entries_by_group(self, date, asset_type=None,group=False):
        print ('----NEW by GROUP--')
        # Entries generated : one by grouped category and one by asset from ungrouped category
        created_move_ids = []
        type_domain = []
        if asset_type:
            type_domain = [('type', '=', asset_type)]

        ungrouped_assets = self.env['account.asset.asset'].search(
            type_domain + [('state', '=', 'open'), ('category_id.group_entries', '=', False)])
        created_move_ids += ungrouped_assets._compute_entries(date, group_entries=False)

        for grouped_category in self.env['account.asset.category'].search(type_domain + [('group_entries', '=', True),('id', '=', group.id)]):

            # print ('-----XXXX---')
            assets = self.env['account.asset.asset'].search(
                [('state', '=', 'open'), ('category_id', '=', grouped_category.id)])
            # print len(assets)
            # print ('-----YYYY-----')

            created_move_ids += assets._compute_entries(date, group_entries=True)
        return created_move_ids

    ################ Change geneate date to end depreciation date not date in the request ####
    @api.multi
    def _compute_entries(self, date, group_entries=False):
        # print ('--------COMPUTER ENTRY-----')
        depreciation_ids = self.env['account.asset.depreciation.line'].search([
            ('asset_id', 'in', self.ids), ('depreciation_date', '<=', date),
            ('move_check', '=', False)])
        # print ('---------DEPER TO OPERATE')
        # print (len(depreciation_ids))

        if group_entries:
            if depreciation_ids:
                return depreciation_ids.with_context(
                    depreciation_date=depreciation_ids[0].depreciation_date).create_grouped_move()
        return depreciation_ids.create_move()



    
class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    department_id = fields.Many2one('hr.department', related='asset_id.department_id', string='ชื่อแผนก',store=True)

    @api.multi
    def post_lines_and_close_asset(self):
        # we re-evaluate the assets to determine whether we can close them
        for line in self:
            # line.log_message_when_posted()
            asset = line.asset_id
            # if asset.currency_id.is_zero(asset.value_residual):
                # asset.message_post(body=_("Document closed."))
                # asset.write({'state': 'close'})


    @api.multi
    def create_grouped_move(self, post_move=True):

        print ('NEW GORUP---')
        if not self.exists():
            return []

        created_moves = self.env['account.move']
        category_id = self[0].asset_id.category_id  # we can suppose that all lines have the same category
        depreciation_date = self.env.context.get('depreciation_date') or fields.Date.context_today(self)

        ###
        account_analytic_id = self[0].asset_id.department_id.analytic_account_id
        ##

        amount = 0.0
        for line in self:
            # Sum amount of all depreciation lines
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            amount += current_currency.compute(line.amount, company_currency)

        name = category_id.name + _(' (grouped)')
        move_line_1 = {
            'name': name,
            'account_id': category_id.account_depreciation_id.id,
            'debit': 0.0,
            'credit': amount,
            'journal_id': category_id.journal_id.id,
            'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
        }

        ################### manage multiple expense per analytic account #################
        analytic_group_ids = {}
        move_line_ids = []
        move_line_ids.append((0, 0, move_line_1))
        for line in self:
            # print(line.asset_id.account_analytic_id.name)
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            company = line.asset_id.company_id
            if line.asset_id.department_id.analytic_account_id.id in analytic_group_ids:
                analytic_group_ids[line.asset_id.department_id.analytic_account_id.id]['amount'] += line.amount
            else:
                analytic_group_ids[line.asset_id.department_id.analytic_account_id.id] = {
                    'amount': line.amount,
                }

        for group in analytic_group_ids:
            move_line_temp = {
                'name': name,
                'account_id': category_id.account_depreciation_expense_id.id,
                'credit': 0.0,
                'debit': analytic_group_ids[group]['amount'],
                'journal_id': category_id.journal_id.id,
                'analytic_account_id': group,
                # 'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if category_id.type == 'purchase' else False,
            }
            move_line_ids.append((0, 0, move_line_temp))
        ##################end manage multiple analytic account group####################

        # move_line_2 = {
        #     'name': name,
        #     'account_id': category_id.account_depreciation_expense_id.id,
        #     'credit': 0.0,
        #     'debit': amount,
        #     'journal_id': category_id.journal_id.id,
        #     'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
        # }

        move_vals = {
            'ref': category_id.name,
            'date': depreciation_date or False,
            'journal_id': category_id.journal_id.id,
            'line_ids': move_line_ids,
        }

        move = self.env['account.move'].create(move_vals)
        self.write({'move_id': move.id, 'move_check': True})
        created_moves |= move

        if post_move and created_moves:
            self.post_lines_and_close_asset()
            created_moves.post()
        return [x.id for x in created_moves]

class AssetAssetReport(models.Model):
    _inherit = "asset.asset.report"

    department_id = fields.Many2one('hr.department', string='ชื่อแผนก', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'asset_asset_report')
        self._cr.execute("""
                create or replace view asset_asset_report as (
                    select
                        min(dl.id) as id,
                        dl.name as name,
                        dl.depreciation_date as depreciation_date,
                        a.date as date,
                        (CASE WHEN dlmin.id = min(dl.id)
                          THEN a.value
                          ELSE 0
                          END) as gross_value,
                        dl.amount as depreciation_value,
                        dl.amount as installment_value,
                        (CASE WHEN dl.move_check
                          THEN dl.amount
                          ELSE 0
                          END) as posted_value,
                        (CASE WHEN NOT dl.move_check
                          THEN dl.amount
                          ELSE 0
                          END) as unposted_value,
                        dl.asset_id as asset_id,
                        dl.move_check as move_check,
                        a.category_id as asset_category_id,
                        a.partner_id as partner_id,
                        a.state as state,
                        a.department_id as department_id,
                        count(dl.*) as installment_nbr,
                        count(dl.*) as depreciation_nbr,
                        a.company_id as company_id
                    from account_asset_depreciation_line dl
                        left join account_asset_asset a on (dl.asset_id=a.id)
                        left join (select min(d.id) as id,ac.id as ac_id from account_asset_depreciation_line as d inner join account_asset_asset as ac ON (ac.id=d.asset_id) group by ac_id) as dlmin on dlmin.ac_id=a.id
                    group by
                        dl.amount,dl.asset_id,dl.depreciation_date,dl.name,
                        a.date, dl.move_check, a.state, a.category_id, a.partner_id, a.company_id,
                        a.value, a.id, a.salvage_value, dlmin.id
            )""")


