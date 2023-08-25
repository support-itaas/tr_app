from odoo import api, models ,fields
from datetime import datetime
from odoo.exceptions import UserError


class stock_production_lot(models.Model):
    _inherit ='stock.production.lot'

    # create_date = fields.Datetime('Creation Date',compute='get_start_lot_date',stored=True)
    start_lot_date = fields.Datetime(string='Mfg Date')
    # related='create_date', compute='get_start_lot_date'

    @api.onchange('product_id')
    # @api.depends('create_date','start_lot_date')
    @api.multi
    def get_start_lot_date(self):
        if not self.start_lot_date:
            # print '1 self.start_lot_date: ' + str(self.start_lot_date)
            # print self.create_date
            self.start_lot_date = datetime.now()



class stock_picking_operation_pa(models.Model):
    _inherit ='stock.picking'
    # pack_operation_product_ids

    def get_line(self, data, max_line):
        # this function will count number of \n
        # print  data
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
        # print "final line"
        # print line_count
        return line_count


    def get_break_line(self, max_body_height, new_line_height, row_line_height, max_line_lenght):
        break_page_line = []
        count_height = 0
        count = 1

        for line in self.move_lines:
            line_height = row_line_height + ((self.get_line(line.product_id.name, max_line_lenght)) * new_line_height)
            count_height += line_height
            if count_height > max_body_height:
                break_page_line.append(count - 1)
                count_height = line_height
            count += 1
        # last page
        break_page_line.append(count - 1)

        # print break_page_line
        return break_page_line


    @api.multi
    def _getlot_name(self, so_id=False, product_id=False):
        print ('get lot')
        result = []
        before_date = ''
        use_date = ''
        end_life_date = ''
        life_date = ''
        lot_name = ''
        # print ':: '+str(so_id)+' = '+str(product_id)
        # print self.product_id.id
        obj_stock_move = self.env['stock.move'].search(
            [('origin', '=', so_id), ('quant_ids.product_id', '=', product_id.id)], limit=1)
        # print obj_stock_move

        if obj_stock_move.quant_ids:
            for lot in obj_stock_move.quant_ids:
                # print lot
                # print lot.product_id
                # print lot.product_id.name
                # print lot.lot_id.name
                # print lot.lot_id.start_lot_date
                # print lot.lot_id.start_lot_date
                if int(product_id.id) == int(lot.product_id.id):
                    lot_name = lot.lot_id.name
                    #   obj_stock_move.quant_ids.lot_id.name
                    # print lot.lot_id.start_lot_date
                    # print lot.lot_id.life_date
                    if lot.lot_id.start_lot_date:
                        before_date = lot.lot_id.start_lot_date.split(' ')
                        if len(before_date) > 0:
                            use_date = before_date[0]
                        else:
                            use_date = '-'

                    elif not lot.lot_id.start_lot_date:
                        if lot.lot_id.create_date:
                            before_date = lot.lot_id.create_date.split(' ')
                            if len(before_date) > 0:
                                use_date = before_date[0]
                        else:
                            startdates = '0000-00-00'
                    else:
                        use_date = '-'

                    if lot.lot_id.life_date:
                        end_life_date = lot.lot_id.life_date.split(' ')
                        if len(end_life_date) > 0:
                            life_date = end_life_date[0]
                        else:
                            life_date = '-'

                    else:
                        life_date = '0000-00-00'


                startdate = use_date.split('-')
                # print startdate
                if lot.lot_id.start_lot_date:
                    startdates = str(startdate[2]) + '-' + str(startdate[1]) + '-' + str(startdate[0])
                    expdate = life_date.split('-')
                    expdates = str(expdate[2]) + '-' + str(expdate[1]) + '-' + str(expdate[0])
                else:
                    startdates = '0000-00-00'
                    expdates = '0000-00-00'
        else:
            lot_name = '-'
            startdates = '0000-00-00'
            expdates = '0000-00-00'

        result = {'lot_name': lot_name,
                  'before_date': startdates,
                  'end_life_date': expdates,
                  }

        # print result
        return result


