# -*- coding: utf-8 -*-
from odoo import api,fields, models




class stock_product_lot(models.Model):
    _inherit ='account.move'


    def print_account(self):

        # print ('----------print_account')
        journal_item = []
        journal_ids = []

        # print len(self.line_ids)

        move_line_ids = self.get_payment_invoice()
        if move_line_ids:
            print ('5555')
            new_move_line_ids = self.line_ids + move_line_ids
        else:
            new_move_line_ids = self.line_ids
        # print ('---------------------')
        # print move_line_ids
        # print ('--------ALL')
        # print len(new_move_line_ids)

        if new_move_line_ids:
            for line in new_move_line_ids:
                print ('--------------------------------------')
                print (line.id)
                account_id_code = line.account_id.code
                account_id_name = line.account_id.name
                department_id_name = line.department_id.name
                account_id_label = line.name

                # print ('^^^^^^^^^^^^^^^^^^^^^^^')
                # print(account_id_name)
                # print(account_id_code)
                # print line.department_id.name
                # print line.debit
                # print line.credit
                # print ('--------------------')



                ##############This is per line - change to group by account code jatupong - 23-04-2020 ##########
                # value = {'account_id_name': account_id_name,
                #          'account_id_code': account_id_code,
                #          'department_id_name': department_id_name,
                #          'account_id_label': account_id_label,
                #          'debit': line.debit,
                #          'credit': line.credit}
                # journal_item.append(value)
                ############################################################################

                ############################################### Check duplicate account code to one line ###################
                # val_new = {
                #     'account_id_code': account_id_code,
                #     'department_id_name':department_id_name,
                # }


                if account_id_code not in journal_ids:
                    print ('-NEW')
                    journal_ids.append(account_id_code)

                    value = {'account_id_name': account_id_name,
                             'account_id_code': account_id_code,
                             'department_id_name':department_id_name,
                             'account_id_label': account_id_label,
                             'debit': line.debit,
                             'credit': line.credit}

                    journal_item.append(value)

                ############## same account, then consider department ##########3
                else:
                    print ('EXIST ACCOUNT')
                    same_account_same_department_id = False
                    ############# has department #########
                    if line.department_id:
                        print ('YES DEPT:')
                        # print (line.department_id.name)
                        ############ USE to get record with same department of new line ##########
                        same_account_same_department_id = list(
                            filter(lambda x: x['department_id_name'] == (line.department_id.name) and x['account_id_code'] == (account_id_code), journal_item))

                        ############ has department and found the same dept ##########
                        if same_account_same_department_id:
                            print ('-SAME ACCOUNT and SAME DEPT')
                            match_same_account_same_department_same_debit_same_credit = False

                            for count in range(0,len(same_account_same_department_id)):
                                ############ has department and found the same dept and same debit value ##########
                                if same_account_same_department_id[count]['debit'] and line.debit:
                                    print ('------SAME DEBIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_debit = same_account_same_department_id[count]['debit']
                                    new_debit = old_debit + line.debit
                                    same_account_same_department_id[count]['debit'] = new_debit
                                    print (same_account_same_department_id[count]['debit'])

                                ############ has department and found the same dept and same credit value ##########
                                elif same_account_same_department_id[count]['credit'] and line.credit:
                                    print ('------SAME CREDIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_credit = same_account_same_department_id[count]['credit']
                                    new_credit = old_credit + line.credit
                                    same_account_same_department_id[count]['credit'] = new_credit
                                    print (same_account_same_department_id[count]['credit'])


                            #########################if not same debit, credit
                            if not match_same_account_same_department_same_debit_same_credit:
                                print ('------DIFF DEBIT-CREDIT')
                                journal_ids.append(account_id_code)
                                value = {'account_id_name': account_id_name,
                                         'account_id_code': account_id_code,
                                         'department_id_name': department_id_name,
                                         'account_id_label': account_id_label,
                                         'debit': line.debit,
                                         'credit': line.credit}

                                journal_item.append(value)

                        ############ has department but could not found the same dept ##########
                        else:
                            # print ('2222')
                            print ('-SAME ACCOUNT, NEW DEP')
                            journal_ids.append(account_id_code)
                            value = {'account_id_name': account_id_name,
                                     'account_id_code': account_id_code,
                                     'department_id_name': department_id_name,
                                     'account_id_label': account_id_label,
                                     'debit': line.debit,
                                     'credit': line.credit}

                            journal_item.append(value)


                    ################### NO department and same account
                    else:
                        print ('NO-DEP, SAME ACCOUNT')
                        same_account_no_department_id = list(
                            filter(lambda x: x['account_id_code'] == (line.account_id.code) and not x['department_id_name'], journal_item))
                        # print ('-SAME - NO DEPT')
                        # print (same_account_no_department_id)
                        ################### if found same account and found no department ###########
                        if same_account_no_department_id:
                            print ('SAME ACCOUNT and NO DEP')
                            match_same_account_same_department_same_debit_same_credit = False
                            for count in range(0,len(same_account_no_department_id)):

                                ############ same debit
                                if same_account_no_department_id[count]['debit'] and line.debit:
                                    print ('------SAME DEBIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_debit = same_account_no_department_id[count]['debit']
                                    new_debit = old_debit + line.debit
                                    same_account_no_department_id[count]['debit'] = new_debit
                                    print (same_account_no_department_id[count]['debit'])

                                ############ same credit
                                elif same_account_no_department_id[count]['credit'] and line.credit:
                                    print ('------SAME CREDIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_credit = same_account_no_department_id[count]['credit']
                                    new_credit = old_credit + line.credit
                                    same_account_no_department_id[count]['credit'] = new_credit
                                    print (same_account_no_department_id[count]['credit'])

                            if not match_same_account_same_department_same_debit_same_credit:
                                ############ not the same debit, credit
                                print ('------DIFF DEBIT-CREDIT')
                                value = {'account_id_name': account_id_name,
                                         'account_id_code': account_id_code,
                                         'department_id_name': department_id_name,
                                         'account_id_label': account_id_label,
                                         'debit': line.debit,
                                         'credit': line.credit}

                                journal_item.append(value)

                        ##################### in case same account but not found no department #######
                        else:
                            print ('NO DEP, SAME ACCOUNT')
                            value = {'account_id_name': account_id_name,
                                     'account_id_code': account_id_code,
                                     'department_id_name': department_id_name,
                                     'account_id_label': account_id_label,
                                     'debit': line.debit,
                                     'credit': line.credit}

                            journal_item.append(value)

        return journal_item



    def get_journal_item_account(self):

        # print ('----------print_account')
        journal_item = []
        journal_ids = []
        new_move_line_ids = self.line_ids
        # print ('---------------------')
        # print move_line_ids
        # print ('--------ALL')
        # print len(new_move_line_ids)

        if new_move_line_ids:
            for line in new_move_line_ids:
                print ('--------------------------------------')
                print (line.id)
                account_id_code = line.account_id.code
                account_id_name = line.account_id.name
                department_id_name = line.department_id.name
                partner_id_name = line.partner_id.name
                account_id_label = line.name

                if account_id_code not in journal_ids:
                    # print ('-NEW')
                    # print account_id_code
                    journal_ids.append(account_id_code)

                    value = {'account_id_name': account_id_name,
                             'account_id_code': account_id_code,
                             'department_id_name':department_id_name,
                             'partner_id_name': partner_id_name,
                             'account_id_label': account_id_label,
                             'debit': line.debit,
                             'credit': line.credit}

                    journal_item.append(value)

                ############## same account, then consider department ##########3
                else:
                    print ('EXIST ACCOUNT')
                    same_account_same_department_id = False
                    ############# has department #########
                    if line.department_id:
                        print ('YES DEPT:')
                        # print (line.department_id.name)
                        ############ USE to get record with same department of new line ##########
                        same_account_same_department_id = list(
                            filter(lambda x: x['department_id_name'] == (line.department_id.name) and x['account_id_code'] == (account_id_code), journal_item))

                        ############ has department and found the same dept ##########
                        if same_account_same_department_id:
                            print ('-SAME ACCOUNT and SAME DEPT')
                            match_same_account_same_department_same_debit_same_credit = False

                            for count in range(0,len(same_account_same_department_id)):
                                ############ has department and found the same dept and same debit value ##########
                                if same_account_same_department_id[count]['debit'] and line.debit:
                                    print ('------SAME DEBIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_debit = same_account_same_department_id[count]['debit']
                                    new_debit = old_debit + line.debit
                                    same_account_same_department_id[count]['debit'] = new_debit
                                    # print (same_account_same_department_id[count]['debit'])

                                ############ has department and found the same dept and same credit value ##########
                                elif same_account_same_department_id[count]['credit'] and line.credit:
                                    print ('------SAME CREDIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_credit = same_account_same_department_id[count]['credit']
                                    new_credit = old_credit + line.credit
                                    same_account_same_department_id[count]['credit'] = new_credit
                                    # print (same_account_same_department_id[count]['credit'])


                            #########################if not same debit, credit
                            if not match_same_account_same_department_same_debit_same_credit:
                                print ('------DIFF DEBIT-CREDIT')
                                journal_ids.append(account_id_code)
                                value = {'account_id_name': account_id_name,
                                         'account_id_code': account_id_code,
                                         'department_id_name': department_id_name,
                                         'partner_id_name': partner_id_name,
                                         'account_id_label': account_id_label,
                                         'debit': line.debit,
                                         'credit': line.credit}

                                journal_item.append(value)

                        ############ has department but could not found the same dept ##########
                        else:
                            # print ('2222')
                            print ('-SAME ACCOUNT, NEW DEP')
                            journal_ids.append(account_id_code)
                            value = {'account_id_name': account_id_name,
                                     'account_id_code': account_id_code,
                                     'department_id_name': department_id_name,
                                     'partner_id_name': partner_id_name,
                                     'account_id_label': account_id_label,
                                     'debit': line.debit,
                                     'credit': line.credit}

                            journal_item.append(value)


                    ################### NO department and same account
                    else:
                        print ('NO-DEP, SAME ACCOUNT')
                        # print account_id_code
                        same_account_no_department_id = list(
                            filter(lambda x: x['account_id_code'] == (line.account_id.code) and not x['department_id_name'], journal_item))
                        # print ('-SAME - NO DEPT')
                        # print (same_account_no_department_id)
                        ################### if found same account and found no department ###########
                        if same_account_no_department_id:
                            print ('SAME ACCOUNT and NO DEP')
                            match_same_account_same_department_same_debit_same_credit = False
                            for count in range(0,len(same_account_no_department_id)):

                                ############ same debit
                                if same_account_no_department_id[count]['debit'] and line.debit:
                                    print ('------SAME DEBIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_debit = same_account_no_department_id[count]['debit']
                                    new_debit = old_debit + line.debit
                                    same_account_no_department_id[count]['debit'] = new_debit
                                    # print (same_account_no_department_id[count]['debit'])

                                ############ same credit
                                elif same_account_no_department_id[count]['credit'] and line.credit:
                                    print ('------SAME CREDIT')
                                    match_same_account_same_department_same_debit_same_credit = True
                                    old_credit = same_account_no_department_id[count]['credit']
                                    new_credit = old_credit + line.credit
                                    same_account_no_department_id[count]['credit'] = new_credit
                                    # print (same_account_no_department_id[count]['credit'])

                            if not match_same_account_same_department_same_debit_same_credit:
                                ############ not the same debit, credit
                                print ('------DIFF DEBIT-CREDIT')
                                value = {'account_id_name': account_id_name,
                                         'account_id_code': account_id_code,
                                         'department_id_name': department_id_name,
                                         'partner_id_name': partner_id_name,
                                         'account_id_label': account_id_label,
                                         'debit': line.debit,
                                         'credit': line.credit}

                                journal_item.append(value)

                        ##################### in case same account but not found no department #######
                        else:
                            print ('NO DEP, SAME ACCOUNT')
                            value = {'account_id_name': account_id_name,
                                     'account_id_code': account_id_code,
                                     'department_id_name': department_id_name,
                                     'partner_id_name': partner_id_name,
                                     'account_id_label': account_id_label,
                                     'debit': line.debit,
                                     'credit': line.credit}

                            journal_item.append(value)

        print ('-----END---')
        print (journal_item)
        return journal_item


