## User Management

Frappe application to handle user management.

Reach us out at apps@essdee.dev to connect with our team.

### License

GNU/General Public License (v3) (see [license.txt](license.txt))

The User Management code is licensed as GNU General Public License (v3) and the copyright is owned by Essdee Knitting Mills Private Limited (Essdee) and Contributors.

### Status codes used:
1. 401 - Unauthorized.
2. 404 - The requested resource could not be found but may be available in the future.
3. 429 - The user has sent too many requests in a given amount of time.
4. 500 - Internal Server Error.

### API Details:
1. Initiate OTP (Method - Post):
   
   #### Endpoint:

   ```
   /api/method/user_management.user_management.doctype.cd_otp_auth_attempt.cd_otp_auth_attempt.initiate_otp
   ```

   #### Request Body:
   
   {
       "mobile_number": "xxxxxxxxxx"
   }

   #### Response Format:

    200 - { "otp_auth_attempt_name":"aef176ad62"}

    404 - {"message": "User Not Found"}
    
    500 - {"message": "OTP Generation Failed"}

2. Verify OTP (Method - Post):
    
    #### Endpoint:

    ```
    /api/method/user_management.user_management.doctype.cd_otp_auth_attempt.cd_otp_auth_attempt.verify_otp
    ```

    #### Request Body:
    
    {
        "otp_auth_attempt_name": "xxxxxxxxxx",
        "incoming_otp": "1234",
        "action": "get_reset_password_key" or "get_api_credentials"
    }

    #### Response Format:

    200 - action = 'get_reset_password_key'
        
        {"reset_password_key": "N8E4yyJCtQgcPrNaN0v5fWXzdsf"}
    
    200 - action = 'get_api_credentials'
        
        {"api_key":"FDFERT3424dvver3r42","api_secret":"cdfewwr32refgtregw4"}
    
    401 - {"message": "Incorrect OTP"}
    
    429 - {"message": "OTP Expired"} or {"message": "Maximum Limit Reached"}

3. Resend OTP (Method - Post):
    
    #### Endpoint:

    ```
    /api/method/user_management.user_management.doctype.cd_otp_auth_attempt.cd_otp_auth_attempt.resend_otp
    ```

    #### Request Body:

    {
        "otp_auth_attempt_name": "xxxxxxxxxx"
    }

    #### Response Format:

    200 - {"message": "OTP Sent Successfully"}
    
    429 - {"message": "Maximum Limit Reached"}
    
    500 - {"message": "Resend OTP Failed"}
