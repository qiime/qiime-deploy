import os
import threading

class BashEnvironment:
    def __init__(self):
        self.var_lock = threading.Lock()
        self.var_lock.acquire()
        self.env_vars = {}
        self.print_vars = {}
        self.var_lock.release()

    def update_env_var(self, var_name, var_value):
        var_name = var_name.upper()
        self.var_lock.acquire()

        # udpate env_vars
        try:
            old_val = self.env_vars[var_name]
            if var_value not in old_val:
                new_val = var_value + ':' + old_val
                self.env_vars[var_name] = new_val
        except:
            self.env_vars[var_name] = var_value

        try:
            os.environ[var_name] = self.env_vars[var_name] + ':' + os.environ[var_name]
        except:
            os.environ[var_name] = self.env_vars[var_name]

        # update print_vars
        try:
            old_print = self.print_vars[var_name]
            if var_value not in old_print:
                new_print = var_value + ':' + old_print
                self.print_vars[var_name] = new_print
        except:
            self.print_vars[var_name] = var_value

        self.var_lock.release()

    def get_print_env(self):
        return_var = {}
        self.var_lock.acquire()
        return_var = self.print_vars
        self.var_lock.release()
        return return_var

    def get_env(self):
        return_var = {}
        self.var_lock.acquire()
        return_var = self.env_vars
        self.var_lock.release()
        return return_var
        
    def get_env_var(self, var_name):
        var_name = var_name.upper()
        return_var = ''
        self.var_lock.acquire()
        try:
            return_var = self.env_vars[var_name]
        except:
            return_var = ''
        self.var_lock.release()
        return return_var
