import logging
from lxml import etree, html
from odoo import api, models

_logger = logging.getLogger(__name__)

class account_invoice_inherit(models.Model):
    _inherit = "account.invoice"


    # @api.onchange('account_note')
    # def account_note_txt(self):
    #     max_char = 120
    #     txt = str(self.account_note)
    #     print(self.account_note)
    #     print(len(txt))
    #     i=1
    #     # txt2 = '1111111'+'\n'+'ddddd'
    #     txt2 = ''
    #     # for x in txt[0:120]:
    #     #     if x != '\n':
    #     #         if i<=39:
    #     #             txt2 += x
    #     #         else:
    #     #             txt2 += '\n'+x
    #     #             i = 1
    #     #     i+=1
    #     # print(txt2)
    #     self.account_note = txt2
    #     # self.some_method(txt)

    @api.multi
    def some_method(self,txt):
        # Get truncated text from an HTML field. It will 40 words and 100
        # characters at most, and will have "..." appended at the end if it
        # gets truncated.
        truncated_text = self.env["ir.fields.converter"].text_from_html(self.account_note, 2, 30, "...")
        print('truncated_text..')
        print(truncated_text)
        print('truncated_text')