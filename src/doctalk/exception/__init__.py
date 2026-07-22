import sys

def error_message_detail(error, error_detail:sys):
    '''
    This function's job is to give out the error in clean string format with mentioning file_name, line_number, error_message.
    It uses error_detail which is a sys module which gives us live traceback through sys.exc_info()
    '''
    # exc_info returns (type, value, traceback), we want the traceback
    _,_,exc_tb = error_detail.exc_info()

    #the traceback knows the exact file and line where it broke
    file_name = exc_tb.tb_frame.f_code.co_filename
    line_number = exc_tb.tb_lineno

    error_message = "error in file [{0}] at line [{1}]:[{2}]".format(file_name, line_number, str(error))
    
    return error_message

class CustomException(Exception):
    '''
    Project wide exception, raise it as:
    raise CustomException(e,sys) from e
    Give a clean one line error message and full original traceback
    '''

    def __init__(self, error_message, error_detail:sys):
        # running the normal exception first
        super().__init__(error_message)
        # then build and store my original version
        self.error_message = error_message_detail(error_message, error_detail)

    def __str__(self):
        return self.error_message