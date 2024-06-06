IRD PAN Details Retrieval Script
This script is designed to fetch PAN details from the Inland Revenue Department (IRD) of Nepal using the PAN number. It performs the following steps:

Connects to the IRD PAN search page to retrieve a CAPTCHA and a token.
Solves the CAPTCHA.
Uses the token, CAPTCHA, and PAN number to fetch the PAN details.
Requirements
Python 3.x
requests library
You can install the required library using pip:

sh
Copy code
pip install requests
Usage
Running the Script
To run the script, execute the following command:

sh
Copy code
python script_name.py
Replace script_name.py with the actual name of your Python file.

Example
sh
Copy code
python ird_pan_search.py
Script Output
The script logs the process and results to both the console and a log file named search_pan.log.

Script Explanation
IRD Class
Initialization
python
Copy code
def __init__(self, pan_no: int):
Initializes the IRD class with the provided PAN number. Retrieves the CAPTCHA, token, and cookies.

_get_captcha_and_cookie Method
python
Copy code
def _get_captcha_and_cookie(self) -> Tuple[str, int, Dict[str, str]]:
Connects to the IRD PAN search page, retrieves and solves the CAPTCHA, extracts the token and cookies.

get_pan_details Method
python
Copy code
def get_pan_details(self) -> Optional[Dict[str, Any]]:
Uses the retrieved token, CAPTCHA, and cookies to fetch the PAN details from the IRD website.

Logging
Logs are configured to output to both the console and a file named search_pan.log. Logging provides details about each step and any errors encountered.

Code Example
Here's a snippet showing how to use the IRD class:

python
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
Replace 500091452 with the actual PAN number you want to search for.

Error Handling
The script handles HTTP request errors and logs appropriate messages.
If the CAPTCHA or token cannot be found in the response, an error is logged and an exception is raised.
If the response from the IRD server is invalid or empty, an appropriate warning is logged.
License
This project is licensed under the MIT License.

This Markdown-formatted README file provides a comprehensive overview of your script, including installation, usage, and details about its functionality. It should help users understand how to set up and run the script, as well as provide insight into its inner workings.
