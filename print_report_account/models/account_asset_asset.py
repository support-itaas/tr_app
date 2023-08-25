import time

from setuptools.dist import sequence

from odoo import api, models, fields
from datetime import datetime,timedelta,date
from dateutil.relativedelta import relativedelta
import calendar
import dateutil.parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
import locale

class AccountAssetAssetLine(models.Model):
    _name = 'asset.location.line'
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char('Name')
    date_asset = fields.Date('วันที่ Asset')
    asset_line = fields.Many2one('account.asset.asset', string="Asset Line")
    location_old = fields.Many2one('assets.location',string="Location Old")
    location_new = fields.Many2one('assets.location', string="Location New")
    sequence_location = fields.Char(string="Sequence")


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'


    sequence_num = fields.Char('Sequence')

    @api.multi
    def reset_account_all(self):

        asset_all = self.env['account.asset.asset'].search([('state', '=', 'open'),('category_id','=',self.category_id.id)],limit=300)
        print(len(asset_all))
        print('bbbb')

        for asset in asset_all:
            # print (asset.code)
            asset.sudo().set_to_draft()
            for line in asset.depreciation_line_ids:
                if line.move_id:
                    line.move_id.button_cancel()
                    line.move_id.unlink()
            # asset.sudo().compute_depreciation_board()
            # asset.sudo().validate()
        #
        # self.compute_generated_entries(datetime.today())


    @api.multi
    def reset_account(self):
        for asset in self:
            asset.write({'state': 'draft'})
            for line in asset.depreciation_line_ids:
                if line.move_id:
                    line.move_id.button_cancel()
                    line.move_id.unlink()
            # asset.sudo().compute_depreciation_board()
            # asset.sudo().validate()
            # asset._compute_entries(datetime.today(), group_entries=False)




    @api.model
    def create(self, vals):
        request = super(AccountAssetAsset, self).create(vals)
        request.write({'number': self.env['ir.sequence'].next_by_code('Cash.register'), })

        return request

    number = fields.Char(string='Number')
    date_asset = fields.Date('วันที่ Asset')
    location_ids = fields.One2many('asset.location.line', 'asset_line', string='Location')
    location_new = fields.Many2one('assets.location', string="Location New")

    # @api.onchange('location_new','date_asset')
    @api.multi
    def add_location(self):
        print('111')
        print(self.location_asset)
        if self.location_asset and self.location_new:
            # seq_test = self.env['ir.sequence'].next_by_code('location.asset')

            # test = self.location_asset
            # print(test)

            sequence =  self.env.ref('print_report_account.seq_location_asset_itaas_inherit')
            date_asset = sequence.with_context(ir_sequence_date=self.date_asset).next_by_id() or '/'
            location_idz = []
            for asset in self:
                vals = {
                    'name': self.name,
                    'sequence_location' : date_asset,
                    'location_old': asset.location_asset,
                    'location_new': asset.location_new,
                    'date_asset': asset.date_asset,
                }
                location_idz.append((0, 0, vals))
                print(location_idz)
            self.update({'location_ids': location_idz})

        elif not self.location_asset and self.location_new:
            print('222222222')
            location_idz = []
            for asset in self:
                vals = {
                    'name': self.name,
                    # 'location_old': asset.location_asset,
                    'location_new': asset.location_new,
                }
                location_idz.append((0, 0, vals))
                print(location_idz)
            self.update({'location_ids': location_idz})

    # @api.multi
    # def location(self):
    #     if self.location_asset:
    #         location_idsz = []
    #         for asset12 in self:
    #             vals = {
    #                 'name': asset12.name,
    #                 'location_old': asset12.location_asset.id,
    #                 'location_new': asset12.location_asset.id,
    #             }
    #             print(vals)
    #             location_idsz.append((0, 0, vals))
    #             self.update({'location_ids': location_idsz})


#
#




