# -*- coding: utf-8 -*-
import math
from odoo import api, models, fields, _

class WizardCoupon(models.AbstractModel):
    _inherit = 'wizard.coupon'

    is_print = fields.Boolean('Print')

    def get_num_page(self,item,page):
        return int(math.ceil(item / page))

    def set_print_wizard_coupon(self):
        self.is_print = True

    def set_coupon_running(self):
        wizard_coupon = self.env['wizard.coupon'].search(['|',('coupon_running','=',False),('coupon_running','=','New')],limit=100)
        for obj in wizard_coupon:
            coupon_running = self.env['ir.sequence'].next_by_code('wizard.coupon.running') or _('New')
            obj.coupon_running = coupon_running


class WizardCouponProduction(models.Model):
    _inherit = 'wizard.coupon.production'

    def get_lines(self, data, max_line):
        # this function will count number of \n
        line_count = 0
        if data:
            line_count = data.count("\n")
            if not line_count:
                #  print "line 0 - no new line or only one line"
                # lenght the same with line max
                if not len(data) % max_line:
                    line_count = len(data) / max_line
                # lenght not the same with line max
                # if less than line max then will be 0 + 1
                # if more than one, example 2 line then will be 1 + 1
                else:
                    line_count = len(data) / max_line + 1
            elif line_count:
                # print "line not 0 - has new line"
                # print line_count
                # if have line count mean has \n then will be add 1 due to the last row have not been count \n
                line_count += 1
                data_line_s = data.split('\n')
                for x in range(0, len(data_line_s), 1):
                    # print data_line_s[x]
                    if len(data_line_s[x]) > max_line:
                        # print "more than one line"
                        line_count += len(data_line_s[x]) / max_line

            # print("final line : " + str(line_count))
        return line_count

    def get_break_wizard_coupon_delivery(self, item_line, max_body_height, new_line_height, row_line_height, max_line_lenght):
        break_page_line = []
        count_height = 0
        count = 1
        for line in item_line:
            line_height = row_line_height + ((self.get_lines(line.package_id.display_name, max_line_lenght)) * new_line_height)
            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)
        # print(break_page_line)
        return break_page_line