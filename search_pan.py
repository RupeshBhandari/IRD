import requests, re
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
    
    
    def __init__(self, pan_no):
        self.pan_no = pan_no
        self.__token, self.__captcha, self.__cookies_dict = self._get_captcha_and_cookie()
    
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