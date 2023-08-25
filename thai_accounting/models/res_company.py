# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    branch_no = fields.Char(string='สาขา',default='00000')
    so_version_require = fields.Boolean(string="ต้องการแสดงเวอร์ชั่นในใบเสนอราคา",default=False)
    payment_with_deduct = fields.Boolean(string='Payment With Deduction', default=False)

    eng_address = fields.Char(string='English Address')
    #only some customer for detail of address
    building = fields.Char(string='building', size=64)
    roomnumber = fields.Char(string='roomnumber', size=32)
    floornumber = fields.Char(string='floornumber', size=32)
    village = fields.Char(string='village', size=64)
    house_number = fields.Char(string='house_number', size=20)
    moo_number = fields.Char(string='moo_number', size=20)
    soi_number = fields.Char(string='soi_number', size=24)
    tumbon = fields.Char(string='tumbon', size=24)
    sale_condition = fields.Text(string="เงื่อนไขการรับประกันสินค้า", translate=True)
    payment_info = fields.Text(string="รายละเอียดการชำระเงิน", translate=True)
    discount_amount_condition = fields.Selection([
        ('unit', 'Per Unit'),
        ('total', 'Per Total')
    ], default='total', string="Discount Amount Condition")
    is_sale_vat = fields.Boolean(string="เก็บภาษีขาย",default=True)
    invoice_step = fields.Selection([('1step','Invoice/Tax Invoice'),('2step','Invoice--->Tax Invoice')],default='2step',help='1step is invoice and tax invoice is the same, 2 step is invoice and tax invoice is difference number')
    disable_excel_tax_report = fields.Boolean(string="Disable Tax Report in Excel Format",default=False)
    authorized_amount = fields.Float(string="Sale Authorize Amount",default=1000000.00)
    readonly_date_invoice = fields.Boolean(string='Read only date invoice')
    allow_invoice_backward = fields.Boolean(string='Allow Record Invoice Backward')
    auto_product_code = fields.Boolean(string='Auto Generate Product Code')
    auto_customer_code = fields.Boolean(string='Auto Generate Customer Code')
    auto_supplier_code = fields.Boolean(string='Auto Generate Supplier Code')
    auto_employee_code = fields.Boolean(string='Auto Generate Employee Code')
    auto_product_barcode = fields.Boolean(string='Auto Generate Product Barcode')
    tax_id_require = fields.Boolean(string='Require Tax ID')
    branch_require = fields.Boolean(string='Require Branch')
    allow_cancel = fields.Boolean(string='Allow Cancel')
    show_head_office = fields.Boolean(string='แสดงสำนักงานใหญ่ในรายงาน')
    show_total_tax_report = fields.Boolean(string='แสดงยอดรวมในรายงานภาษี')
    is_head_office = fields.Boolean(string='สำนักงานใหญ่', default=True)

    def get_company_full_address_text(self):
        address = self.get_company_full_address()
        address_text = ' '.join(address)
        return address_text

    def get_company_full_address(self):
        address = []
        # use in qweb company_address = o.company_id.get_company_full_address()
        # <t t-set="company_address" t-value="o.company_id.get_company_full_address()"/>
        # <span t-esc="' '.join([ address for address in company_address ])"/>
        if self.country_id.code == 'TH':
            if self.house_number:
                # address += str(self.house_number) + " "
                address.append(str(self.house_number))
            if self.building:
                # address += 'อาคาร' + str(self.building) + " "
                address.append('อาคาร' + str(self.building))
            if self.roomnumber:
                # address += 'ห้องเลขที่' + str(self.roomnumber) + " "
                address.append('ห้องเลขที่' + str(self.roomnumber))
            if self.floornumber:
                # address += 'ชั้นที่' + str(self.floornumber) + " "
                address.append('ชั้นที่' + str(self.floornumber))
            if self.village:
                # address += 'หมู่บ้าน' + str(self.village) + " "
                address.append('หมู่บ้าน' + str(self.village))

            if self.moo_number:
                # address += 'หมู่ ' + str(self.moo_number) + " "
                address.append('หมู่ ' + str(self.moo_number))
            if self.soi_number:
                # address += 'ซอย' + str(self.soi_number) + " "
                address.append('ซอย' + str(self.soi_number))
            if self.street:
                # address += 'ถนน' + str(self.street) + " "
                address.append('ถนน' + str(self.street))

            if self.street2:
                # address += str(self.street2) + " "
                address.append(str(self.street2))

            if self.state_id and self.state_id.code == 'BKK':
                if self.tumbon:
                    # address += 'แขวง' + str(self.tumbon) + " "
                    address.append('แขวง' + str(self.tumbon))
                if self.city:
                    # address += 'เขต' + str(self.city) + " "
                    address.append('เขต' + str(self.city))

                # address += 'เขต' + str(self.city) + " "
                address.append(str(self.state_id.name))
            else:
                if self.tumbon:
                    # address += 'ตำบล' + str(self.tumbon) + " "
                    address.append('ตำบล' + str(self.tumbon))
                if self.city:
                    # address += 'อำเภอ' + str(self.city) + " "
                    address.append('อำเภอ' + str(self.city))
                address.append('จังหวัด' + str(self.state_id.name))
        else:
            if self.building:
                address.append(str(self.building))
            if self.roomnumber:
                address.append(str(self.roomnumber))
            if self.floornumber:
                address.append(str(self.floornumber))
            if self.village:
                address.append(str(self.village))
            if self.house_number:
                address.append(str(self.house_number))
            if self.moo_number:
                address.append(str(self.moo_number))
            if self.soi_number:
                address.append(str(self.soi_number))
            if self.street:
                address.append(str(self.street))
            if self.street2:
                address.append(str(self.street2))
            if self.tumbon:
                address.append(str(self.tumbon))
            if self.city:
                address.append(str(self.city))
            if self.state_id:
                address.append(str(self.state_id.name))

        if self.zip:
            address.append(str(self.zip))


        return address


