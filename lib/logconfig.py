import logging

def configure_log():
    formatter = logging.Formatter('%(asctime)s - %(name)-16s - ' + \
                                  '%(levelname)-8s - %(message)s')
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.getLogger('').setLevel(logging.INFO)
