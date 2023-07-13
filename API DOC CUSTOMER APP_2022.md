<!-- /!\ do not modify above this line -->

# Date : 11-Jan-2023

# Odoo version :11.0CE

# Api version :1.0.8

TEST CREDENTIALS

URL : https://odoo11ce.technaureus.com <br/>
DATABASE : wiz_140422_thai <br/>
USER : admin <br/>
PASSWORD : tis@wizthai <br/>

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

1.REDEEM COUPON API : This api redeems a coupon.
----------------

| REQUIREMENTS       | EXPECTED DATA                                                                                                                                                                                                                                                                                                                                    |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| URL                | http://IPADDRESS/web/dataset/call                                                                                                                                                                                                                                                                                                                |
| METHOD             | GET                                                                                                                                                                                                                                                                                                                                              |
| REQUEST            | {"jsonrpc":"2.0","method":"call","id":2,"params":{"model":"wizard.shop.api","method":"redeem_coupon","args":["",{"customer":15, "service":15, "branch":1, "plate_number":1}]}}</br></br>ID: Authenticated user ID</br>CUSTOMER: Id of Customer</br>SERVICE: Id of selected service</br>BRANCH: Id of branch</br>PLATE NUMBER: Id of plate number |
| RESPONSE (success) | {"jsonrpc": "2.0","id": 2,"result": {"success": "true","message": "Coupon CPN/2022/0003 is successfully redeemed","data": {"coupon": 3}}}</br></br>success: true if success else false</br>message: Reason if failed</br>                                                                                                                        |  
| RESPONSE (failed)  | return {"success": "false", "message": "Please provide service id id in parameter", "data": []}</br></br>Response you will get if the service is not valid                                                                                                                                                                                       |  
| RESPONSE (failed)  | return {"success": "false", "message": "Please provide customer id in parameter", "data": []}</br></br>Response you will get if the customer is not valid                                                                                                                                                                                        |  
| RESPONSE (failed)  | return {"success": "false", "message": "Please provide branch id in parameter", "data": []}</br></br>Response you will get if the branch is not valid                                                                                                                                                                                            |  
| RESPONSE (failed)  | return {"success": "false", "message": "Please provide plate number id in parameter", "data": []}</br></br>Response you will get if the plate number is not valid                                                                                                                                                                                |  
| RESPONSE (failed)  | return {"success": "false", "message": "no coupons found", "data": []}</br></br>Response you will get if no coupons found                                                                                                                                                                                                                        |  

2.FETCH ONLINE QR CODE API : This api generates dynamic qr code.
----------------

| REQUIREMENTS       | EXPECTED DATA                                                                                                                                                                                                                                                                                                   |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| URL                | http://IPADDRESS/web/dataset/call                                                                                                                                                                                                                                                                               |
| METHOD             | GET                                                                                                                                                                                                                                                                                                             |
| REQUEST            | {"jsonrpc":"2.0","method":"call","id":2,"params":{"model":"wizard.shop.api","method":"fetch_online_qr_code","args":["",{"order":1}]}}</br></br>ID: Authenticated user ID</br>Order: Id of order                                                                                                                 |
| RESPONSE (success) | {"jsonrpc": "2.0","id": 2,"result": {"success": "true","message": "Qr code generated","data": [{"qr_raw_data": raw data,"qr_image": image in base64}],"payment_amount": "10"}]}}</br></br>success: true if success else false</br>message: Reason if failed</br>data: Qr code image in base64 and raw data</br> |  
| RESPONSE (failed)  | {"success": "false", "message": "Order not found", "data": []}</br></br>Response you will get if the order doesn't exist                                                                                                                                                                                        |

3.PLACE ORDER : This api place an order.
----------------

