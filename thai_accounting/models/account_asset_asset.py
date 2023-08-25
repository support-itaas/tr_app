#-*- coding: utf-8 -*-


from odoo import api, fields, models, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import dateutil.parser
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime, timedelta
from decimal import *

def isodd(x):
    return bool(x % 2)

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class account_asset_category(models.Model):
    _inherit = "account.asset.category"

    profit_loss_disposal_account_id = fields.Many2one('account.account',string='Disposal Account')
    salvage_value = fields.Float(string='Default Salvage Value')

class ResCompany(models.Model):
    _inherit = 'res.company'

    asset_depreciation_year = fields.Boolean(string='พิจารณาค่าเสื่อมทุกปีเท่ากัน')

class account_asset_asset(models.Model):
    _inherit = "account.asset.asset"

    # Date: 20/4/2017 Tunyaporn
    barcode = fields.Char(string='Barcode',copy=False,readonly=True, states={'draft': [('readonly', False)]})
    employees_id = fields.Many2one('hr.employee', string='ชื่อพนักงาน')
    department_id = fields.Many2one('hr.department', string='ชื่อแผนก',track_visibility='onchange')
    serial_number = fields.Char(string='Serial Number',readonly=True, states={'draft': [('readonly', False)]})
    note = fields.Text(string='Note')
    purchase_date = fields.Date(string='Purchase Date',readonly=True, states={'draft': [('readonly', False)]})
    asset_purchase_price = fields.Float(string='Purchase Value',readonly=True, states={'draft': [('readonly', False)]})
    depreciated_amount = fields.Float(string='Depreciated Value',readonly=True,compute='get_depreciated_amount')
    asset_disposal_date = fields.Date(string='Disposal Date', readonly=True, states={'draft': [('readonly', False)],'open': [('readonly', False)]})
    # End


    @api.depends('value_residual')
    def get_depreciated_amount(self):
        for asset in self:
            asset.depreciated_amount = asset.asset_purchase_price - asset.salvage_value - asset.value_residual


    @api.model
    def create(self, vals):
        if not vals.get('purchase_date'):
            vals['purchase_date'] = vals.get('date')

        if not vals.get('asset_purchase_price'):
            vals['asset_purchase_price'] = vals.get('value')

        return super(account_asset_asset,self).create(vals)

    def _get_ean_key(self, code):
        code_new = ''
        sum = 0
        length = len(code)
        for i in range(length,12):
            code +='0'

        code = code.replace('-', '')
        for i in range(12):
            num = ''
            if code[i] == '-':
                num = 0
            else:
                num = code[i]

            if isodd(i):
                sum += 3 * int(num)

            else:
                sum += int(num)

            code_new += str(num)
        key = (10 - sum % 10) % 10
        ean13 = code_new + str(key)
        return ean13

    def _generate_ean13_value(self,code):
        ean13 = False

        # reference_code = self.category_id.account_income_recognition_id.code
        # ean = self.env['ir.sequence'].next_by_code('product.code')
        ean13 = self._get_ean_key(code)
        return ean13

    def _get_reference_code(self,category_id):
        reference_code1 = self.env['account.asset.category'].browse(category_id).account_asset_id.code
        reference_code2 = self.env['ir.sequence'].sudo().next_by_code(reference_code1)

        if not reference_code2:
            # print "no sequence then create new one"
            ir_sequence = self.env['ir.sequence']
            # force sequence_id field to new sequence
            vals_seq = {
                'name': self.env['account.asset.category'].browse(category_id).name,
                'code': reference_code1,
                'padding': 4,
                'company_id': self.env.user.company_id.id,
            }
            ir_sequence.sudo().create(vals_seq)
            reference_code2 = self.env['ir.sequence'].sudo().next_by_code(reference_code1)

            # raise UserError(_('Please setting running number of this asset category.'))

        print (reference_code1)
        print (reference_code2)
        if reference_code1 and reference_code2:
            reference_code = reference_code1 + reference_code2
        elif reference_code1 and not reference_code2:
            reference_code = reference_code1
        elif not reference_code1 and reference_code2:
            reference_code = reference_code2
        else:
            reference_code = 'NO-CODE'
        return reference_code

    @api.multi
    def validate(self):
        if not (self.code and self.barcode):
            if not self.code:
                self.code = self._get_reference_code(self.category_id.id)
            if not self.barcode:
                try:
                    self.barcode = self._generate_ean13_value(str(self.code))
                except:
                    self.barcode = self._generate_ean13_value(str(self.id))

        self.write({'state': 'open'})
        fields = [
            'method',
            'method_number',
            'method_period',
            'method_end',
            'method_progress_factor',
            'method_time',
            'salvage_value',
            'invoice_id',
        ]
        ref_tracked_fields = self.env['account.asset.asset'].fields_get(fields)
        for asset in self:
            tracked_fields = ref_tracked_fields.copy()
            if asset.method == 'linear':
                del (tracked_fields['method_progress_factor'])
            if asset.method_time != 'end':
                del (tracked_fields['method_end'])
            else:
                del (tracked_fields['method_number'])
            dummy, tracking_value_ids = asset._message_track(tracked_fields, dict.fromkeys(fields))
            asset.message_post(subject=_('Asset created'), tracking_value_ids=tracking_value_ids)


    def _compute_board_amount(self, sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date):
        amount = 0

        #ถ้าคือรายการสุดท้าย ยอดที่ต้องหักเท่ากับมูลค่าสันทรัพย์ที่เหลือ
        if sequence == undone_dotation_number:
            amount = residual_amount


        #ถ้าไม่ใช้รายการสุดท่าย
        else:
            if self.method == 'linear':
                #ยอดค่าเสือมที่ต้องหักโดยเฉลี่ย = ยอดมูลค่าสินทรัพย์ส่วนที่เหลือ / (จำนวนครั้งที่ต้องหัก - จำนวนครั้งที่หักไปแล้ว)
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))

                #หักโดยการใช้วันสุดท้ายชองเดือน
                if self.prorata:


                    ################ 1) this is first method - cal the whole month of the asset live ###########
                    #self.method_number คือ จำนวนครั้งที่หักค่าเสือม
                    # amount = amount_to_depr / self.method_number
                    # date = datetime.strptime(self.date, '%Y-%m-%d')
                    #
                    # purchase_date = strToDate(self.purchase_date)
                    # end_date = purchase_date + relativedelta(
                    #     years=+(self.category_id.method_number * self.category_id.method_period / 12))
                    # #calculate total depreciation day from purchase date to end date
                    # total_depreciation_day = (end_date - purchase_date).days
                    # #calculate amount depreciation per day
                    # amount_per_day = (self.asset_purchase_price - self.salvage_value) / total_depreciation_day
                    # print total_depreciation_day
                    # print amount_per_day

                    #################### 2) calculate amount per day per year ##############
                    #####################2.1) this is option to consider per day a year or all year equally
                    if calendar.isleap(depreciation_date.year) and not self.env.user.company_id.asset_depreciation_year:
                        total_depreciation_day = 366
                    else:
                        total_depreciation_day = 365


                    amount_per_year = (self.asset_purchase_price - self.salvage_value) * ((float(12) / float(self.category_id.method_number * self.category_id.method_period)))
                    amount_per_day = amount_per_year / total_depreciation_day
                   #print "amount per day"
                    #print depreciation_date.year
                    #print amount_per_year
                    #print total_depreciation_day
                    #print amount_per_day
                    #print "xxxxxxxxxxxxx"



                    if sequence == 1:
                        #print "sequence1"
                        if self.method_period % 12 != 0:
                            # print "--------PER MONTH----"
                            # print "self.method_period % 12 != 0"
                            # date = depreciation_date
                            month_days = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                            days = month_days - strToDate(self.date).day + 1
                            amount = amount_per_day * days
                            # print self.method_period
                            # print month_days
                            # print depreciation_date.day
                            # print strToDate(self.date).day
                            # print depreciation_date
                            # print days
                            # print amount_per_day
                            # print amount
                        else:
                            # print "else self.method_period % 12 != 0"
                            # print "--------PER YEAR----"
                            # print self.company_id.compute_fiscalyear_dates(depreciation_date)['date_to']
                            # print depreciation_date
                            # print strToDate(self.date)
                            days = (depreciation_date-strToDate(self.date)).days + 1
                            # print days
                            # print "------------_END-FIRST EYR"
                            amount = amount_per_day * days
                            # print depreciation_date
                            # print amount_per_day
                            # print days
                            # print amount

                    else:

                        if self.method_period % 12 != 0:
                            # print "PER MONTH"
                            month_days = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                            if depreciation_date.day != month_days:
                                month_days = depreciation_date.day
                            amount = amount_per_day * month_days
                        else:
                            # print "else self.method_period % 12 != 0"
                            # print "--------PER YEAR---222----"
                            # print self.company_id.compute_fiscalyear_dates(depreciation_date)['date_to']
                            if calendar.isleap(depreciation_date.year):
                                days = 366
                            else:
                                days = 365

                            amount = amount_per_day * days


            elif self.method == 'degressive':
                amount = residual_amount * self.method_progress_factor
                if self.prorata:
                    if sequence == 1:
                        if self.method_period % 12 != 0:
                            date = datetime.strptime(self.date, '%Y-%m-%d')
                            month_days = calendar.monthrange(date.year, date.month)[1]
                            days = month_days - date.day + 1
                            amount = (residual_amount * self.method_progress_factor) / month_days * days
                        else:
                            days = (self.company_id.compute_fiscalyear_dates(depreciation_date)['date_to'] - depreciation_date).days + 1
                            amount = (residual_amount * self.method_progress_factor) / total_days * days
        return amount

    def _compute_board_undone_dotation_nb(self, depreciation_date, total_days):
        undone_dotation_number = self.method_number
        if self.method_time == 'end':
            end_date = datetime.strptime(self.method_end, DF).date()
            undone_dotation_number = 0
            while depreciation_date <= end_date:
                depreciation_date = date(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+self.method_period)
                undone_dotation_number += 1
        if self.prorata:
           #if first day is 1, then no need to add antoher period if not add one more
            if depreciation_date.day != 1:
                undone_dotation_number += 1
        return undone_dotation_number

    @api.multi
    def compute_depreciation_board(self):
        self.ensure_one()

        posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
        unposted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_check)

        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

        if self.value_residual != 0.0:
            amount_to_depr = residual_amount = self.value_residual
            if self.prorata:
                # if we already have some previous validated entries, starting date is last entry + method period
                if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
                else:
                    if self.method_period % 12 != 0:
                        depreciation_date = datetime.strptime(self._get_last_depreciation_date()[self.id], DF).date()
                    else:
                        # print "--------"
                        depreciation_date = datetime.strptime(self._get_last_depreciation_date()[self.id], DF).date().replace(month=12, day=31)
            else:
                # depreciation_date = 1st of January of purchase year if annual valuation, 1st of
                # purchase month in other cases
                if self.method_period >= 12:
                    asset_date = datetime.strptime(self.date[:4] + '-01-01', DF).date()
                else:
                    asset_date = datetime.strptime(self.date[:7] + '-01', DF).date()
                # if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
                else:
                    depreciation_date = asset_date
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            # print "depreciation_date1"
            # print depreciation_date

            undone_dotation_number = self._compute_board_undone_dotation_nb(depreciation_date, total_days)

            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                # print "depreciation_date2"
                # print depreciation_date
                sequence = x + 1
                #new function
                month_days = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                depreciation_date_new = date(int(depreciation_date.year), int(depreciation_date.month), int(month_days))

                #this is original
                #amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date)

                amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr, undone_dotation_number,
                                                    posted_depreciation_line_ids, total_days, depreciation_date_new)

                amount = self.currency_id.round(amount)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount

                # month_days = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                # depreciation_date_new = date(int(depreciation_date.year), int(depreciation_date.month), int(month_days))
                # print "new date"
                # print depreciation_date_str

                vals = {
                    'amount': amount,
                    'asset_id': self.id,
                    'sequence': sequence,
                    'name': (self.code or '') + '/' + str(sequence),
                    'remaining_value': residual_amount,
                    'depreciated_value': self.value - (self.salvage_value + residual_amount),
                    'depreciation_date': depreciation_date_new.strftime(DF),
                }
                commands.append((0, False, vals))
                # Considering Depr. Period as months
                depreciation_date = date(year, month, day) + relativedelta(months=+self.method_period)
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year

        self.write({'depreciation_line_ids': commands})

        return True

    @api.multi
    def set_to_close(self):
        move_ids = []
        for asset in self:
            # define the last post date
            today = datetime.today().strftime(DF)
            if self.asset_disposal_date:
                disposal_date = strToDate(self.asset_disposal_date)
            else:
                disposal_date = strToDate(today)

            before_disposal_date = disposal_date + relativedelta(days=-1)

            ######### all unpost before disposal date will be post
            self._compute_entries(before_disposal_date)

            ######## refresh unpost again ########
            unposted_depreciation_line_ids = asset.depreciation_line_ids.filtered(lambda x: not x.move_check)

            if unposted_depreciation_line_ids:
                old_values = {
                    'method_end': asset.method_end,
                    'method_number': asset.method_number,
                }

                # Remove all unposted depr. lines
                commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]
                # print "commands"
                # print commands
                # Create a new depr. line with the residual amount and post it
                sequence = len(asset.depreciation_line_ids) - len(unposted_depreciation_line_ids) + 1

                ################## last post until the day before dispose #########


                #define the last deprecation amount
                if self.value_residual != 0.0:
                    amount_to_depr = residual_amount = self.value_residual

                #define the year and total day of the depreciate date
                year = before_disposal_date.year
                total_days = (year % 4) and 365 or 366

                ###define all post
                posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(
                    key=lambda l: l.depreciation_date)

                ####pending post
                undone_dotation_number = self._compute_board_undone_dotation_nb(before_disposal_date, total_days)

                amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr, undone_dotation_number,
                                                    posted_depreciation_line_ids, total_days, disposal_date)

                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount

                vals_before_disposal = {
                    'amount': amount,  # the last date depreciation amount before dispose
                    'asset_id': asset.id,
                    'sequence': sequence,
                    'name': (asset.code or '') + '/' + str(sequence),
                    'remaining_value': residual_amount,
                    'depreciated_value': self.value - (self.salvage_value + residual_amount),
                    'depreciation_date': disposal_date,
                    'move_check': True
                }
                commands.append((0, False, vals_before_disposal))
                asset.write({'depreciation_line_ids': commands})
                #### update unpost and do post
                unposted_depreciation_line_ids = asset.depreciation_line_ids.filtered(lambda x: not x.move_check)
                unposted_depreciation_line_ids.create_move()

                ### update and clear unpost one more time
                unposted_depreciation_line_ids = asset.depreciation_line_ids.filtered(lambda x: not x.move_check)
                commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]
                ################## end depreciation on dispose date ############
                vals = {
                    'amount': asset.value_residual,
                    'asset_id': asset.id,
                    'sequence': sequence+1,
                    'name': (asset.code or '') + '/' + str(sequence),
                    'remaining_value': 0,
                    'depreciated_value': asset.value - asset.salvage_value,  # the asset is completely depreciated
                    'depreciation_date': disposal_date,
                }
                commands.append((0, False, vals))

                asset.write({'depreciation_line_ids': commands, 'method_end': today, 'method_number': sequence+1})
                tracked_fields = self.env['account.asset.asset'].fields_get(['method_number', 'method_end'])
                changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
                if changes:
                    asset.message_post(subject=_('Asset sold or disposed. Accounting entry awaiting for validation.'),
                                       tracking_value_ids=tracking_value_ids)
                move_ids += asset.depreciation_line_ids[-1].create_move(post_move=False)
        if move_ids:
            name = _('Disposal Move')
            view_mode = 'form'
            if len(move_ids) > 1:
                name = _('Disposal Moves')
                view_mode = 'tree,form'
            return {
                'name': name,
                'view_type': 'form',
                'view_mode': view_mode,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': move_ids[0],
            }

    def _get_asset_summary_by_category(self, category_id):

        domain = [('move_check', '=', True), ('asset_id.state', 'in', ('open', 'close'))]
        if self.date_from:
            domain.append(('depreciation_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('depreciation_date', '<=', self.date_to))
        if self.department_id:
            domain.append(('asset_id.department_id', '<=', self.department_id.id))

        domain.append(('asset_id.category_id', '=', category_id.id))
        depreciation_line_obj = self.env['account.asset.depreciation.line']
        depreciation_line_ids = depreciation_line_obj.search(domain,
                                                             order='category_id asc,asset_id asc,depreciation_date')
        depreciation_lines = {}
        if depreciation_line_ids:
            for line in depreciation_line_ids:
                asset_id = line.asset_id

                if asset_id.id in depreciation_lines:
                    # this is another depreciation line in exsting line
                    depreciation_lines[asset_id.id]['amount'] += line.amount
                else:
                    # last date mean, last post date before search date
                    domain_last_asset = [('move_check', '=', True), ('asset_id', '=', asset_id.id),
                                         ('depreciation_date', '<=', self.date_from)]
                    domain_next_asset = [('move_check', '=', True), ('asset_id', '=', asset_id.id),
                                         ('depreciation_date', '<=', self.date_to)]
                    last_date_record = depreciation_line_obj.search(domain_last_asset, limit=1,
                                                                    order='depreciation_date desc')
                    next_date_record = depreciation_line_obj.search(domain_next_asset, limit=1,
                                                                    order='depreciation_date desc')
                    disposal_date = False
                    # for last record before start date
                    if last_date_record:
                        previous_depreciated_amount = last_date_record.remaining_value
                    else:
                        previous_depreciated_amount = asset_id.value

                    # for last record before or the same with end date that depreciated
                    if next_date_record and next_date_record.remaining_value:
                        next_depreciated_amount = next_date_record.remaining_value
                    elif next_date_record and not next_date_record.remaining_value:
                        next_depreciated_amount = next_date_record.remaining_value
                        disposal_date = next_date_record.depreciation_date
                    else:
                        next_depreciated_amount = asset_id.value_residual

                    number_of_year = (Decimal(asset_id.method_number * asset_id.method_period)) / Decimal(12)
                    if number_of_year:
                        percent = Decimal(100) / number_of_year
                    else:
                        percent = 0
                    depreciation_lines[asset_id.id] = {
                        'name': asset_id.name,
                        'category_id': asset_id.category_id.id,
                        'code': asset_id.code,
                        'purchase_date': asset_id.purchase_date,
                        'date': asset_id.date,
                        'purchase_value': asset_id.asset_purchase_price,
                        'amount': line.amount,
                        'previous_depreciated_amount': previous_depreciated_amount,
                        'next_depreciated_amount': next_depreciated_amount,
                        'percent': percent,
                        'depreciated_value': line.depreciated_value,
                        'remaining_value': line.remaining_value,
                        'disposal_date': disposal_date,
                    }

            depreciation_lines = [value for key, value in depreciation_lines.items()]

        return depreciation_lines

class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    @api.multi
    def create_move(self, post_move=True):
        created_moves = self.env['account.move']
        prec = self.env['decimal.precision'].precision_get('Account')
        if post_move:
            for line in self:
                depreciation_date = self.env.context.get(
                    'depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
                company_currency = line.asset_id.company_id.currency_id
                current_currency = line.asset_id.currency_id
                amount = current_currency.compute(line.amount, company_currency)
                asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
                reference = line.asset_id.code
                journal_id = line.asset_id.category_id.journal_id.id
                partner_id = line.asset_id.partner_id.id
                categ_type = line.asset_id.category_id.type
                debit_account = line.asset_id.category_id.account_depreciation_expense_id.id
                credit_account = line.asset_id.category_id.account_depreciation_id.id
                move_line_1 = {
                    'name': asset_name,
                    'department_id': line.asset_id.department_id.id,
                    'account_id': credit_account,
                    'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
                    'analytic_account_id': line.asset_id.category_id.account_analytic_id.id if categ_type == 'sale' else False,
                    'date': depreciation_date,
                }
                move_line_2 = {
                    'name': asset_name,
                    'department_id': line.asset_id.department_id.id,
                    'account_id': debit_account,
                    'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and line.amount or 0.0,
                    'analytic_account_id': line.asset_id.category_id.account_analytic_id.id if categ_type == 'purchase' else False,
                    'date': depreciation_date,
                }
                move_vals = {
                    'ref': reference,
                    'date': depreciation_date or False,
                    'journal_id': line.asset_id.category_id.journal_id.id,
                    'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                    'asset_id': line.asset_id.id,
                }
                move = self.env['account.move'].create(move_vals)
                line.write({'move_id': move.id, 'move_check': True})
                created_moves |= move

        #this is for sell or disposal
        else:
            for line in self:
                depreciation_date = self.env.context.get(
                    'depreciation_date') or line.depreciation_date or fields.Date.context_today(self)

                date = fields.Date.context_today(self)
                # print "depreciation_date"
                # print depreciation_date
                company_currency = line.asset_id.company_id.currency_id
                current_currency = line.asset_id.currency_id
                amount = current_currency.compute(line.amount + line.asset_id.salvage_value, company_currency)
                sign = (
                       line.asset_id.category_id.journal_id.type == 'purchase' or line.asset_id.category_id.journal_id.type == 'sale' and 1) or -1
                asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids)) + '- Disposal'
                reference = line.asset_id.code
                journal_id = line.asset_id.category_id.journal_id.id
                partner_id = line.asset_id.partner_id.id
                categ_type = line.asset_id.category_id.type

                #original
                # debit_account = line.asset_id.category_id.account_income_recognition_id.id or line.asset_id.category_id.account_asset_id.id
                # credit_account = line.asset_id.category_id.account_depreciation_id.id

                # new
                debit_account = line.asset_id.category_id.account_depreciation_id.id
                credit_account = line.asset_id.category_id.account_asset_id.id
                gain_loss_account = line.asset_id.category_id.profit_loss_disposal_account_id.id


                prec = self.env['decimal.precision'].precision_get('Account')
                move_line_1 = {
                    'name': asset_name,
                    'department_id': line.asset_id.department_id.id,
                    'account_id': credit_account,
                    'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'credit': line.asset_id.value if float_compare(line.asset_id.value, 0.0, precision_digits=prec) > 0 else 0.0,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and - sign * line.amount or 0.0,
                    'analytic_account_id': line.asset_id.category_id.account_analytic_id.id if categ_type == 'sale' else False,
                    'date': date,
                }

                move_line_2 = {
                    'name': asset_name,
                    'department_id': line.asset_id.department_id.id,
                    'account_id': gain_loss_account,
                    'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
                    'analytic_account_id': line.asset_id.category_id.account_analytic_id.id if categ_type == 'purchase' else False,
                    'date': date,
                }
                move_line_3 = {
                    'name': asset_name,
                    'department_id': line.asset_id.department_id.id,
                    'account_id': debit_account,
                    'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                    'debit': (line.asset_id.value - amount) if float_compare((line.asset_id.value - amount), 0.0, precision_digits=prec) > 0 else 0.0,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency != current_currency and current_currency.id or False,
                    'amount_currency': company_currency != current_currency and sign * line.amount or 0.0,
                    'analytic_account_id': line.asset_id.category_id.account_analytic_id.id if categ_type == 'purchase' else False,
                    'date': date,
                }
                move_vals = {
                    'ref': reference,
                    'date': depreciation_date or False,
                    'journal_id': line.asset_id.category_id.journal_id.id,
                    'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2),(0, 0, move_line_3)],
                    'asset_id': line.asset_id.id,
                }

                move = self.env['account.move'].create(move_vals)
                line.write({'move_id': move.id, 'move_check': True})
                created_moves |= move


        if post_move and created_moves:
            created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).post()
        return [x.id for x in created_moves]


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    def asset_create(self):
        if self.asset_category_id:
            for i in range(0,int(self.quantity),1):
                vals = {
                    'name': self.name,
                    'code': self.product_id.default_code or False,
                    'category_id': self.asset_category_id.id,
                    'value': self.price_subtotal_signed/self.quantity,
                    'salvage_value': self.asset_category_id.salvage_value,
                    'partner_id': self.invoice_id.partner_id.id,
                    'company_id': self.invoice_id.company_id.id,
                    'currency_id': self.invoice_id.company_currency_id.id,
                    'date': self.invoice_id.date_invoice,
                    'invoice_id': self.invoice_id.id,
                }
                changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
                vals.update(changed_vals['value'])
                asset = self.env['account.asset.asset'].create(vals)
                if self.asset_category_id.open_asset:
                    asset.validate()
        return True

class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    category_id = fields.Many2one('account.asset.category',related='asset_id.category_id', string='Category ID',store=True)
