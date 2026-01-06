"""
M-Pesa integration module
"""
import requests
import base64
from datetime import datetime
from django.conf import settings


class MPesaClient:
    """Client for M-Pesa STK Push API"""
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.shortcode = settings.MPESA_SHORTCODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        
        # Set base URL based on environment
        if settings.MPESA_ENVIRONMENT == 'production':
            self.base_url = 'https://api.safaricom.co.ke'
        else:
            self.base_url = 'https://sandbox.safaricom.co.ke'
    
    def get_access_token(self):
        """
        Get OAuth access token from M-Pesa API
        """
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        try:
            response = requests.get(
                url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            response.raise_for_status()
            
            json_response = response.json()
            return json_response.get('access_token')
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get M-Pesa access token: {str(e)}")
    
    def generate_password(self, timestamp):
        """
        Generate password for STK push
        Password = Base64(Shortcode + Passkey + Timestamp)
        """
        data_to_encode = f"{self.shortcode}{self.passkey}{timestamp}"
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode('utf-8')
    
    def format_phone_number(self, phone_number):
        """
        Format phone number to M-Pesa format (254XXXXXXXXX)
        Accepts: 0712345678, +254712345678, 254712345678, 712345678
        """
        # Remove spaces and special characters
        phone = ''.join(filter(str.isdigit, phone_number))
        
        # Remove leading zeros
        phone = phone.lstrip('0')
        
        # Add country code if not present
        if not phone.startswith('254'):
            phone = '254' + phone
        
        # Validate length (should be 12 digits: 254XXXXXXXXX)
        if len(phone) != 12:
            raise ValueError("Invalid phone number format")
        
        return phone
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc="Donation to Jambo Rafiki"):
        """
        Initiate STK Push to customer's phone
        
        Args:
            phone_number: Customer phone number (will be formatted)
            amount: Amount to charge (minimum 1)
            account_reference: Donation ID or reference
            transaction_desc: Description of transaction
        
        Returns:
            dict: Response from M-Pesa API
        """
        # Get access token
        access_token = self.get_access_token()
        
        # Format phone number
        formatted_phone = self.format_phone_number(phone_number)
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Generate password
        password = self.generate_password(timestamp)
        
        # Prepare request
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),  # Must be integer
            "PartyA": formatted_phone,
            "PartyB": self.shortcode,
            "PhoneNumber": formatted_phone,
            "CallBackURL": self.callback_url,
            "AccountReference": str(account_reference),
            "TransactionDesc": transaction_desc
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"M-Pesa STK Push failed: {str(e)}")
    
    def query_transaction(self, checkout_request_id):
        """
        Query the status of a transaction
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push
        
        Returns:
            dict: Transaction status
        """
        access_token = self.get_access_token()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self.generate_password(timestamp)
        
        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"M-Pesa query failed: {str(e)}")


def process_mpesa_callback(callback_data):
    """
    Process M-Pesa callback data
    
    Args:
        callback_data: JSON data from M-Pesa callback
    
    Returns:
        dict: Processed callback information
    """
    result = {
        'success': False,
        'transaction_id': None,
        'amount': None,
        'phone_number': None,
        'receipt': None,
        'message': ''
    }
    
    try:
        body = callback_data.get('Body', {})
        stk_callback = body.get('stkCallback', {})
        
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        
        if result_code == 0:
            # Success
            result['success'] = True
            result['message'] = result_desc
            
            # Extract metadata
            callback_metadata = stk_callback.get('CallbackMetadata', {})
            items = callback_metadata.get('Item', [])
            
            for item in items:
                name = item.get('Name')
                value = item.get('Value')
                
                if name == 'Amount':
                    result['amount'] = value
                elif name == 'MpesaReceiptNumber':
                    result['receipt'] = value
                    result['transaction_id'] = value
                elif name == 'PhoneNumber':
                    result['phone_number'] = value
        else:
            # Failed
            result['success'] = False
            result['message'] = result_desc
        
        return result
    
    except Exception as e:
        result['message'] = f"Error processing callback: {str(e)}"
        return result
