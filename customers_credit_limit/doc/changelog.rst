.. _changelog:

Changelog
=========

`Version 0.1 (2018 April 28 01:11)`
---------------------------------
This is the first release for Odoo 11 community and enterprise edition.
- Whats new? 
  - On the customer form, accounting tab, you will see a summary of the customers draft invoices, overdue invoices, confirmed sales orders, receivable taxes, credit limit and if tax is included/excluded in credit limit checking. 
  - Implemented proper multi-currency support. Just make sure your exchange rate is regularly updated.
  - In multi-currency situation, credit limit is computed and checked in local currency
  - In the Sales module settings, you can set a default credit limit (in base currency) to be applied to new customers created in the system. 
  - At the top right corner of the Quotation form, there is a banner informing the user if the quotation will or will not exceed the credit limit if confirmed. The banner will also inform if credit limit is not set (i.e the credit limit is zero)
  - By click of a button, You can notify your sales manager or sales department about the credit limit situation of a sales order or quotation
  - If you have sales manager privileges, you can bypass the credit limit check and confirm the order.
  - At the top right corner of the quotation form, you can see if the customer has overdue invoices. When you click on this status, you will open the overdue invoices for you to review 

