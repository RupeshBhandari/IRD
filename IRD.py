import requests, re, json, urllib.parse
from typing import Tuple, Optional, Any, Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("search_pan.log"),  # Log to a file named ird.log
        # logging.StreamHandler()  # Log to the console
    ]
)
logger = logging.getLogger(__name__)

#main class
class IRD():
    SEARCH_URL = 'https://ird.gov.np/pan-search'
    PAN_DETAILS_URL = 'https://ird.gov.np/statstics/getPanSearch'
    LOGIN_URL = "https://taxpayerportal.ird.gov.np/Handlers/E-SystemServices/Taxpayer/TaxPayerValidLoginHandler.ashx"
    RESOURCE_VATRETURN_URL = "https://taxpayerportal.ird.gov.np/Handlers/VAT/VatReturnsHandler.ashx?method=GetVatReturnList"
    
    def __init__(self, pan_no, password=''):
        self.pan_no = pan_no
        self.password = password
        
    
    # get the Captcha first and solve it
    def _get_captcha_and_cookie(self) -> Tuple[str, int, Dict[str, str]]:

        try:
            response = requests.get(self.SEARCH_URL)
            response.raise_for_status()  # Check for HTTP errors
        except requests.RequestException as e:
            logger.error(f"Error connecting to {self.SEARCH_URL} for captcha and cookie and token: {e}")
            raise ValueError(f"Error connecting to {self.SEARCH_URL}: {e}")
        
        cookies_dict = requests.utils.dict_from_cookiejar(response.cookies)
        logger.info("Successfully connected and retrieved cookies.")

            
        captcha_match = re.search(r"What is [0-9]\+[0-9]", response.text)

        token_match = re.search(r'name="_token" value="([^"]+)"', response.text)

        if not captcha_match or not token_match:
            logger.error("Captcha or token not found in the response.")
            raise ValueError("Captcha or token not found.")

        # # Extract the numbers from the expression
        numbers = re.findall(r'\d+', captcha_match.group())
        token_match = re.search(r'[A-Za-z0-9]{40}', token_match.group())
        token_match = token_match.group()


        # # Convert the numbers to integers
        num1, num2 = map(int, numbers)

        token = token_match
        captcha = num1 + num2
        return token, captcha, cookies_dict

    # get the json data using the token, captcha and cookies
    def get_pan_details(self) -> Optional[Dict[str, Any]]:
        # # # Define the login URL and credentials
        self.__token, self.__captcha, self.__cookies_dict = self._get_captcha_and_cookie()
        
        login_payload = {
            "_token": self.__token,
            "pan": self.pan_no,
            "captcha": self.__captcha
        }

        try:
            res = requests.post(url= self.PAN_DETAILS_URL,json=login_payload, cookies= self.__cookies_dict)
            res.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error posting to {self.PAN_DETAILS_URL}: {e}")
            return None

        if res.json() == 0:
            logger.warning("Received an empty response from the server.")
            return None
        
        return res.json()

    
    
    def _check_login(self):
        login_payload = {
            "pan": self.pan_no,
            "TPName": self.pan_no,
            "TPPassword": self.password,
            "formToken": "a",
            "pIP": "27.34.68.199",
            "LoginType": "NOR"
        }
        
        # Create a session to persist cookies across requests
        self.session = requests.Session()

            # Step 1: Send a POST request to the login page
        login_response = self.session.post(self.LOGIN_URL, data=login_payload)
        if not "User Login Succcessful" in login_response.text:
            print("login unsucesful")
            return False
        
        return True
    
    def _get_resource_vatreturn(self):
        
         # Step 2: Make a GET request to the desired resource
        resource_response = self.session.get(self.RESOURCE_VATRETURN_URL)
        if not resource_response.status_code == 200:
            return None
        
        # Remove everything before the first "[" and after the last "]"
        json_start = resource_response.text.find("[")
        json_end = resource_response.text.rfind("]")
        trimmed_json = resource_response.text[json_start:json_end + 1]

        # Parse the trimmed JSON
        original_data = json.loads(trimmed_json)

        # Initialize a list to store the additional JSON responses
        additional_responses = []

        # Create a dictionary to store the merged data
        merged_data = {}
        
        final_data = {}

        for item in original_data:
            # Get the SubmissionNo from the original JSON response
            submission_no = item.get("SubmissionNo")
            if submission_no:
                # Construct the URL for the additional JSON response
                additional_url = f"https://taxpayerportal.ird.gov.np/Handlers/Vat/VatReturnsHandler.ashx?method=GetVatReturn&SubNo={submission_no}"
                # print(additional_url)

                # Make a GET request to the additional URL
                additional_response = self.session.get(additional_url)
                if additional_response.status_code == 200:
                    # Remove everything before the first "[" and after the last "]"
                    json_start = additional_response.text.find(":{")
                    json_end = additional_response.text.rfind("},")
                    trimmed_json = additional_response.text[json_start:json_end + 1][1:]
                    trimmed_json = "[" + trimmed_json + "]"


                    # Parse the trimmed JSON
                    additional_data = json.loads(trimmed_json)

                    # Populate the merged_data dictionary
                    for entry in original_data:
                        submission_no = entry["SubmissionNo"]
                        merged_data[submission_no] = entry

                    for entry in additional_data:
                        submission_number = entry["SubmissionNumber"]
                        if submission_number in merged_data:
                            merged_data[submission_number].update(entry)



    # Convert the merged_data dictionary to a list of merged entries
        # merged_data_list = list(merged_data.values())
        json_data = json.dumps(merged_data)
        return json_data
    
    
    def get_vat_details(self):
        if not self._check_login():
            return None    
        return self._get_resource_vatreturn()
        
    def get_etds_details(self):
        if not self._check_login():
            return None
        #get today's date
        dateresponse = requests.get("https://taxpayerportal.ird.gov.np/Handlers/Common/DateHandler.ashx?method=GetCurrentDate")
        match = re.search(r'"NepaliDate":"(\d{4}\.\d{2}\.\d{2})"', dateresponse.text)
        nepali_date = match.group(1)
        nepali_date = nepali_date[:10]

        # Check if the login was successful based on the response content
        base_url = "https://taxpayerportal.ird.gov.np/Handlers/TDS/GetTransactionHandler.ashx"
        # Define the payload data
        payload = {
            "method": "GetWithholderRecs",
            "_dc": "1706364195083",
            "objWith": '{"WhPan":"304460847","FromDate":"2060.01.01","ToDate":"2080.07.04"}',
            "page": 1,
            "start": 0,
            "limit": 25
        }
        # Assign the value of "nepali_date" to the "ToDate" key in the payload
        payload["objWith"] = payload["objWith"].replace('"ToDate":"2080.07.04"', f'"ToDate":"{nepali_date}"')
        payload["objWith"] = payload["objWith"].replace('"WhPan":"304460847"', f'"WhPan":"{self.pan_no}"')
        # Encode the payload as a query string
        encoded_payload = urllib.parse.urlencode(payload)
        resource_url = f"{base_url}?{encoded_payload}"
        # Define the resource URL you want to access after login
        print(resource_url)
        # Step 2: Make a GET request to the desired resource
        resource_response = self.session.get(resource_url)
        if resource_response.status_code == 200:
            # Remove everything before the first "[" and after the last "]"
            json_start = resource_response.text.find("[")
            json_end = resource_response.text.rfind("]")
            trimmed_json = resource_response.text[json_start:json_end + 1]
            # Parse the trimmed JSON
            original_data = json.loads(trimmed_json)
        else:
            print("List of Submission Number Not Obtained")


        ### getting the TRANSACTION DETAILS
        # Initialize an empty list to store the transactionInfo
        transactionInfo = []

        # Loop through each item in the original_data
        for item in original_data:
            TranNo = item["TranNo"]

            # Define the payload
            payload = {
                "method": "GetTrans",
                "objIns": {
                    "TransNo": TranNo,
                    "RecStatus": "V",
                    "FromDate": "1",
                    "ToDate": "500"
                },
                "formToken": "a"
            }

            # Define the URL
            base_url = "https://taxpayerportalb.ird.gov.np:8081/Handlers/TDS/InsertTransactionHandler.ashx"

            # Encode the payload as a query string
            encoded_payload = urllib.parse.urlencode(payload)
            resource_url = f"{base_url}?{encoded_payload}"

            # Define the resource URL you want to access after login
            print(resource_url)

            try:
                # Send a POST request to the URL with the payload
                response = requests.post(resource_url)
                print(response)

                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                # Remove everything before the first "[" and after the last "]"
                    json_start = response.text.find("[")
                    json_end = response.text.rfind("]")
                    trimmed_json = response.text[json_start:json_end + 1]

                    # Parse the trimmed JSON
                    each_response = json.loads(trimmed_json)
                    #print(each_response)

                    # Append the response to the transactionInfo list
                    transactionInfo.append(each_response)

                else:
                    print(f"Request for TranNo {TranNo} failed with status code {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Request for TranNo {TranNo} failed with an exception: {e}")

        # At this point, transactionInfo contains the JSON responses for each TranNo
        # You can access the data as needed

        # Initialize an empty list to store the formatted data
        formatted_data = []

        # Extract column names dynamically from the JSON data
        if transactionInfo:
            columns = set()
            for level1_item in transactionInfo:
                for level2_item in level1_item:
                    columns.update(level2_item.keys())

            # Create a list of dictionaries with dynamic column names
            for level1_item in transactionInfo:
                for level2_item in level1_item:
                    formatted_item = {"Level 1": level2_item.get("RowNumber")}
                    for column in columns:
                        formatted_item[column] = level2_item.get(column)
                    formatted_data.append(formatted_item)

        return formatted_data
    
if __name__ == '__main__':
    try:
        ird_instance = IRD(pan_no=500091452)
        pan_details = ird_instance.get_pan_details()
        if pan_details:
            logger.info(f"PAN details: {pan_details}")
        else:
            logger.warning("PAN details could not be retrieved.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")