| REQUIREMENTS       | EXPECTED DATA                                                                                                                                                                                                                                                                                                                                                                                                                              |
|--------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| URL                | http://IPADDRESS/web/dataset/call                                                                                                                                                                                                                                                                                                                                                                                                          |
| METHOD             | GET                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| REQUEST            | {"jsonrpc":"2.0","method":"call","id":2,"params":{"model":"pos.order","method":"place_order","args":["",15, 2,0,[{"product_id": 15,"qty": 1,"price_unit":444},{"product_id": 19,"qty": 1,"price_unit":680}], 414]}}</br></br>ID: Authenticated user ID</br>PARTNER: Id of partner</br>BRANCH: branch id</br>USE WALLET: 0 if false 1 if true</br>ORDER LINES: pass required orderline data</br>ORDER ID: order id that needs to be updated |
| RESPONSE (success) | {"jsonrpc": "2.0","id": 2,"result": {"success": "true","message": "Order Updated","data": [{"order_id": 418}]}}</br>ORDER ID: updated order id                                                                                                                                                                                                                                                                                             |  
| RESPONSE (success) | {'success': "true", "message": "order placed","data": [{"order_id": 418}]})</br>ORDER ID: new created order id                                                                                                                                                                                                                                                                                                                             |  
| RESPONSE (failed)  | {"success": "false", "message": "order not found","data": []}</br></br>Response you will get if the order doesn't exist                                                                                                                                                                                                                                                                                                                    |
| RESPONSE (failed)  | {"success": "false", "message": "expiry not set","data": []}</br></br>Response you will get if the expiry not not set for an order                                                                                                                                                                                                                                                                                                         |
|

4.PAYMENT RESULT API : This api returns the response whether a payment is success or not.
----------------

| REQUIREMENTS       | EXPECTED DATA                                                                                                                                                                                                   |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| URL                | http://IPADDRESS/web/dataset/call                                                                                                                                                                               |
| METHOD             | GET                                                                                                                                                                                                             |
| REQUEST            | {"jsonrpc":"2.0","method":"call","id":2,"params":{"model":"wizard.customer.api","method":"customer_payment_result","args":["",{"order":9}]}}</br></br>ID: Authenticated user ID</br>ORDER_ID: Id of order Order |
| RESPONSE (success) | {"jsonrpc": "2.0","id": 2,"result": {"success": "true","message": "Payment done for Main/0024","data": []}}</br></br>success: true if success else false</br>message: Reason if failed</br>                     |  
| RESPONSE (failed)  | {"jsonrpc": "2.0","id": 2,"result": {"success": "false","message": "Payment pending for order Main/0027","data": []}}</br></br>Response you will get if the payment is pending for the order                    |  
| RESPONSE (failed)  | {"jsonrpc": "2.0","id": 2,"result": {"success": "false","message": "Payment failed for order Main/0027","data": []}}</br></br>Response you will get if the payment is failed for the order                      |  
| RESPONSE (failed)  | {"jsonrpc": "2.0","id": 2,"result": {"success": "false","message": "Please provide a valid order id","data": []}}</br></br>Response you will get if the order is not valid                                      |  


5.CONFIG DATAS API : This api returns configuration datas.
----------------

| REQUIREMENTS       | EXPECTED DATA                                                                                                                                                                       |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| URL                | http://IPADDRESS/web/dataset/call                                                                                                                                                   |
| METHOD             | GET                                                                                                                                                                                 |
| REQUEST            | {"jsonrpc":"2.0","method":"call","id":2,"params":{"model":"installment.api","method":"get_config_datas","args":[""]}}</br></br>ID: Authenticated user ID</br>                       |
| RESPONSE (success) | {"jsonrpc": "2.0","id": 2,"result": {"success": "true","message": "Datas retrieved","data": {"gbpay_install_min_amount": 2500.0}}}</br></br>Response you will get if there is datas |  
| RESPONSE (failed)  | {"jsonrpc": "2.0","id": 2,"result": {"success": "false","message": "No datas retrieved","data": []}}</br></br>Response you will get if there is no datas                            |  
